"""LCM Service — Long-term Context Memory for hermes-agent.

FastAPI on port 18732. Hybrid search (FTS5 BM25 + sqlite-vec cosine) followed by
cross-encoder reranking via a sibling reranker service. Pluggable embedding
providers: Ollama (default), OpenAI, Azure OpenAI, AWS Bedrock.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import threading
import uuid
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import httpx
import sqlite_vec
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from auto_capture import SessionManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("lcm-service")


# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "butter-memory.db")))
SNAPSHOT_PATH = Path(os.getenv("SNAPSHOT_PATH", str(DATA_DIR / "MEMORY_SNAPSHOT.md")))

EMBED_PROVIDER = os.getenv("BUTTER_LCM_EMBED_PROVIDER", "ollama").lower()

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_EMBED_MODEL = os.getenv("AZURE_EMBED_MODEL", "")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_EMBED_MODEL = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v1")

RERANKER_URL = os.getenv("RERANKER_URL", "").rstrip("/")

VEC_WEIGHT = float(os.getenv("VECTOR_WEIGHT", "0.4"))
KW_WEIGHT = float(os.getenv("KEYWORD_WEIGHT", "0.6"))
TOP_K = int(os.getenv("TOP_K", "20"))
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))

EMBED_DIM_MAP = {
    "nomic-embed-text": 768,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

VEC_DIM = int(
    os.getenv(
        "VEC_DIM",
        str(
            EMBED_DIM_MAP.get(
                OLLAMA_EMBED_MODEL
                if EMBED_PROVIDER == "ollama"
                else OPENAI_EMBED_MODEL,
                1536,
            )
        ),
    )
)

EMBED_TIMEOUT = float(os.getenv("EMBED_TIMEOUT", "60"))
RERANK_TIMEOUT = float(os.getenv("RERANK_TIMEOUT", "60"))

SESSION_BUFFER_SIZE = int(os.getenv("SESSION_BUFFER_SIZE", "6"))
EXTRACTION_INTERVAL = int(os.getenv("EXTRACTION_INTERVAL", "3"))
IDLE_FLUSH_SECONDS = int(os.getenv("IDLE_FLUSH_SECONDS", "180"))
EXTRACTION_MAX_PER_SESSION = int(os.getenv("EXTRACTION_MAX_PER_SESSION", "5"))
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "llama3.2")
SIMILARITY_HIGH = float(os.getenv("SIMILARITY_HIGH", "0.85"))
SIMILARITY_MED = float(os.getenv("SIMILARITY_MED", "0.65"))
DEBOUNCE_SECONDS = float(os.getenv("DEBOUNCE_SECONDS", "30"))

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Pluggable embedding ──────────────────────────────────────────────────────


def embed_one(text: str) -> list[float]:
    if EMBED_PROVIDER == "ollama":
        return _embed_ollama(text)
    elif EMBED_PROVIDER == "openai":
        return _embed_openai(text)
    elif EMBED_PROVIDER == "azure":
        return _embed_azure(text)
    elif EMBED_PROVIDER == "bedrock":
        return _embed_bedrock(text)
    else:
        raise HTTPException(
            status_code=500, detail=f"unknown embed provider: {EMBED_PROVIDER}"
        )


def _embed_ollama(text: str) -> list[float]:
    try:
        with httpx.Client(timeout=EMBED_TIMEOUT) as client:
            resp = client.post(
                f"{OLLAMA_BASE}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        log.error("ollama embed failed: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"ollama embed error: {exc}"
        ) from exc

    vec = payload.get("embedding")
    if not isinstance(vec, list) or not vec:
        raise HTTPException(status_code=502, detail="ollama returned empty embedding")
    if len(vec) != VEC_DIM:
        raise HTTPException(
            status_code=500,
            detail=f"embedding dim mismatch: got {len(vec)}, expected {VEC_DIM}",
        )
    return vec


def _embed_openai(text: str) -> list[float]:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    try:
        with httpx.Client(timeout=EMBED_TIMEOUT) as client:
            resp = client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={"input": text, "model": OPENAI_EMBED_MODEL},
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        log.error("openai embed failed: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"openai embed error: {exc}"
        ) from exc

    data = payload.get("data")
    if not data or not data[0].get("embedding"):
        raise HTTPException(status_code=502, detail="openai returned empty embedding")
    vec = data[0]["embedding"]
    if len(vec) != VEC_DIM:
        raise HTTPException(
            status_code=500,
            detail=f"embedding dim mismatch: got {len(vec)}, expected {VEC_DIM}",
        )
    return vec


def _embed_azure(text: str) -> list[float]:
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
        raise HTTPException(
            status_code=500,
            detail="AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY required",
        )
    model = AZURE_EMBED_MODEL or OPENAI_EMBED_MODEL
    url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{model}/embeddings?api-version=2024-06-01"
    try:
        with httpx.Client(timeout=EMBED_TIMEOUT) as client:
            resp = client.post(
                url,
                headers={
                    "api-key": AZURE_OPENAI_KEY,
                    "Content-Type": "application/json",
                },
                json={"input": text},
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        log.error("azure embed failed: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"azure embed error: {exc}"
        ) from exc

    data = payload.get("data")
    if not data or not data[0].get("embedding"):
        raise HTTPException(status_code=502, detail="azure returned empty embedding")
    vec = data[0]["embedding"]
    if len(vec) != VEC_DIM:
        raise HTTPException(
            status_code=500,
            detail=f"embedding dim mismatch: got {len(vec)}, expected {VEC_DIM}",
        )
    return vec


def _embed_bedrock(text: str) -> list[float]:
    try:
        import boto3
    except ImportError:
        raise HTTPException(
            status_code=500, detail="boto3 not installed for bedrock provider"
        )

    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    model = BEDROCK_EMBED_MODEL
    try:
        if "titan" in model:
            body = json.dumps({"inputText": text})
        else:
            body = json.dumps({"inputText": text})

        response = client.invoke_model(
            body=body,
            modelId=model,
            accept="application/json",
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        vec = result.get("embedding")
    except Exception as exc:
        log.error("bedrock embed failed: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"bedrock embed error: {exc}"
        ) from exc

    if not isinstance(vec, list) or not vec:
        raise HTTPException(status_code=502, detail="bedrock returned empty embedding")
    return vec


# ── DB layer ──────────────────────────────────────────────────────────────────

_db_lock = threading.Lock()


def _open_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS memories (
            id           TEXT PRIMARY KEY,
            content      TEXT NOT NULL,
            category     TEXT NOT NULL DEFAULT 'general',
            source       TEXT NOT NULL DEFAULT 'manual',
            created_at   REAL NOT NULL,
            archived_at  REAL,
            is_archived  INTEGER NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
        CREATE INDEX IF NOT EXISTS idx_memories_created  ON memories(created_at);
        CREATE INDEX IF NOT EXISTS idx_memories_archived ON memories(is_archived);

        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(content, tokenize = 'porter unicode61');

        CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec
            USING vec0(embedding float[{VEC_DIM}]);

        CREATE TABLE IF NOT EXISTS memory_auto_meta (
            memory_id          TEXT PRIMARY KEY,
            session_id         TEXT,
            extracted_at       REAL,
            model_used         TEXT,
            confidence         REAL,
            related_to_id      TEXT,
            contradiction_of_id TEXT,
            raw_extraction     TEXT
        );
        """
    )


