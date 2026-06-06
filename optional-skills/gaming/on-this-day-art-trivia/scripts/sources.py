"""Source adapters for on-this-day events.

Three adapters, in preference order:

1. **Britannica** ``/on-this-day/<Month>-<Day>`` — editorial curation.
2. **Wikimedia** REST API ``/feed/v1/wikipedia/en/onthisday/events/<MM>/<DD>``
   — structured JSON; reliable fallback.
3. **onthisday.com** — final fallback for HTML curation.

Each adapter returns a list of :class:`CandidateEvent` and is independently
testable via cached fixtures in ``tests/fixtures/``. Network access is not
required for tests — adapters accept optional ``html``/``payload`` arguments
so fixtures can be injected.

The HTML parsers are intentionally tolerant: they prefer schema-stable
structures (e.g., the Wikimedia REST schema) and fall back to text-only
extraction when markup is brittle. Failures degrade silently — we move on
to the next adapter rather than crashing.
"""

from __future__ import annotations

import calendar
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .scoring import CandidateEvent

logger = logging.getLogger(__name__)

USER_AGENT = "hermes-on-this-day-art-trivia/0.1 (+github.com/hermes-agent)"
HTTP_TIMEOUT = 10.0


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _http_get(url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Best-effort HTTP GET. Returns text or None on any failure."""
    headers = dict(headers or {})
    headers.setdefault("User-Agent", USER_AGENT)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            data = resp.read()
            return data.decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.debug("source GET failed: %s — %s", url, exc)
        return None


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(html: str) -> str:
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", html or "")).strip()


def _month_day_url_segment(month: int, day: int) -> str:
    return f"{calendar.month_name[month].lower()}-{day}"


# --------------------------------------------------------------------------- #
# Britannica adapter
# --------------------------------------------------------------------------- #

class _BritannicaParser(HTMLParser):
    """Tolerant parser. Pulls anchored event entries from Britannica's
    /on-this-day pages.

    Britannica's page structure has shifted multiple times; rather than
    over-fitting to one selector, we collect any text inside ``<li>`` tags
    that begin with a 4-digit year, which is the editorial convention used
    consistently across versions.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._depth: int = 0
        self._li_open: bool = False
        self._buffer: List[str] = []
        self.entries: List[str] = []

    def handle_starttag(self, tag: str, attrs):  # noqa: D401
        if tag == "li":
            self._li_open = True
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self._li_open:
            text = _WS_RE.sub(" ", " ".join(self._buffer)).strip()
            if text and re.match(r"^-?\d{1,4}\b", text):
                self.entries.append(text)
            self._li_open = False
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._li_open:
            self._buffer.append(data)


_LOCATION_RE = re.compile(
    r"\b(?:in|at|near|over|from|to)\s+([A-Z][A-Za-z\.\-']+(?:[ ,][A-Z][A-Za-z\.\-']+){0,3})"
)
_YEAR_PREFIX_RE = re.compile(r"^(?P<year>-?\d{1,4})\s+(?P<rest>.*)$")


def _extract_year_and_rest(entry: str) -> Tuple[Optional[int], str]:
    m = _YEAR_PREFIX_RE.match(entry.strip())
    if not m:
        return None, entry.strip()
    try:
        return int(m.group("year")), m.group("rest").strip(" :—-")
    except ValueError:
        return None, entry.strip()


def _extract_location(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Best-effort: returns (location, country)."""
    match = _LOCATION_RE.search(text or "")
    if not match:
        return (None, None)
    raw = match.group(1).strip().rstrip(".,;")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) >= 2:
        return (parts[0], parts[-1])
    return (raw, None)


def _build_canonical_answer(text: str) -> str:
    # Take the leading clause (before the first period or semicolon) and
    # cap to ~14 words.
    first_clause = re.split(r"[\.;]", text, maxsplit=1)[0].strip()
    words = first_clause.split()
    if len(words) > 14:
        first_clause = " ".join(words[:14])
    return first_clause


def parse_britannica_html(html: str) -> List[CandidateEvent]:
    parser = _BritannicaParser()
    try:
        parser.feed(html or "")
    except Exception as exc:
        logger.debug("Britannica parse failed: %s", exc)
        return []
    out: List[CandidateEvent] = []
    for entry in parser.entries:
        year, rest = _extract_year_and_rest(entry)
        if not rest:
            continue
        loc, country = _extract_location(rest)
        out.append(
            CandidateEvent(
                summary=rest,
                canonical_answer=_build_canonical_answer(rest),
                year=year,
                location=loc,
                country=country,
                category="event",
                source="britannica",
                raw={"raw_entry": entry},
            )
        )
    return out


def fetch_britannica(month: int, day: int, *, html: Optional[str] = None) -> List[CandidateEvent]:
    if html is None:
        url = f"https://www.britannica.com/on-this-day/{_month_day_url_segment(month, day)}"
        html = _http_get(url)
    if not html:
        return []
    return parse_britannica_html(html)


# --------------------------------------------------------------------------- #
# Wikimedia adapter
# --------------------------------------------------------------------------- #

def parse_wikimedia_payload(payload: Dict[str, Any]) -> List[CandidateEvent]:
    out: List[CandidateEvent] = []
    if not isinstance(payload, dict):
        return out
    # The /onthisday/all endpoint returns multiple keys; the /events one is a list.
    sections: Dict[str, str] = {
        "events": "event",
        "selected": "event",
        "births": "birth",
        "deaths": "death",
        "holidays": "holiday",
    }
    for key, category in sections.items():
        items = payload.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            text = (item.get("text") or "").strip()
            if not text:
                continue
            year = item.get("year")
            try:
                year_int = int(year) if year is not None else None
            except (TypeError, ValueError):
                year_int = None
            loc, country = _extract_location(text)
            page_titles: List[str] = []
            for page in item.get("pages") or []:
                if isinstance(page, dict):
                    title = page.get("normalizedtitle") or page.get("title")
                    if isinstance(title, str):
                        page_titles.append(title)
            canonical = page_titles[0] if page_titles else _build_canonical_answer(text)
            out.append(
                CandidateEvent(
                    summary=text,
                    canonical_answer=canonical,
                    year=year_int,
                    location=loc,
                    country=country,
                    category=category,
                    source="wikimedia",
                    raw={"pages": page_titles},
                )
            )
    return out


def fetch_wikimedia(month: int, day: int, *, payload: Optional[Dict[str, Any]] = None) -> List[CandidateEvent]:
    if payload is None:
        url = (
            f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/"
            f"{month:02d}/{day:02d}"
        )
        text = _http_get(url, headers={"Accept": "application/json"})
        if not text:
            return []
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.debug("Wikimedia decode failed: %s", exc)
            return []
    return parse_wikimedia_payload(payload)


# --------------------------------------------------------------------------- #
# onthisday.com adapter (lightweight fallback)
# --------------------------------------------------------------------------- #

class _OnThisDayParser(HTMLParser):
    """Pulls list-item entries with a leading 4-digit year. Mirrors the
    Britannica strategy. Used only as a last-resort fallback.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._li_open = False
        self._buf: List[str] = []
        self.entries: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "li":
            self._li_open = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self._li_open:
            text = _WS_RE.sub(" ", " ".join(self._buf)).strip()
            if text and re.search(r"\b\d{3,4}\b", text[:8]):
                self.entries.append(text)
            self._li_open = False

    def handle_data(self, data: str) -> None:
        if self._li_open:
            self._buf.append(data)


def parse_onthisday_html(html: str) -> List[CandidateEvent]:
    parser = _OnThisDayParser()
    try:
        parser.feed(html or "")
    except Exception as exc:
        logger.debug("onthisday parse failed: %s", exc)
        return []
    out: List[CandidateEvent] = []
    for entry in parser.entries:
        year, rest = _extract_year_and_rest(entry)
        if not rest:
            continue
        loc, country = _extract_location(rest)
        out.append(
            CandidateEvent(
                summary=rest,
                canonical_answer=_build_canonical_answer(rest),
                year=year,
                location=loc,
                country=country,
                category="event",
                source="onthisday",
                raw={"raw_entry": entry},
            )
        )
    return out


def fetch_onthisday(month: int, day: int, *, html: Optional[str] = None) -> List[CandidateEvent]:
    if html is None:
        url = f"https://www.onthisday.com/events/{calendar.month_name[month].lower()}/{day}"
        html = _http_get(url)
    if not html:
        return []
    return parse_onthisday_html(html)


# --------------------------------------------------------------------------- #
# Aggregator
# --------------------------------------------------------------------------- #

def fetch_all_candidates(month: int, day: int) -> List[CandidateEvent]:
    """Pull from every adapter; deduplicate by canonical_answer."""
    seen: set = set()
    out: List[CandidateEvent] = []
    for fetcher in (fetch_britannica, fetch_wikimedia, fetch_onthisday):
        try:
            events = fetcher(month, day)
        except Exception as exc:
            logger.warning("source %s failed: %s", fetcher.__name__, exc)
            events = []
        for ev in events:
            key = (ev.canonical_answer.lower(), ev.year)
            if key in seen:
                continue
            seen.add(key)
            out.append(ev)
    return out


# --------------------------------------------------------------------------- #
# Local fixture-based fallback (kept for offline-only mode)
# --------------------------------------------------------------------------- #

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def load_fixture_events(month: int, day: int) -> List[CandidateEvent]:
    """Load events from a JSON fixture if present; used for fully offline runs."""
    path = FIXTURES_DIR / f"{month:02d}-{day:02d}.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return parse_wikimedia_payload(payload)
