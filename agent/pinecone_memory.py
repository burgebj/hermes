from __future__ import annotations

import logging
from typing import Any, Iterable

logger = logging.getLogger(__name__)


class PineconeMemoryClient:
    """Minimal Pinecone wrapper with fail-open behavior and normalized records."""

    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
        pinecone_module: Any | None = None,
    ) -> None:
        self._config = config if config is not None else _load_pinecone_config()
        self._pinecone_module = pinecone_module
        self._index = None

    def is_configured(self) -> bool:
        return bool(self._config.get("api_key") and (self._config.get("index_name") or self._config.get("index_host")))

    def upsert_records(self, records: Iterable[dict[str, Any]], *, namespace: str | None = None) -> int:
        normalized = [self._normalize_record(record) for record in records]
        if not normalized:
            return 0
        if not self.is_configured():
            return self._on_unavailable("upsert_records", default=0, reason="missing Pinecone configuration")
        try:
            index = self._get_index()
            kwargs = {"vectors": normalized}
            effective_namespace = namespace or self._config.get("namespace")
            if effective_namespace:
                kwargs["namespace"] = effective_namespace
            index.upsert(**kwargs)
            return len(normalized)
        except Exception as exc:
            return self._handle_error("upsert_records", exc, default=0)

    def query(
        self,
        *,
        vector: list[float],
        top_k: int = 5,
        namespace: str | None = None,
        filter: dict[str, Any] | None = None,
        include_values: bool = True,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        if not self.is_configured():
            return self._on_unavailable("query", default=[], reason="missing Pinecone configuration")
        try:
            index = self._get_index()
            kwargs: dict[str, Any] = {
                "vector": vector,
                "top_k": top_k,
                "include_values": include_values,
                "include_metadata": include_metadata,
            }
            effective_namespace = namespace or self._config.get("namespace")
            if effective_namespace:
                kwargs["namespace"] = effective_namespace
            if filter:
                kwargs["filter"] = filter
            response = index.query(**kwargs)
            matches = getattr(response, "matches", None)
            if matches is None and isinstance(response, dict):
                matches = response.get("matches", [])
            return [self._normalize_match(match) for match in (matches or [])]
        except Exception as exc:
            return self._handle_error("query", exc, default=[])

    def delete_by_source(
        self,
        *,
        source_kind: str,
        source_id: str,
        source_path: str | None = None,
        namespace: str | None = None,
    ) -> bool:
        if not self.is_configured():
            return self._on_unavailable("delete_by_source", default=False, reason="missing Pinecone configuration")
        filter_payload: dict[str, Any] = {
            "source_kind": {"$eq": source_kind},
            "source_id": {"$eq": source_id},
        }
        if source_path:
            filter_payload["source_path"] = {"$eq": source_path}
        try:
            index = self._get_index()
            kwargs: dict[str, Any] = {"filter": filter_payload}
            effective_namespace = namespace or self._config.get("namespace")
            if effective_namespace:
                kwargs["namespace"] = effective_namespace
            index.delete(**kwargs)
            return True
        except Exception as exc:
            return self._handle_error("delete_by_source", exc, default=False)

    def _get_index(self) -> Any:
        if self._index is not None:
            return self._index
        module = self._pinecone_module
        if module is None:
            import pinecone as module  # type: ignore[import-not-found]
        api_key = self._config.get("api_key")
        client = module.Pinecone(api_key=api_key)
        index_host = self._config.get("index_host")
        index_name = self._config.get("index_name")
        self._index = client.Index(host=index_host) if index_host else client.Index(index_name)
        return self._index

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        metadata = dict(record.get("metadata") or {})
        normalized = {
            "id": str(record["id"]),
            "values": list(record["values"]),
            "metadata": metadata,
        }
        return normalized

    def _normalize_match(self, match: Any) -> dict[str, Any]:
        if hasattr(match, "to_dict"):
            match = match.to_dict()
        elif not isinstance(match, dict):
            match = {
                "id": getattr(match, "id", ""),
                "values": getattr(match, "values", []) or [],
                "metadata": getattr(match, "metadata", {}) or {},
                "score": getattr(match, "score", None),
            }
        normalized = {
            "id": str(match.get("id", "")),
            "values": list(match.get("values") or []),
            "metadata": dict(match.get("metadata") or {}),
        }
        if "score" in match and match.get("score") is not None:
            normalized["score"] = match.get("score")
        return normalized

    def _handle_error(self, operation: str, exc: Exception, *, default: Any) -> Any:
        if self._config.get("fail_open"):
            logger.warning("Pinecone memory %s failed; fail-open enabled: %s", operation, exc)
            return default
        raise exc

    def _on_unavailable(self, operation: str, *, default: Any, reason: str) -> Any:
        if self._config.get("fail_open"):
            logger.warning("Pinecone memory %s skipped; fail-open enabled: %s", operation, reason)
            return default
        raise RuntimeError(f"Pinecone memory {operation} unavailable: {reason}")


def _load_pinecone_config() -> dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        root = load_config() or {}
    except Exception as exc:
        logger.debug("Failed to load Pinecone config: %s", exc)
        root = {}
    pinecone_cfg = root.get("pinecone") or {}
    if not isinstance(pinecone_cfg, dict):
        pinecone_cfg = {}
    return {
        "api_key": pinecone_cfg.get("api_key") or root.get("pinecone_api_key"),
        "index_name": pinecone_cfg.get("index_name") or root.get("pinecone_index_name"),
        "index_host": pinecone_cfg.get("index_host") or root.get("pinecone_index_host"),
        "namespace": pinecone_cfg.get("namespace") or root.get("pinecone_namespace"),
        "fail_open": bool(root.get("pinecone_fail_open", pinecone_cfg.get("fail_open", False))),
    }
