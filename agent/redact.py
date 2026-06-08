"""Regex-based secret redaction for logs and tool output.

Applies pattern matching to mask API keys, tokens, and credentials
before they reach log files, verbose output, or gateway logs.

Short tokens (< 18 chars) are fully masked. Longer tokens preserve
the first 6 and last 4 characters for debuggability.
"""

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Sensitive query-string parameter names (case-insensitive exact match).
# Ported from nearai/ironclaw#2529 — catches tokens whose values don't match
# any known vendor prefix regex (e.g. opaque tokens, short OAuth codes).
_SENSITIVE_QUERY_PARAMS = frozenset({
    "access_token",
    "refresh_token",
    "id_token",
    "token",
    "api_key",
    "apikey",
    "client_secret",
    "password",
    "auth",
    "jwt",
    "session",
    "secret",
    "key",
    "code",           # OAuth authorization codes
    "signature",      # pre-signed URL signatures
    "x-amz-signature",
})

# Sensitive form-urlencoded / JSON body key names (case-insensitive exact match).
# Exact match, NOT substring — "token_count" and "session_id" must NOT match.
# Ported from nearai/ironclaw#2529.
_SENSITIVE_BODY_KEYS = frozenset({
    "access_token",
    "refresh_token",
    "id_token",
    "token",
    "api_key",
    "apikey",
    "client_secret",
    "password",
    "auth",
    "jwt",
    "secret",
    "private_key",
    "authorization",
    "key",
})

# Snapshot at import time so runtime env mutations (e.g. LLM-generated
# `export HERMES_REDACT_SECRETS=false`) cannot disable redaction
# mid-session.  ON by default — secure default per issue #17691. Users who
# need raw credential values in tool output (e.g. working on the redactor
# itself) can opt out via `security.redact_secrets: false` in config.yaml
# (bridged to this env var in hermes_cli/main.py, gateway/run.py, and
# cli.py) or `HERMES_REDACT_SECRETS=false` in ~/.hermes/.env. An opt-out
# warning is logged at gateway and CLI startup so operators see the
# downgrade — see `_log_redaction_status()` in gateway/run.py and cli.py.
_REDACT_ENABLED = os.getenv("HERMES_REDACT_SECRETS", "true").lower() in {"1", "true", "yes", "on"}

# Known API key prefixes -- match the prefix + contiguous token chars
_PREFIX_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{10,}",           # OpenAI / OpenRouter / Anthropic (sk-ant-*)
    r"ghp_[A-Za-z0-9]{10,}",            # GitHub PAT (classic)
    r"github_pat_[A-Za-z0-9_]{10,}",    # GitHub PAT (fine-grained)
    r"gho_[A-Za-z0-9]{10,}",            # GitHub OAuth access token
    r"ghu_[A-Za-z0-9]{10,}",            # GitHub user-to-server token
    r"ghs_[A-Za-z0-9]{10,}",            # GitHub server-to-server token
    r"ghr_[A-Za-z0-9]{10,}",            # GitHub refresh token
    r"xox[baprs]-[A-Za-z0-9-]{10,}",    # Slack tokens
    r"AIza[A-Za-z0-9_-]{30,}",          # Google API keys
    r"pplx-[A-Za-z0-9]{10,}",           # Perplexity
    r"fal_[A-Za-z0-9_-]{10,}",          # Fal.ai
    r"fc-[A-Za-z0-9]{10,}",             # Firecrawl
    r"bb_live_[A-Za-z0-9_-]{10,}",      # BrowserBase
    r"gAAAA[A-Za-z0-9_=-]{20,}",        # Codex encrypted tokens
    r"AKIA[A-Z0-9]{16}",                # AWS Access Key ID
    r"sk_live_[A-Za-z0-9]{10,}",        # Stripe secret key (live)
    r"sk_test_[A-Za-z0-9]{10,}",        # Stripe secret key (test)
    r"rk_live_[A-Za-z0-9]{10,}",        # Stripe restricted key
    r"SG\.[A-Za-z0-9_-]{10,}",          # SendGrid API key
    r"hf_[A-Za-z0-9]{10,}",             # HuggingFace token
    r"r8_[A-Za-z0-9]{10,}",             # Replicate API token
    r"npm_[A-Za-z0-9]{10,}",            # npm access token
    r"pypi-[A-Za-z0-9_-]{10,}",         # PyPI API token
    r"dop_v1_[A-Za-z0-9]{10,}",         # DigitalOcean PAT
    r"doo_v1_[A-Za-z0-9]{10,}",         # DigitalOcean OAuth
    r"am_[A-Za-z0-9_-]{10,}",           # AgentMail API key
    r"sk_[A-Za-z0-9_]{10,}",            # ElevenLabs TTS key (sk_ underscore, not sk- dash)
    r"tvly-[A-Za-z0-9]{10,}",           # Tavily search API key
    r"exa_[A-Za-z0-9]{10,}",            # Exa search API key
    r"gsk_[A-Za-z0-9]{10,}",            # Groq Cloud API key
    r"syt_[A-Za-z0-9]{10,}",            # Matrix access token
    r"retaindb_[A-Za-z0-9]{10,}",       # RetainDB API key
    r"hsk-[A-Za-z0-9]{10,}",            # Hindsight API key
    r"mem0_[A-Za-z0-9]{10,}",           # Mem0 Platform API key
    r"brv_[A-Za-z0-9]{10,}",            # ByteRover API key
    r"xai-[A-Za-z0-9]{30,}",            # xAI (Grok) API key
]

