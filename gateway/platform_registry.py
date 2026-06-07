"""
Platform Adapter Registry

Allows platform adapters (built-in and plugin) to self-register so the gateway
can discover and instantiate them without hardcoded if/elif chains.

Built-in adapters continue to use the existing if/elif in _create_adapter()
for now.  Plugin adapters register here via PluginContext.register_platform()
and are looked up first -- if nothing is found the gateway falls through to
the legacy code path.

Usage (plugin side):

    from gateway.platform_registry import platform_registry, PlatformEntry

    platform_registry.register(PlatformEntry(
        name="irc",
        label="IRC",
        adapter_factory=lambda cfg: IRCAdapter(cfg),
        check_fn=check_requirements,
        validate_config=lambda cfg: bool(cfg.extra.get("server")),
        required_env=["IRC_SERVER"],
        install_hint="pip install irc",
    ))

Usage (gateway side):

    adapter = platform_registry.create_adapter("irc", platform_config)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class PlatformEntry:
    """Metadata and factory for a single platform adapter."""

    # Identifier used in config.yaml (e.g. "irc", "viber").
    name: str

    # Human-readable label (e.g. "IRC", "Viber").
    label: str

    # Factory callable: receives a PlatformConfig, returns an adapter instance.
    # Using a factory instead of a bare class lets plugins do custom init
    # (e.g. passing extra kwargs, wrapping in try/except).
    adapter_factory: Callable[[Any], Any]

    # Returns True when the platform's dependencies are available.
    check_fn: Callable[[], bool]

    # Optional: given a PlatformConfig, is it properly configured?
    # If None, the registry skips config validation and lets the adapter
    # fail at connect() time with a descriptive error.
    validate_config: Optional[Callable[[Any], bool]] = None

    # Optional: given a PlatformConfig, is the platform connected/enabled?
    # Used by ``GatewayConfig.get_connected_platforms()`` and setup UI status.
    # If None, falls back to ``validate_config`` or ``check_fn``.
    is_connected: Optional[Callable[[Any], bool]] = None

    # Env vars this platform needs (for ``hermes setup`` display).
    required_env: list = field(default_factory=list)

    # Hint shown when check_fn returns False.
    install_hint: str = ""

    # Optional setup function for interactive configuration.
    # Signature: () -> None (prompts user, saves env vars).
    # If None, falls back to _setup_standard_platform (needs token_var + vars)
    # or a generic "set these env vars" display.
    setup_fn: Optional[Callable[[], None]] = None

    # "builtin" or "plugin"
    source: str = "plugin"

    # Name of the plugin manifest that registered this entry (empty for
    # built-ins).  Used by ``hermes gateway setup`` to auto-enable the
    # owning plugin when the user configures its platform.
    plugin_name: str = ""

    # ── Auth env var names (for _is_user_authorized integration) ──
    # E.g. "IRC_ALLOWED_USERS" — checked for comma-separated user IDs.
    allowed_users_env: str = ""
    # E.g. "IRC_ALLOW_ALL_USERS" — if truthy, all users authorized.
    allow_all_env: str = ""

    # ── Message limits ──
    # Max message length for smart-chunking.  0 = no limit.
    max_message_length: int = 0

    # ── Privacy ──
    # If True, session descriptions redact PII (phone numbers, etc.)
    pii_safe: bool = False

    # ── Display ──
    # Emoji for CLI/gateway display (e.g. "💬")
    emoji: str = "🔌"

    # Whether this platform should appear in _UPDATE_ALLOWED_PLATFORMS
    # (allows /update command from this platform).
    allow_update_command: bool = True

    # ── LLM guidance ──
    # Platform hint injected into the system prompt (e.g. "You are on IRC.
    # Do not use markdown.").  Empty string = no hint.
    platform_hint: str = ""

    # ── Env-driven auto-configuration ──
    # Optional: read env vars, return a dict of ``PlatformConfig.extra`` fields
    # to seed when the platform is auto-enabled.  Called during
    # ``_apply_env_overrides`` BEFORE the adapter is constructed, so
    # ``gateway status`` etc. can reflect env-only configuration without
    # instantiating the adapter.  Return ``None`` (or an empty dict) to skip.
    # Signature: () -> Optional[dict[str, Any]]
    env_enablement_fn: Optional[Callable[[], Optional[dict]]] = None

    # ── YAML→env config bridge ──
    # Optional: translate this platform's ``config.yaml`` keys into env vars
    # and/or seed ``PlatformConfig.extra`` directly.  Lets a plugin own its
    # YAML config translation instead of forcing core ``gateway/config.py``
    # to know every platform's schema.
    #
    # Signature: (yaml_cfg: dict, platform_cfg: dict) -> Optional[dict]
    # Called from ``load_gateway_config()`` after the generic shared-key loop
    # and before ``_apply_env_overrides``.  Mutating ``os.environ`` is allowed
    # (use ``not os.getenv(...)`` guards to preserve env > YAML precedence);
    # any returned dict is merged into ``PlatformConfig.extra``.  Exceptions
    # are caught and logged at debug level.
    # See website/docs/developer-guide/adding-platform-adapters.md for the
    # full contract and a worked example.
    apply_yaml_config_fn: Optional[Callable[[dict, dict], Optional[dict]]] = None

    # Optional: home-channel env var name for cron/notification delivery
    # (e.g. ``"IRC_HOME_CHANNEL"``).  When set, ``cron.scheduler`` treats this
    # platform as a valid ``deliver=<name>`` target and reads the env var to
    # resolve the default chat/room ID.  Empty = no cron home-channel support.
    cron_deliver_env_var: str = ""

    # ── Standalone (out-of-process) sending ──
    # Optional: async coroutine that delivers a message without a live
    # gateway adapter.  Called by ``tools/send_message_tool._send_via_adapter``
    # when ``cron`` runs in a separate process from the gateway and the
    # in-process adapter weakref is therefore ``None``.
    #
    # Signature:
    #     async (pconfig, chat_id, message, *, thread_id=None,
    #            media_files=None, force_document=False) -> dict
    #
    # Returns ``{"success": True, "message_id": ...}`` on success or
    # ``{"error": str}`` on failure.  Plugin authors typically open an
    # ephemeral connection / acquire a fresh OAuth token, send, and close.
    # Without this hook, plugin platforms cannot serve as cron ``deliver=``
    # targets when the gateway is not co-resident with the cron process.
    standalone_sender_fn: Optional[Callable[..., Awaitable[dict]]] = None


@dataclass
class LazyPlatformEntry:
    """Import-free placeholder for a bundled platform adapter.

    Holds only the cheap, manifest-derived metadata the gateway/setup UI
    needs *before* a platform is actually used (name, label, required_env,
    install_hint, emoji, plugin_name).  The heavy adapter module — and the
    SDK it pulls in (e.g. ``discord.py``, ``microsoft_teams``, aiohttp) — is
    NOT imported until the first time a *live* capability is required:
    ``create_adapter()``, ``check_fn``, ``setup_fn``, ``apply_yaml_config_fn``,
    ``standalone_sender_fn``, etc.

    The ``loader`` callable imports the adapter module and calls its
    ``register(ctx)`` entry point, which re-registers a real
    :class:`PlatformEntry` under the same ``name`` (last-writer-wins), thereby
    materialising the lazy entry in place.  See ``PlatformRegistry.get`` /
    ``_materialise``.

    This mirrors the model-provider deferral already used in
    ``hermes_cli/plugins.py`` (manifest recorded at discovery, module imported
    on first real use) so that a gateway running without any messaging
    platform (e.g. api_server-only on Modal) never pays the adapter import
    cost at ``import gateway.run`` time.
    """

    # Registry key (platform value, e.g. "discord") — equals the plugin
    # directory name by convention.
    name: str
    # Human-readable label for status/setup display.
    label: str = ""
    # Imports the adapter module and triggers its register(ctx); raises on
    # failure (callers wrap in try/except and fall through to legacy paths).
    loader: Callable[[], None] = lambda: None
    # Cheap metadata mirrored from the manifest so status/setup UIs don't
    # force a load.  Names intentionally match PlatformEntry fields.
    required_env: list = field(default_factory=list)
    install_hint: str = ""
    emoji: str = "🔌"
    plugin_name: str = ""
    source: str = "plugin"
    # Auth/cron env-var names — derived mechanically from the platform value
    # (``<PLATFORM_UPPER>_ALLOWED_USERS`` etc.) so the gateway's startup
    # allowlist-warning scan and cron deliver-target enumeration work off the
    # placeholder without importing the adapter.  Mirror PlatformEntry.
    allowed_users_env: str = ""
    allow_all_env: str = ""
    cron_deliver_env_var: str = ""


class PlatformRegistry:
    """Central registry of platform adapters.

    Thread-safe for reads (dict lookups are atomic under GIL).
    Writes happen at startup during sequential discovery.

    Entries are either fully-materialised :class:`PlatformEntry` objects or
    cheap :class:`LazyPlatformEntry` placeholders.  Lazy entries are
    transparently materialised on first access that needs a live callable.
    """

    def __init__(self) -> None:
        self._entries: dict[str, PlatformEntry] = {}
        # Lazy placeholders keyed by platform name.  Kept separate from
        # ``_entries`` so metadata-only enumeration (status, setup) never
        # triggers a materialisation.
        self._lazy: dict[str, LazyPlatformEntry] = {}

    # -- lazy registration ---------------------------------------------------

    def register_lazy(self, lazy: LazyPlatformEntry) -> None:
        """Register an import-free placeholder for a bundled platform.

        A subsequent ``register()`` of a real :class:`PlatformEntry` with the
        same name supersedes the placeholder (materialisation).  Conversely a
        placeholder never overwrites an already-materialised entry.
        """
        if lazy.name in self._entries:
            # Already materialised — keep the real entry.
            return
        self._lazy[lazy.name] = lazy
        logger.debug("Registered lazy platform placeholder: %s", lazy.name)

    def _materialise(self, name: str) -> Optional[PlatformEntry]:
        """Force-load a lazy entry's adapter module and return the real entry.

        Returns the materialised :class:`PlatformEntry`, or ``None`` if the
        name is unknown or the loader failed.  Idempotent: once materialised
        the lazy placeholder is dropped.
        """
        if name in self._entries:
            return self._entries[name]
        lazy = self._lazy.get(name)
        if lazy is None:
            return None
        try:
            lazy.loader()  # imports adapter module; its register() repopulates _entries
        except Exception as e:
            logger.error(
                "Failed to materialise platform '%s' (lazy import): %s",
                lazy.label or name, e, exc_info=True,
            )
            return None
        finally:
            self._lazy.pop(name, None)
        return self._entries.get(name)

    def register(self, entry: PlatformEntry) -> None:
        """Register a platform adapter entry.

        If an entry with the same name exists, it is replaced (last writer
        wins -- this lets plugins override built-in adapters if desired).
        Registering a real entry supersedes any lazy placeholder for the
        same name.
        """
        self._lazy.pop(entry.name, None)
        if entry.name in self._entries:
            prev = self._entries[entry.name]
            logger.info(
                "Platform '%s' re-registered (was %s, now %s)",
                entry.name,
                prev.source,
                entry.source,
            )
        self._entries[entry.name] = entry
        logger.debug("Registered platform adapter: %s (%s)", entry.name, entry.source)

    def unregister(self, name: str) -> bool:
        """Remove a platform entry.  Returns True if it existed."""
        had_lazy = self._lazy.pop(name, None) is not None
        had_real = self._entries.pop(name, None) is not None
        return had_real or had_lazy

    def get(self, name: str) -> Optional[PlatformEntry]:
        """Look up a platform entry by name, materialising if lazy.

        Callers read live attributes (``standalone_sender_fn``,
        ``apply_yaml_config_fn``, ``adapter_factory`` …) off the returned
        entry, so a lazy placeholder must be force-loaded here.
        """
        if name in self._entries:
            return self._entries[name]
        if name in self._lazy:
            return self._materialise(name)
        return None

    def all_entries(self) -> list:
        """Return all registered platform entries (materialised + lazy).

        Materialised :class:`PlatformEntry` objects and import-free
        :class:`LazyPlatformEntry` placeholders are returned side by side.
        Enumeration intentionally does NOT materialise — callers that only
        read cheap metadata (name, label, required_env, install_hint, emoji,
        plugin_name, the auth/cron env-var names) work against either type.
        Code that needs a live callable should call ``get(name)`` to force a
        load for that specific platform.
        """
        merged: dict[str, Any] = dict(self._lazy)
        merged.update(self._entries)  # materialised wins over placeholder
        return list(merged.values())

    def plugin_entries(self) -> list:
        """Return only plugin-registered platform entries (materialised + lazy).

        See :meth:`all_entries` for the no-materialise contract.
        """
        return [e for e in self.all_entries() if getattr(e, "source", "plugin") == "plugin"]

    def is_registered(self, name: str) -> bool:
        """True if *name* is registered — does NOT materialise a lazy entry.

        A cheap existence check (used to decide whether the gateway handles a
        platform at all) must not pay the adapter import cost.
        """
        return name in self._entries or name in self._lazy

    def create_adapter(self, name: str, config: Any) -> Optional[Any]:
        """Create an adapter instance for the given platform name.

        Returns None if:
        - No entry registered for *name*
        - check_fn() returns False (missing deps)
        - validate_config() returns False (misconfigured)
        - The factory raises an exception

        Materialises a lazy entry on demand — this is the canonical "the
        platform is actually being used now" path, so importing the adapter
        module (and its SDK) here is exactly the intended cost.
        """
        entry = self.get(name)
        if entry is None:
            return None

        if not entry.check_fn():
            hint = f" ({entry.install_hint})" if entry.install_hint else ""
            logger.warning(
                "Platform '%s' requirements not met%s",
                entry.label,
                hint,
            )
            return None

        if entry.validate_config is not None:
            try:
                if not entry.validate_config(config):
                    logger.warning(
                        "Platform '%s' config validation failed",
                        entry.label,
                    )
                    return None
            except Exception as e:
                logger.warning(
                    "Platform '%s' config validation error: %s",
                    entry.label,
                    e,
                )
                return None

        try:
            adapter = entry.adapter_factory(config)
            return adapter
        except Exception as e:
            logger.error(
                "Failed to create adapter for platform '%s': %s",
                entry.label,
                e,
                exc_info=True,
            )
            return None


# Module-level singleton
platform_registry = PlatformRegistry()