db = _open_db(DB_PATH)
_init_schema(db)


@contextmanager
def db_txn():
    with _db_lock:
        db.execute("BEGIN")
        try:
            yield db
        except Exception:
            db.execute("ROLLBACK")
            raise
        else:
            db.execute("COMMIT")


session_manager = SessionManager(db, _db_lock, db_txn)


# ── Search primitives ─────────────────────────────────────────────────────────


def keyword_search(query: str, limit: int) -> dict[int, float]:
    fts_query = _sanitize_fts(query)
    if not fts_query:
        return {}
    try:
        cur = db.execute(
            """
            SELECT rowid, bm25(memories_fts) AS score
            FROM memories_fts
            WHERE memories_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (fts_query, limit),
        )
        return {row["rowid"]: row["score"] for row in cur.fetchall()}
    except sqlite3.OperationalError as exc:
        log.warning("fts query failed (%s) for %r", exc, fts_query)
        return {}


def vector_search(embedding: list[float], limit: int) -> dict[int, float]:
    blob = sqlite_vec.serialize_float32(embedding)
    cur = db.execute(
        """
        SELECT rowid, distance
        FROM memories_vec
        WHERE embedding MATCH ?
          AND k = ?
        ORDER BY distance
        """,
        (blob, limit),
    )
    return {row["rowid"]: row["distance"] for row in cur.fetchall()}


def _sanitize_fts(query: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in query)
    tokens = [t for t in cleaned.split() if t]
    return " ".join(tokens)


def _normalise(values: Iterable[float], invert: bool = False) -> dict[int, float]:
    items = list(values)
    if not items:
        return {}
    nums = [v for _, v in items]
    lo, hi = min(nums), max(nums)
    span = hi - lo
    out: dict[int, float] = {}
    for rowid, val in items:
        if span <= 0:
            out[rowid] = 1.0
            continue
        scaled = (val - lo) / span
        out[rowid] = 1.0 - scaled if invert else scaled
    return out


def hybrid_search(query: str, embedding: list[float], top_k: int) -> list[dict]:
    pool = max(top_k, TOP_K)
    kw_raw = keyword_search(query, pool)
    vec_raw = vector_search(embedding, pool)

    kw_norm = _normalise(kw_raw.items(), invert=True)
    vec_norm = _normalise(vec_raw.items(), invert=True)

    combined: dict[int, float] = {}
    for rowid in set(kw_norm) | set(vec_norm):
        combined[rowid] = VEC_WEIGHT * vec_norm.get(
            rowid, 0.0
        ) + KW_WEIGHT * kw_norm.get(rowid, 0.0)

    if not combined:
        return []

    ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    rowids = [r for r, _ in ranked]
    placeholders = ",".join("?" * len(rowids))
    cur = db.execute(
        f"""
        SELECT rowid, id, content, category, source, created_at
        FROM memories
        WHERE rowid IN ({placeholders}) AND is_archived = 0
        """,
        rowids,
    )
    by_rowid = {row["rowid"]: row for row in cur.fetchall()}

    results: list[dict] = []
    for rowid, score in ranked:
        row = by_rowid.get(rowid)
        if row is None:
            continue
        results.append(
            {
                "id": row["id"],
                "content": row["content"],
                "category": row["category"],
                "source": row["source"],
                "created_at": row["created_at"],
                "hybrid_score": score,
                "vec_distance": vec_raw.get(rowid),
                "bm25": kw_raw.get(rowid),
            }
        )
    return results


# ── Reranker ──────────────────────────────────────────────────────────────────


def rerank(query: str, candidates: list[dict]) -> list[dict]:
    if not candidates or not RERANKER_URL:
        for c in candidates:
            c["rerank_score"] = None
        return candidates
    docs = [c["content"] for c in candidates]
    try:
        with httpx.Client(timeout=RERANK_TIMEOUT) as client:
            resp = client.post(
                f"{RERANKER_URL}/rerank",
                json={"query": query, "documents": docs},
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        log.warning("reranker unavailable (%s) — falling back to hybrid order", exc)
        for c in candidates:
            c["rerank_score"] = None
        return candidates

    scores = payload.get("scores") or []
    rankings = payload.get("rankings")
    if len(scores) != len(candidates):
        log.warning(
            "reranker returned %d scores for %d docs", len(scores), len(candidates)
        )
        for c in candidates:
            c["rerank_score"] = None
        return candidates

    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)

    if rankings and len(rankings) == len(candidates):
        order = [candidates[i] for i in rankings if 0 <= i < len(candidates)]
    else:
        order = sorted(candidates, key=lambda c: c["rerank_score"] or 0.0, reverse=True)
    return order


# ── API ───────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def _lifespan(app: FastAPI):
    log.info(
        "lcm-service ready: db=%s provider=%s reranker=%s vec_dim=%d",
        DB_PATH,
        EMBED_PROVIDER,
        RERANKER_URL or "(disabled)",
        VEC_DIM,
    )
    yield
    await session_manager.flush_all()


app = FastAPI(title="LCM Service", version="1.0.0", lifespan=_lifespan)


class StoreRequest(BaseModel):
    content: str = Field(min_length=1)
    category: str = "general"
    source: str = "manual"


class StoreResponse(BaseModel):
    id: str
    status: str = "stored"


class RecallRequest(BaseModel):
    query: str = Field(min_length=1)
    category: Optional[str] = None
    limit: int = Field(default=RERANK_TOP_K, ge=1, le=100)
    candidate_pool: int = Field(default=TOP_K, ge=1, le=200)


class RecallResult(BaseModel):
    id: str
    content: str
    category: str
    source: str
    created_at: float
    hybrid_score: float
    rerank_score: Optional[float] = None


class RecallResponse(BaseModel):
    results: list[RecallResult]
    reranked: bool


class ForgetRequest(BaseModel):
    id: str = Field(min_length=1)


class MemoryListItem(BaseModel):
    id: str
    content: str
    category: str
    source: str
    created_at: float
    auto_meta: Optional[dict] = None


class MemoryListResponse(BaseModel):
    items: list[MemoryListItem]
    total: int


class AutoCaptureDisableRequest(BaseModel):
    session_id: str


class AutoCaptureEnableRequest(BaseModel):
    session_id: str


class SessionTurnRequest(BaseModel):
    session_id: str = Field(min_length=1)
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(min_length=1)


class TurnPairRequest(BaseModel):
    session_id: str = Field(min_length=1)
    user_content: str = Field(min_length=1)
    assistant_content: str = Field(min_length=1)


class SessionTurnResponse(BaseModel):
    status: str = "buffered"
    session_id: str
    turn_count: int = 0


class SessionEndRequest(BaseModel):
    session_id: str = Field(min_length=1)


@app.post("/memory/session/turn", response_model=SessionTurnResponse)
async def memory_session_turn(req: SessionTurnRequest) -> SessionTurnResponse:
    try:
        await session_manager.add_turn(
            session_id=req.session_id,
            role=req.role,
            content=req.content,
        )
        session = session_manager._sessions.get(req.session_id)
        turn_count = session.turn_count if session else 0
        return SessionTurnResponse(
            session_id=req.session_id,
            turn_count=turn_count,
        )
    except Exception as exc:
        log.error("auto-capture turn ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/memory/session/turn_pair", response_model=SessionTurnResponse)
async def memory_session_turn_pair(req: TurnPairRequest) -> SessionTurnResponse:
    try:
        await session_manager.add_turn(
            session_id=req.session_id,
            role="user",
            content=req.user_content,
        )
        await session_manager.add_turn(
            session_id=req.session_id,
            role="assistant",
            content=req.assistant_content,
        )
        session = session_manager._sessions.get(req.session_id)
        turn_count = session.turn_count if session else 0
        return SessionTurnResponse(
            session_id=req.session_id,
            turn_count=turn_count,
        )
    except Exception as exc:
        log.error("auto-capture turn_pair ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/memory/session/end")
async def memory_session_end(req: SessionEndRequest) -> dict:
    await session_manager.end_session(req.session_id)
    return {"status": "ended", "session_id": req.session_id}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "lcm",
        "version": "1.0.0",
        "embed_provider": EMBED_PROVIDER,
    }


@app.get("/stats")
def stats() -> dict:
    with _db_lock:
        total = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        active = db.execute(
            "SELECT COUNT(*) FROM memories WHERE is_archived = 0"
        ).fetchone()[0]
        archived = total - active
        vec_count = db.execute("SELECT COUNT(*) FROM memories_vec").fetchone()[0]
    return {
        "total": total,
        "active": active,
        "archived": archived,
        "vectors": vec_count,
        "db_path": str(DB_PATH),
        "embed_provider": EMBED_PROVIDER,
    }


@app.post("/memory/store", response_model=StoreResponse)
def memory_store(req: StoreRequest) -> StoreResponse:
    embedding = embed_one(req.content)
    blob = sqlite_vec.serialize_float32(embedding)
    memory_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).timestamp()

    with db_txn() as conn:
        cur = conn.execute(
            """
            INSERT INTO memories (id, content, category, source, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (memory_id, req.content, req.category, req.source, created_at),
        )
        rowid = cur.lastrowid
        conn.execute(
            "INSERT INTO memories_fts(rowid, content) VALUES (?, ?)",
            (rowid, req.content),
        )
        conn.execute(
            "INSERT INTO memories_vec(rowid, embedding) VALUES (?, ?)",
            (rowid, blob),
        )

    log.info("stored memory %s (rowid=%d, category=%s)", memory_id, rowid, req.category)
    return StoreResponse(id=memory_id)


@app.post("/memory/recall", response_model=RecallResponse)
def memory_recall(req: RecallRequest) -> RecallResponse:
    embedding = embed_one(req.query)

    with _db_lock:
        candidates = hybrid_search(req.query, embedding, top_k=req.candidate_pool)

    if req.category:
        candidates = [c for c in candidates if c.get("category") == req.category]

    if not candidates:
        return RecallResponse(results=[], reranked=False)

    ordered = rerank(req.query, candidates)
    reranked_flag = any(c.get("rerank_score") is not None for c in ordered)
    trimmed = ordered[: req.limit]

    return RecallResponse(
        results=[
            RecallResult(
                id=c["id"],
                content=c["content"],
                category=c["category"],
                source=c["source"],
                created_at=c["created_at"],
                hybrid_score=c["hybrid_score"],
                rerank_score=c.get("rerank_score"),
            )
            for c in trimmed
        ],
        reranked=reranked_flag,
    )


@app.post("/memory/forget")
def memory_forget(req: ForgetRequest) -> dict:
    with db_txn() as conn:
        row = conn.execute(
            "SELECT rowid FROM memories WHERE id = ?", (req.id,)
        ).fetchone()
        if row is None:
            return {"status": "not_found", "id": req.id}
        rowid = row["rowid"]
        conn.execute("DELETE FROM memories WHERE id = ?", (req.id,))
        conn.execute("DELETE FROM memories_fts WHERE rowid = ?", (rowid,))
        conn.execute("DELETE FROM memories_vec WHERE rowid = ?", (rowid,))

    log.info("forgot memory %s (rowid=%d)", req.id, rowid)
    return {"status": "forgotten", "id": req.id}


@app.post("/memory/snapshot")
def memory_snapshot() -> dict:
    with _db_lock:
        rows = db.execute(
            """
            SELECT id, content, category, source, created_at
            FROM memories
            WHERE is_archived = 0
            ORDER BY created_at DESC
            """
        ).fetchall()

    lines = [
        "# LCM Memory Snapshot",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} — {len(rows)} memories_",
        "",
    ]
    for row in rows:
        ts = datetime.fromtimestamp(row["created_at"], tz=timezone.utc).isoformat()
        lines.append(f"## [{row['category']}] {row['id']}")
        lines.append(f"_source={row['source']} · created={ts}_")
        lines.append("")
        lines.append(row["content"])
        lines.append("")

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text("\n".join(lines), encoding="utf-8")
    log.info("snapshot written: %d memories → %s", len(rows), SNAPSHOT_PATH)
    return {"status": "ok", "count": len(rows), "path": str(SNAPSHOT_PATH)}