# ENV assignment patterns: KEY=value where KEY contains a secret-like name
_SECRET_ENV_NAMES = r"(?:API_?KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AUTH)"
_ENV_ASSIGN_RE = re.compile(
    rf"([A-Z0-9_]{{0,50}}{_SECRET_ENV_NAMES}[A-Z0-9_]{{0,50}})\s*=\s*(['\"]?)(\S+)\2",
)

# JSON field patterns: "apiKey": "value", "token": "value", etc.
_JSON_KEY_NAMES = r"(?:api_?[Kk]ey|token|secret|password|access_token|refresh_token|auth_token|bearer|secret_value|raw_secret|secret_input|key_material)"
_JSON_FIELD_RE = re.compile(
    rf'("{_JSON_KEY_NAMES}")\s*:\s*"([^"]+)"',
    re.IGNORECASE,
)

# Authorization headers
_AUTH_HEADER_RE = re.compile(
    r"(Authorization:\s*Bearer\s+)(\S+)",
    re.IGNORECASE,
)

# Telegram bot tokens: bot<digits>:<token> or <digits>:<token>,
# where token part is restricted to [-A-Za-z0-9_] and length >= 30
_TELEGRAM_RE = re.compile(
    r"(bot)?(\d{8,}):([-A-Za-z0-9_]{30,})",
)

# Private key blocks: -----BEGIN RSA PRIVATE KEY----- ... -----END RSA PRIVATE KEY-----
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN[A-Z ]*PRIVATE KEY-----[\s\S]*?-----END[A-Z ]*PRIVATE KEY-----"
)

# Database connection strings: protocol://user:PASSWORD@host
# Catches postgres, mysql, mongodb, redis, amqp URLs and redacts the password
_DB_CONNSTR_RE = re.compile(
    r"((?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:]+:)([^@]+)(@)",
    re.IGNORECASE,
)

# JWT tokens: header.payload[.signature] — always start with "eyJ" (base64 for "{")
# Matches 1-part (header only), 2-part (header.payload), and full 3-part JWTs.
_JWT_RE = re.compile(
    r"eyJ[A-Za-z0-9_-]{10,}"           # Header (always starts with eyJ)
    r"(?:\.[A-Za-z0-9_=-]{4,}){0,2}"   # Optional payload and/or signature
)

# E.164 phone numbers: +<country><number>, 7-15 digits
# Negative lookahead prevents matching hex strings or identifiers
_SIGNAL_PHONE_RE = re.compile(r"(\+[1-9]\d{6,14})(?![A-Za-z0-9])")

# URLs containing query strings — matches `scheme://...?...[# or end]`.
# Used to scan text for URLs whose query params may contain secrets.
# Ported from nearai/ironclaw#2529.
_URL_WITH_QUERY_RE = re.compile(
    r"(https?|wss?|ftp)://"          # scheme
    r"([^\s/?#]+)"                    # authority (may include userinfo)
    r"([^\s?#]*)"                     # path
    r"\?([^\s#]+)"                    # query (required)
    r"(#\S*)?",                       # optional fragment
)

