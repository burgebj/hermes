"""Jina AI tools for search, reader extraction, embeddings, and reranking."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from tools.registry import registry

JINA_SEARCH_URL = "https://s.jina.ai/"
JINA_READER_BASE_URL = "https://r.jina.ai/"
JINA_API_BASE_URL = "https://api.jina.ai/v1"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_EMBEDDING_MODEL = "jina-embeddings-v3"
DEFAULT_RERANK_MODEL = "jina-reranker-v2-base-multilingual"
MAX_SEARCH_LIMIT = 20
MAX_READ_URLS = 5
MAX_EMBED_INPUTS = 32
MAX_RERANK_DOCUMENTS = 50


def _has_jina_api_key() -> bool:
    return bool((os.getenv("JINA_API_KEY") or "").strip())


def _api_key() -> str:
    key = (os.getenv("JINA_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("JINA_API_KEY is not configured")
    return key


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _request_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
    data = None
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/json",
        "User-Agent": "hermes-agent-jina-tool/1.0",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if not body:
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"Jina API HTTP {exc.code}: {detail}") from exc


def _request_text(url: str) -> str:
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "text/plain, text/markdown, */*",
        "User-Agent": "hermes-agent-jina-tool/1.0",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"Jina Reader HTTP {exc.code}: {detail}") from exc


def jina_search(query: str, limit: int = 5) -> str:
    """Search the web via Jina Search."""
    query = (query or "").strip()
    if not query:
        return _json_dumps({"success": False, "error": "query is required"})
    try:
        limit = max(1, min(int(limit or 5), MAX_SEARCH_LIMIT))
    except (TypeError, ValueError):
        limit = 5
    params = urllib.parse.urlencode({"q": query, "num": limit})
    data = _request_json(f"{JINA_SEARCH_URL}?{params}")
    results = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(results, list):
        results = results[:limit]
    return _json_dumps({"success": True, "query": query, "results": results})


def jina_read(urls: list[str]) -> str:
    """Read/extract one or more URLs via Jina Reader."""
    if not isinstance(urls, list):
        return _json_dumps({"success": False, "error": "urls must be a list"})
    clean_urls = [str(url).strip() for url in urls if str(url).strip()][:MAX_READ_URLS]
    if not clean_urls:
        return _json_dumps({"success": False, "error": "at least one URL is required"})

    results = []
    for url in clean_urls:
        reader_url = JINA_READER_BASE_URL + url
        try:
            content = _request_text(reader_url)
            results.append({"url": url, "content": content, "error": None})
        except Exception as exc:  # keep multi-URL calls best-effort
            results.append({"url": url, "content": "", "error": str(exc)})
    return _json_dumps({"success": True, "results": results})


def jina_embed(
    input: str | list[str],
    model: str = DEFAULT_EMBEDDING_MODEL,
    task: str = "retrieval.query",
) -> str:
    """Create embeddings via Jina Embeddings API."""
    if isinstance(input, str):
        values: str | list[str] = input.strip()
        if not values:
            return _json_dumps({"success": False, "error": "input is required"})
    elif isinstance(input, list):
        values = [str(item) for item in input if str(item).strip()][:MAX_EMBED_INPUTS]
        if not values:
            return _json_dumps({"success": False, "error": "input list is empty"})
    else:
        return _json_dumps({"success": False, "error": "input must be a string or list of strings"})

    payload = {
        "model": (model or DEFAULT_EMBEDDING_MODEL).strip(),
        "task": (task or "retrieval.query").strip(),
        "input": values,
    }
    data = _request_json(f"{JINA_API_BASE_URL}/embeddings", method="POST", payload=payload)
    return _json_dumps({"success": True, **(data if isinstance(data, dict) else {"data": data})})


def _normalize_rerank_result(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"document": item}
    normalized = dict(item)
    document = normalized.get("document")
    if isinstance(document, dict):
        normalized["document"] = document.get("text") or document.get("content") or document
    return normalized


def jina_rerank(
    query: str,
    documents: list[str],
    model: str = DEFAULT_RERANK_MODEL,
    top_n: int | None = None,
) -> str:
    """Rerank documents by relevance to a query via Jina Reranker."""
    query = (query or "").strip()
    if not query:
        return _json_dumps({"success": False, "error": "query is required"})
    if not isinstance(documents, list):
        return _json_dumps({"success": False, "error": "documents must be a list"})
    clean_docs = [str(doc) for doc in documents if str(doc).strip()][:MAX_RERANK_DOCUMENTS]
    if not clean_docs:
        return _json_dumps({"success": False, "error": "at least one document is required"})

    payload: dict[str, Any] = {
        "model": (model or DEFAULT_RERANK_MODEL).strip(),
        "query": query,
        "documents": clean_docs,
    }
    if top_n is not None:
        try:
            payload["top_n"] = max(1, min(int(top_n), len(clean_docs)))
        except (TypeError, ValueError):
            pass
    data = _request_json(f"{JINA_API_BASE_URL}/rerank", method="POST", payload=payload)
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        data = {**data, "results": [_normalize_rerank_result(item) for item in data["results"]]}
    return _json_dumps({"success": True, **(data if isinstance(data, dict) else {"data": data})})


JINA_SEARCH_SCHEMA = {
    "name": "jina_search",
    "description": "Search the web using Jina AI Search. Good for broad web research when JINA_API_KEY is configured.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query."},
            "limit": {"type": "integer", "description": "Maximum results to return.", "minimum": 1, "maximum": MAX_SEARCH_LIMIT, "default": 5},
        },
        "required": ["query"],
    },
}

JINA_READ_SCHEMA = {
    "name": "jina_read",
    "description": "Extract clean markdown/text content from web page URLs using Jina AI Reader.",
    "parameters": {
        "type": "object",
        "properties": {
            "urls": {"type": "array", "items": {"type": "string"}, "description": "URLs to extract, max 5.", "maxItems": MAX_READ_URLS},
        },
        "required": ["urls"],
    },
}

JINA_EMBED_SCHEMA = {
    "name": "jina_embed",
    "description": "Create embeddings with Jina AI Embeddings for retrieval, clustering, or semantic comparison.",
    "parameters": {
        "type": "object",
        "properties": {
            "input": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}], "description": "Text or list of texts to embed."},
            "model": {"type": "string", "description": "Jina embedding model.", "default": DEFAULT_EMBEDDING_MODEL},
            "task": {"type": "string", "description": "Embedding task, e.g. retrieval.query or retrieval.passage.", "default": "retrieval.query"},
        },
        "required": ["input"],
    },
}

JINA_RERANK_SCHEMA = {
    "name": "jina_rerank",
    "description": "Rerank candidate documents/passages by relevance to a query using Jina AI Reranker.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Query to rank against."},
            "documents": {"type": "array", "items": {"type": "string"}, "description": "Candidate documents/passages, max 50."},
            "model": {"type": "string", "description": "Jina reranker model.", "default": DEFAULT_RERANK_MODEL},
            "top_n": {"type": "integer", "description": "Optional number of top results to return.", "minimum": 1},
        },
        "required": ["query", "documents"],
    },
}

registry.register(
    name="jina_search",
    toolset="jina",
    schema=JINA_SEARCH_SCHEMA,
    handler=lambda args, **kw: jina_search(args.get("query", ""), limit=args.get("limit", 5)),
    check_fn=_has_jina_api_key,
    requires_env=["JINA_API_KEY"],
    emoji="🔎",
    max_result_size_chars=100_000,
)
registry.register(
    name="jina_read",
    toolset="jina",
    schema=JINA_READ_SCHEMA,
    handler=lambda args, **kw: jina_read(args.get("urls", [])),
    check_fn=_has_jina_api_key,
    requires_env=["JINA_API_KEY"],
    emoji="📖",
    max_result_size_chars=100_000,
)
registry.register(
    name="jina_embed",
    toolset="jina",
    schema=JINA_EMBED_SCHEMA,
    handler=lambda args, **kw: jina_embed(args.get("input", ""), model=args.get("model", DEFAULT_EMBEDDING_MODEL), task=args.get("task", "retrieval.query")),
    check_fn=_has_jina_api_key,
    requires_env=["JINA_API_KEY"],
    emoji="🧬",
    max_result_size_chars=100_000,
)
registry.register(
    name="jina_rerank",
    toolset="jina",
    schema=JINA_RERANK_SCHEMA,
    handler=lambda args, **kw: jina_rerank(args.get("query", ""), args.get("documents", []), model=args.get("model", DEFAULT_RERANK_MODEL), top_n=args.get("top_n")),
    check_fn=_has_jina_api_key,
    requires_env=["JINA_API_KEY"],
    emoji="🏁",
    max_result_size_chars=100_000,
)