@app.get("/memory/list", response_model=MemoryListResponse)
def memory_list(
    source: str = "all", limit: int = 20, offset: int = 0
) -> MemoryListResponse:
    allowed_sources = {"auto", "manual", "all"}
    if source not in allowed_sources:
        raise HTTPException(
            status_code=400, detail=f"source must be one of {allowed_sources}"
        )

    with _db_lock:
        if source == "all":
            count_row = db.execute(
                "SELECT COUNT(*) FROM memories WHERE is_archived = 0"
            ).fetchone()
            rows = db.execute(
                "SELECT id, content, category, source, created_at "
                "FROM memories WHERE is_archived = 0 "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        else:
            count_row = db.execute(
                "SELECT COUNT(*) FROM memories WHERE is_archived = 0 AND source = ?",
                (source,),
            ).fetchone()
            rows = db.execute(
                "SELECT id, content, category, source, created_at "
                "FROM memories WHERE is_archived = 0 AND source = ? "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (source, limit, offset),
            ).fetchall()

    total = count_row[0]
    items: list[MemoryListItem] = []
    for row in rows:
        auto_meta = None
        if row["source"] == "auto":
            auto_meta = session_manager.get_auto_meta(row["id"])
        items.append(
            MemoryListItem(
                id=row["id"],
                content=row["content"],
                category=row["category"],
                source=row["source"],
                created_at=row["created_at"],
                auto_meta=auto_meta,
            )
        )

    return MemoryListResponse(items=items, total=total)


@app.post("/memory/auto-capture/disable")
def auto_capture_disable(req: AutoCaptureDisableRequest) -> dict:
    ok = session_manager.disable_auto_capture(req.session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="session not found")
    return {"status": "disabled", "session_id": req.session_id}


@app.post("/memory/auto-capture/enable")
def auto_capture_enable(req: AutoCaptureEnableRequest) -> dict:
    ok = session_manager.enable_auto_capture(req.session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="session not found")
    return {"status": "enabled", "session_id": req.session_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=18732, log_level="info")