# URLs containing userinfo — `scheme://user:password@host` for ANY scheme
# (not just DB protocols already covered by _DB_CONNSTR_RE above).
# Catches things like `https://user:token@api.example.com/v1/foo`.
_URL_USERINFO_RE = re.compile(
    r"(https?|wss?|ftp)://([^/\s:@]+):([^/\s@]+)@",
)

# HTTP access logs often use a relative request target rather than a full URL:
# `"POST /webhook?password=... HTTP/1.1"`. The full-URL redactor above only
# sees strings containing `://`, so handle request-target query strings too.
_HTTP_REQUEST_TARGET_QUERY_RE = re.compile(
    r"\b((?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|TRACE|CONNECT)\s+[^ \t\r\n\"']*?)"
    r"\?([^ \t\r\n\"']+)",
    re.IGNORECASE,
)

# Form-urlencoded body detection: conservative — only applies when the entire
# text looks like a query string (k=v&k=v pattern with no newlines).
_FORM_BODY_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_.-]*=[^&\s]*(?:&[A-Za-z_][A-Za-z0-9_.-]*=[^&\s]*)+$"
)

# Compile known prefix patterns into one alternation
_PREFIX_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(" + "|".join(_PREFIX_PATTERNS) + r")(?![A-Za-z0-9_-])"
)


def mask_secret(
    value: str,
    *,
    head: int = 4,
    tail: int = 4,
    floor: int = 12,
    placeholder: str = "***",
    empty: str = "",
) -> str:
    """Mask a secret for display, preserving ``head`` and ``tail`` characters.

    Canonical helper for display-time redaction across Hermes — used by
    ``hermes config``, ``hermes status``, ``hermes dump``, and anywhere
    a secret needs to be shown truncated for debuggability while still
    keeping the bulk hidden.

    Args:
        value:       The secret to mask. ``None``/empty returns ``empty``.
        head:        Leading characters to preserve. Default 4.
        tail:        Trailing characters to preserve. Default 4.
        floor:       Values shorter than ``head + tail + floor_margin`` are
                     fully masked (returns ``placeholder``). Default 12 —
                     matches the existing config/status/dump convention.
        placeholder: Value returned for too-short inputs. Default ``"***"``.
        empty:       Value returned when ``value`` is falsy (None, ""). The
                     caller can override this to e.g. ``color("(not set)",
                     Colors.DIM)`` for user-facing display.

    Examples:
        >>> mask_secret("sk-proj-abcdef1234567890")
        'sk-p...7890'
        >>> mask_secret("short")                         # fully masked
        '***'
        >>> mask_secret("")                              # empty default
        ''
        >>> mask_secret("", empty="(not set)")           # empty override
        '(not set)'
        >>> mask_secret("long-token", head=6, tail=4, floor=18)
        '***'
    """
    if not value:
        return empty
    if len(value) < floor:
        return placeholder
    return f"{value[:head]}...{value[-tail:]}"


def _mask_token(token: str) -> str:
    """Mask a log token — conservative 18-char floor, preserves 6 prefix / 4 suffix."""
    # Empty input: historically this returned "***" rather than "". Preserve.
    if not token:
        return "***"
    return mask_secret(token, head=6, tail=4, floor=18)


def _redact_query_string(query: str) -> str:
    """Redact sensitive parameter values in a URL query string.

    Handles `k=v&k=v` format. Sensitive keys (case-insensitive) have values
    replaced with `***`. Non-sensitive keys pass through unchanged.
    Empty or malformed pairs are preserved as-is.
    """
    if not query:
        return query
    parts = []
    for pair in query.split("&"):
        if "=" not in pair:
            parts.append(pair)
            continue
        key, _, value = pair.partition("=")
        if key.lower() in _SENSITIVE_QUERY_PARAMS:
            parts.append(f"{key}=***")
        else:
            parts.append(pair)
    return "&".join(parts)


def _redact_url_query_params(text: str) -> str:
    """Scan text for URLs with query strings and redact sensitive params.

    Catches opaque tokens that don't match vendor prefix regexes, e.g.
    `https://example.com/cb?code=ABC123&state=xyz` → `...?code=***&state=xyz`.
    """
    def _sub(m: re.Match) -> str:
        scheme = m.group(1)
        authority = m.group(2)
        path = m.group(3)
        query = _redact_query_string(m.group(4))
        fragment = m.group(5) or ""
        return f"{scheme}://{authority}{path}?{query}{fragment}"
    return _URL_WITH_QUERY_RE.sub(_sub, text)


def _redact_url_userinfo(text: str) -> str:
    """Strip `user:password@` from HTTP/WS/FTP URLs.

    DB protocols (postgres, mysql, mongodb, redis, amqp) are handled
    separately by `_DB_CONNSTR_RE`.
    """
    return _URL_USERINFO_RE.sub(
        lambda m: f"{m.group(1)}://{m.group(2)}:***@",
        text,
    )


def _redact_http_request_target_query_params(text: str) -> str:
    """Redact sensitive query params in HTTP access-log request targets."""
    def _sub(m: re.Match) -> str:
        prefix = m.group(1)
        query = _redact_query_string(m.group(2))
        return f"{prefix}?{query}"
    return _HTTP_REQUEST_TARGET_QUERY_RE.sub(_sub, text)


def _redact_form_body(text: str) -> str:
    """Redact sensitive values in a form-urlencoded body.

    Only applies when the entire input looks like a pure form body
    (k=v&k=v with no newlines, no other text). Single-line non-form
    text passes through unchanged. This is a conservative pass — the
    `_redact_url_query_params` function handles embedded query strings.
    """
    if not text or "\n" in text or "&" not in text:
        return text
    # The body-body form check is strict: only trigger on clean k=v&k=v.
    if not _FORM_BODY_RE.match(text.strip()):
        return text
    return _redact_query_string(text.strip())


def redact_sensitive_text(text: str, *, force: bool = False, code_file: bool = False) -> str:
    """Apply all redaction patterns to a block of text.

    Safe to call on any string -- non-matching text passes through unchanged.
    Enabled by default. Disable via security.redact_secrets: false in config.yaml.
    Set force=True for safety boundaries that must never return raw secrets
    regardless of the user's global logging redaction preference.

    Set code_file=True to skip the ENV-assignment and JSON-field regex
    patterns when the text is known to be source code (e.g. MAX_TOKENS=***
    constants, "apiKey": "test" fixtures). Prefix patterns, auth headers,
    private keys, DB connstrings, JWTs, and URL secrets are still redacted.

    Performance: each regex pattern is gated behind a cheap substring
    pre-check (e.g. ``"=" in text`` for ENV assignments, ``"://" in text``
    for URLs, ``"eyJ" in text`` for JWTs). On a typical hermes log line
    (no secrets) this drops the 13-pattern scan from ~5.6us to ~1.8us per
    record (-68%). The pre-checks are conservative — false positives
    still run the full regex, which then doesn't match. False negatives
    are impossible because every regex requires the gated substring to
    match.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)
    if not text:
        return text
    if not (force or _REDACT_ENABLED):
        return text

    # Known prefixes (sk-, ghp_, etc.) — gate on substring presence
    if _has_known_prefix_substring(text):
        text = _PREFIX_RE.sub(lambda m: _mask_token(m.group(1)), text)

    # ENV assignments: OPENAI_API_KEY=***  (skip for code files — false positives)
    if not code_file:
        if "=" in text:
            def _redact_env(m):
                name, quote, value = m.group(1), m.group(2), m.group(3)
                return f"{name}={quote}{_mask_token(value)}{quote}"
            text = _ENV_ASSIGN_RE.sub(_redact_env, text)

        # JSON fields: "apiKey": "***"  (skip for code files — false positives)
        if ":" in text and '"' in text:
            def _redact_json(m):
                key, value = m.group(1), m.group(2)
                return f'{key}: "{_mask_token(value)}"'
            text = _JSON_FIELD_RE.sub(_redact_json, text)

    # Authorization headers — _AUTH_HEADER_RE is "Authorization: Bearer ..."
    # case-insensitive, so "uthorization" is the cheapest substring gate that
    # covers both "Authorization" and "authorization" without a casefold().
    if "uthorization" in text or "UTHORIZATION" in text:
        text = _AUTH_HEADER_RE.sub(
            lambda m: m.group(1) + _mask_token(m.group(2)),
            text,
        )

    # Telegram bot tokens — pattern requires ":<token>" with digits prefix
    if ":" in text:
        def _redact_telegram(m):
            prefix = m.group(1) or ""
            digits = m.group(2)
            return f"{prefix}{digits}:***"
        text = _TELEGRAM_RE.sub(_redact_telegram, text)

    # Private key blocks
    if "BEGIN" in text and "-----" in text:
        text = _PRIVATE_KEY_RE.sub("[REDACTED PRIVATE KEY]", text)

    # Database connection string passwords
    if "://" in text:
        text = _DB_CONNSTR_RE.sub(lambda m: f"{m.group(1)}***{m.group(3)}", text)

    # JWT tokens (eyJ... — base64-encoded JSON headers)
    if "eyJ" in text:
        text = _JWT_RE.sub(lambda m: _mask_token(m.group(0)), text)

    # NOTE: Web-URL redaction (query params + userinfo + HTTP access-log
    # request targets) is intentionally OFF. Many legitimate workflows pass
    # opaque tokens through query strings — magic-link checkouts, OAuth
    # callbacks the agent is meant to follow, pre-signed share URLs — and
    # blanket-redacting param values by name breaks those skills mid-flow.
    # Known credential shapes (sk-, ghp_, JWTs, etc.) inside URLs are still
    # caught by _PREFIX_RE and _JWT_RE above. DB connection-string passwords
    # are still caught by _DB_CONNSTR_RE.

    # Form-urlencoded bodies (only triggers on clean k=v&k=v inputs).
    if "&" in text and "=" in text:
        text = _redact_form_body(text)

    # E.164 phone numbers (Signal, WhatsApp)
    if "+" in text:
        def _redact_phone(m):
            phone = m.group(1)
            if len(phone) <= 8:
                return phone[:2] + "****" + phone[-2:]
            return phone[:4] + "****" + phone[-4:]
        text = _SIGNAL_PHONE_RE.sub(_redact_phone, text)

    return text


# Substrings used to gate ``_PREFIX_RE`` execution. If none of these appear in
# the input string, the prefix regex cannot match anything, so we skip it.
# False positives are fine (they just run the regex, which then matches
# nothing) — the bound is "no false negatives" and that holds because every
# pattern in ``_PREFIX_PATTERNS`` has at least one of these as a literal
# substring of its leading characters.
#
# Derived automatically from ``_PREFIX_PATTERNS`` at module load time so a
# future PR that adds a new prefix to the regex list can't silently break
# the screen.

def _extract_literal_prefix(pattern: str) -> str:
    """Return the leading literal characters of a regex pattern.

    Stops at the first regex metacharacter (``[``, ``(``, ``\\``, ``.``,
    ``?``, ``*``, ``+``, ``|``, ``{``, ``^``, ``$``).  Returns the literal
    that any match of the pattern MUST contain as a substring, so the
    pre-screen never produces false negatives.
    """
    meta = "[(\\.?*+|{^$"
    for i, ch in enumerate(pattern):
        if ch in meta:
            return pattern[:i]
    return pattern


_PREFIX_SUBSTRINGS = tuple(
    _extract_literal_prefix(p) for p in _PREFIX_PATTERNS
)


def _has_known_prefix_substring(text: str) -> bool:
    """Return True if ``text`` contains any known credential prefix substring.

    Used as a cheap pre-check before invoking the expensive ``_PREFIX_RE``.
    """
    return any(p in text for p in _PREFIX_SUBSTRINGS)


_HTTP_METHOD_SUBSTRINGS = (
    "GET ",
    "POST ",
    "PUT ",
    "PATCH ",
    "DELETE ",
    "HEAD ",
    "OPTIONS ",
    "TRACE ",
    "CONNECT ",
)


def _has_http_method_substring(text: str) -> bool:
    """Cheap pre-check before scanning for access-log request targets."""
    upper = text.upper()
    return any(method in upper for method in _HTTP_METHOD_SUBSTRINGS)


# Regex matching a redaction placeholder produced by ``_mask_token`` — a known
# credential prefix followed by up to a few token chars, ``...``, then a short
# trailing slice (``_mask_token`` keeps 6 head / 4 tail by default, so e.g.
# ``sk-example-real-key`` becomes ``sk-exa...-key``). Used by the patch tool to
# reject ``old_string`` / ``new_string`` arguments that look like they were
# copy-pasted from redacted ``read_file`` output (#30962) — those won't match
# the raw bytes on disk and, worse, would corrupt the real secret if written
# back through a replacement block.
# JWTs are masked via ``_JWT_RE`` and don't appear in ``_PREFIX_PATTERNS``,
# so we add ``eyJ`` (the universal JWT header prefix) explicitly here.
_REDACTED_PLACEHOLDER_PREFIXES = tuple(
    sorted(set(s for s in (*_PREFIX_SUBSTRINGS, "eyJ") if s), key=len, reverse=True)
)

# Shared "masked-token body" pattern: ``_mask_token`` keeps 6 head / 4 tail
# (floor 18); ``mask_secret`` defaults to 4 head / 4 tail (floor 12). Both
# slice the raw token chars, so the body characters are whatever the original
# token alphabet was. Prefix patterns only ever produce ``[A-Za-z0-9_=+-]``
# slices (no ``.`` or ``/``), so the class is tight enough to avoid matching
# stray ``foo/bar.../baz.py`` paths in real source code. The trailing
# ``{4,8}`` floor matches ``_mask_token``'s fixed 4-char tail; loosening
# below 4 buys no recall and widens false-positive risk on prose like
# ``foo=bar...ab``.
_MASK_BODY = r"[A-Za-z0-9_=+-]{0,6}\.\.\.[A-Za-z0-9_=+-]{4,8}"

# Prefix-based masked token: ``{known-credential-prefix}{0-6 chars}...{2-8 chars}``.
# Catches values whose original form carried a recognisable vendor prefix
# (``sk-``, ``ghp_``, ``eyJ``, ...) — the prefix slice survives masking.
_REDACTED_PLACEHOLDER_RE = re.compile(
    r"(?:"
    + "|".join(re.escape(p) for p in _REDACTED_PLACEHOLDER_PREFIXES)
    + r")"
    + _MASK_BODY
)

# Sensitive-key context — when redaction strips an OPAQUE secret (no known
# vendor prefix; e.g. an OAuth bearer, a random ``PASSWORD=…``), the leading
# key name is the only signal that what follows used to be a secret. These
# patterns mirror ``_ENV_ASSIGN_RE`` / ``_JSON_FIELD_RE`` / ``_AUTH_HEADER_RE``
# so the guard sees the same surfaces the redactor writes through.
_SENSITIVE_KEY_CONTEXT = (
    r"(?:"
    # YAML / JSON / TOML / config-style assignment: ``api_key: value``,
    # ``"apiKey": "value"``, ``password = value``. Word-anchored so partial
    # matches like ``not_a_token`` don't trigger.
    r"\b(?i:api[_-]?key|apikey|access[_-]?token|refresh[_-]?token|id[_-]?token"
    r"|token|secret(?:_value|_key|_input)?|raw_secret|password|passwd"
    r"|credential|client[_-]?secret|private[_-]?key|key_material"
    r"|auth(?:orization)?|bearer)"
    r"['\"]?\s*[:=]\s*['\"]?"
    # Authorization-header value: ``Authorization: Bearer <token>``.
    r"|(?i:authorization:\s*bearer\s+)"
    # ENV-style assignment: ``FOO_API_KEY=...`` (matches the same key shapes
    # ``_ENV_ASSIGN_RE`` redacts — uppercase, sensitive suffix anywhere).
    r"|\b[A-Z][A-Z0-9_]*(?:API_?KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AUTH)"
    r"[A-Z0-9_]*\s*=\s*['\"]?"
    r")"
)

# Context-based masked token: sensitive key + masked-token body. Catches
# opaque secrets (no recognised vendor prefix) that the prefix regex misses.
_CONTEXT_MASKED_RE = re.compile(_SENSITIVE_KEY_CONTEXT + _MASK_BODY)

# NOTE: a tempting fourth rule would be "sensitive key + bare ``***``" — that
# shape IS emitted by the redactor for very short values (``_ENV_ASSIGN_RE`` /
# ``_JSON_FIELD_RE`` /  ``_TELEGRAM_RE`` / query-string redaction all write
# bare ``***``). It is **deliberately not detected**: the same shape is also
# how real ``.env.example`` / ``README.md`` / config-template files document
# placeholder secrets, and refusing every edit to such files is worse than
# the (narrow) corruption window — real production secrets are almost always
# long enough that the redactor masks them as ``head...tail`` (caught by
# ``_CONTEXT_MASKED_RE``) rather than ``***``. Detection of ``***`` is kept
# only where it is unambiguous: inside a DB / URL connection string, where
# the position between ``:`` and ``@`` cannot legitimately be ``***``.

# DB / URL connection string with masked password (``postgres://user:***@host``).
# Emitted by ``_DB_CONNSTR_RE`` and ``_URL_USERINFO_RE``. Round-tripping this
# through ``patch`` / ``write_file`` overwrites the real password with ``***``.
_CONNSTRING_TRIPLE_STAR_RE = re.compile(
    r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp|https?|wss?|ftp)"
    r"://[^:/\s@]+:\*\*\*@",
    re.IGNORECASE,
)

# Distinctive literal placeholders that ``redact_sensitive_text`` emits for
# whole secret blocks. These should never appear verbatim in real source code,
# so any occurrence in patch input is almost certainly a copy-paste from
# redacted output rather than the actual file bytes.
_LITERAL_REDACTED_MARKERS = (
    "[REDACTED PRIVATE KEY]",
)


def looks_like_redacted_secret(text: Optional[str]) -> Optional[str]:
    """Return the offending substring if ``text`` looks like redacted output.

    Detects three shapes produced by :func:`redact_sensitive_text`:

      * prefix-based masked tokens — ``{known-prefix}…...{tail}`` for values
        carrying a recognised vendor prefix (``sk-``, ``ghp_``, ``eyJ``, …).
      * context-based masked tokens — opaque values redacted via the ENV /
        JSON-field / Authorization-header paths, where only the surrounding
        key name flags the secret.
      * ``***`` inside a DB / URL connection string
        (``postgres://user:***@host``) — the only ``***`` shape that cannot
        plausibly be a documentation placeholder.
      * literal markers like ``[REDACTED PRIVATE KEY]``.

    Bare ``***`` next to a sensitive key (``api_key: ***``) is **not**
    flagged: the same shape is how real ``.env.example`` / README / template
    files document placeholders, and the corruption window it would close
    is narrow (only fires for sub-floor-length values, which are rarely
    real production secrets).

    Returns the matched substring on detection (intended for inclusion in
    the rejection error so the agent can see exactly what tripped the
    check), or ``None`` if the text is safe to use as raw file content.

    This is a heuristic — a sufficiently adversarial real file could include
    a string of this exact shape. The point is to catch the realistic agent
    bug where redacted ``read_file`` output is fed back into a write tool.
    """
    if not text:
        return None

    for marker in _LITERAL_REDACTED_MARKERS:
        if marker in text:
            return marker

    if "..." in text:
        # Prefix-based first (cheap substring pre-check + tight regex).
        if any(p in text for p in _REDACTED_PLACEHOLDER_PREFIXES):
            m = _REDACTED_PLACEHOLDER_RE.search(text)
            if m:
                return m.group(0)
        # Context-based (opaque tokens behind a sensitive key name).
        m = _CONTEXT_MASKED_RE.search(text)
        if m:
            return m.group(0)

    if "***" in text:
        m = _CONNSTRING_TRIPLE_STAR_RE.search(text)
        if m:
            return m.group(0)

    return None


class RedactingFormatter(logging.Formatter):
    """Log formatter that redacts secrets from all log messages."""

    def __init__(self, fmt=None, datefmt=None, style='%', **kwargs):
        super().__init__(fmt, datefmt, style, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_sensitive_text(original)
