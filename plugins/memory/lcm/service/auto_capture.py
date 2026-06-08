"""Butter LCM Auto-Capture — Background session memory extraction.

Runs as an async background task managed by the FastAPI app lifespan.
Extracts durable facts from conversation turns and persists them to the
existing sqlite-vec + FTS5 LCM store.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sqlite3
import struct
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

log = logging.getLogger("butter-lcm.auto_capture")

# ── Config (env vars) ──────────────────────────────────────────────────────────

SESSION_BUFFER_SIZE = int(os.getenv("SESSION_BUFFER_SIZE", "6"))
EXTRACTION_INTERVAL = int(os.getenv("EXTRACTION_INTERVAL", "3"))
IDLE_FLUSH_SECONDS = int(os.getenv("IDLE_FLUSH_SECONDS", "180"))
EXTRACTION_MAX_PER_SESSION = int(os.getenv("EXTRACTION_MAX_PER_SESSION", "5"))
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip(
    "/"
)
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "llama3.2")
SIMILARITY_HIGH = float(os.getenv("SIMILARITY_HIGH", "0.85"))
SIMILARITY_MED = float(os.getenv("SIMILARITY_MED", "0.65"))
SIMILARITY_LOW = float(os.getenv("SIMILARITY_LOW", "0.65"))
DEBOUNCE_SECONDS = float(os.getenv("DEBOUNCE_SECONDS", "30"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_TIMEOUT = float(os.getenv("EMBED_TIMEOUT", "60"))
SNAPSHOT_PATH = Path(os.getenv("SNAPSHOT_PATH", "/app/data/MEMORY_SNAPSHOT.md"))
VEC_DIM = int(os.getenv("VEC_DIM", "768"))

# ── Privacy patterns ───────────────────────────────────────────────────────────

PRIVACY_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"xox[baprs]-[a-zA-Z0-9]{10,}"),
    re.compile(r"AIza[a-zA-Z0-9_-]{35}"),
    re.compile(r"amzn\.mfa[a-zA-Z0-9]+"),
    re.compile(r"-----BEGIN [A-Z]+ PRIVATE KEY-----"),
    re.compile(r"Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),
]

# ── Extraction prompts ─────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = (
    "You are a memory extraction system. Given a conversation, extract durable facts — "
    "user preferences, project context, decisions, biographical details, and technical "
    "preferences. Return STRICT JSON only. No prose outside the JSON object.\n\n"
    "Rules:\n"
    "- Extract ONLY facts worth remembering long-term\n"
    '- Skip: debugging questions, syntax lookups, transient tasks, "thanks"\n'
    "- Each fact must be a standalone, self-contained statement\n"
    '- Use the user\'s voice (e.g., "Harsh prefers dark mode")\n'
    "- Confidence: 0.0-1.0 for each fact\n\n"
    "Return format:\n"
    '{\n  "facts": [\n    {\n      "content": "...",\n      "confidence": 0.9,\n'
    '      "category": "user|preference|work|project|decision|technical"\n    }\n  ]\n}\n\n'
    'If no durable facts: {"facts": []}'
)

EXTRACTION_STRICT_PROMPT = (
    EXTRACTION_SYSTEM_PROMPT
    + "\n\nIMPORTANT: Your response must be parseable by json.loads(). "
    'If you cannot produce valid JSON, return exactly: {"facts": []}'
)

MERGE_PROMPT = (
    'Given existing memory: "{existing}"\n'
    'And new fact: "{new}"\n'
    'Decide: "update_existing", "skip_as_duplicate", or "insert_as_variant"\n'
    'Return: {{"decision": "update_existing|skip_as_duplicate|insert_as_variant", '
    '"merged_content": "..."}}'
)

# ── Data models ────────────────────────────────────────────────────────────────


@dataclass
class Turn:
    role: str
    content: str
    timestamp: float


@dataclass
class Session:
    id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    turns: list[Turn] = field(default_factory=list)
    turn_count: int = 0
    extraction_count: int = 0
    auto_capture_enabled: bool = True
    last_extraction_at: Optional[float] = None
    idle_task: Optional[asyncio.Task] = None


# ── Helpers ────────────────────────────────────────────────────────────────────


def redact_private(text: str) -> str:
    for pat in PRIVACY_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def embed_one_sync(text: str) -> list[float]:
    try:
        with httpx.Client(timeout=EMBED_TIMEOUT) as client:
            resp = client.post(
                f"{OLLAMA_BASE}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        log.error("auto-capture embed failed: %s", exc)
        return []

    vec = payload.get("embedding")
    if not isinstance(vec, list) or not vec:
        return []
    return vec


def _rowid_for_memory(conn: sqlite3.Connection, memory_id: str) -> Optional[int]:
    row = conn.execute(
        "SELECT rowid FROM memories WHERE id = ?", (memory_id,)
    ).fetchone()
    return row[0] if row else None


def hybrid_search_for_auto(
    conn: sqlite3.Connection,
    query: str,
    embedding: list[float],
    top_k: int = 3,
) -> list[dict]:
    import sqlite_vec

    blob = sqlite_vec.serialize_float32(embedding)

    fts_query = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in query)
    tokens = [t for t in fts_query.split() if t]
    fts_query = " ".join(tokens)

    kw_results: dict[int, float] = {}
    if fts_query:
        try:
            cur = conn.execute(
                "SELECT rowid, bm25(memories_fts) AS score FROM memories_fts "
                "WHERE memories_fts MATCH ? ORDER BY score LIMIT ?",
                (fts_query, top_k * 3),
            )
            kw_results = {row["rowid"]: row[1] for row in cur.fetchall()}
        except sqlite3.OperationalError:
            pass

    vec_results: dict[int, float] = {}
    try:
        cur = conn.execute(
            "SELECT rowid, distance FROM memories_vec WHERE embedding MATCH ? AND k = ? "
            "ORDER BY distance",
            (blob, top_k * 3),
        )
        vec_results = {row["rowid"]: row[1] for row in cur.fetchall()}
    except sqlite3.OperationalError:
        pass

    def normalise(values: dict[int, float], invert: bool = False) -> dict[int, float]:
        if not values:
            return {}
        nums = list(values.values())
        lo, hi = min(nums), max(nums)
        span = hi - lo
        out = {}
        for rid, val in values.items():
            if span <= 0:
                out[rid] = 1.0
            else:
                scaled = (val - lo) / span
                out[rid] = 1.0 - scaled if invert else scaled
        return out

    kw_norm = normalise(kw_results, invert=True)
    vec_norm = normalise(vec_results, invert=True)

    vec_weight = 0.4
    kw_weight = 0.6
    combined: dict[int, float] = {}
    for rid in set(kw_norm) | set(vec_norm):
        combined[rid] = vec_weight * vec_norm.get(rid, 0.0) + kw_weight * kw_norm.get(
            rid, 0.0
        )

    if not combined:
        return []

    ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    rowids = [r for r, _ in ranked]
    placeholders = ",".join("?" * len(rowids))
    rows = conn.execute(
        f"SELECT rowid, id, content, category, source, created_at "
        f"FROM memories WHERE rowid IN ({placeholders}) AND is_archived = 0",
        rowids,
    ).fetchall()

    by_rowid = {row[0]: row for row in rows}
    results = []
    for rid, score in ranked:
        row = by_rowid.get(rid)
        if row is None:
            continue
        results.append(
            {
                "id": row[1],
                "content": row[2],
                "category": row[3],
                "source": row[4],
                "created_at": row[5],
                "hybrid_score": score,
            }
        )
    return results


# ── Session Manager ────────────────────────────────────────────────────────────


class SessionManager:
    def __init__(self, db: sqlite3.Connection, db_lock, db_txn_fn):
        self._db = db
        self._db_lock = db_lock
        self._db_txn = db_txn_fn
        self._sessions: dict[str, Session] = {}
        self._last_snapshot_at: float = 0.0
        self._last_debounce: dict[str, float] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        session = Session(id=session_id or f"sess_{uuid.uuid4().hex[:8]}")
        self._sessions[session.id] = session
        return session

    def disable_auto_capture(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session.auto_capture_enabled = False
        return True

    def enable_auto_capture(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session.auto_capture_enabled = True
        return True

    async def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        session = self.get_or_create_session(session_id)
        if not session.auto_capture_enabled:
            return

        redacted = redact_private(content)
        turn = Turn(role=role, content=redacted, timestamp=time.time())
        session.turns.append(turn)
        if len(session.turns) > SESSION_BUFFER_SIZE:
            session.turns = session.turns[-SESSION_BUFFER_SIZE:]
        session.turn_count += 1

        if session.idle_task is not None:
            session.idle_task.cancel()
            try:
                await session.idle_task
            except asyncio.CancelledError:
                pass
        session.idle_task = asyncio.create_task(self._idle_flush(session.id))

        if session.turn_count % EXTRACTION_INTERVAL == 0:
            await self._trigger_extraction(session)

    async def _idle_flush(self, session_id: str) -> None:
        try:
            await asyncio.sleep(IDLE_FLUSH_SECONDS)
            session = self._sessions.get(session_id)
            if session and session.auto_capture_enabled:
                await self._trigger_extraction(session)
        except asyncio.CancelledError:
            pass

    async def end_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        if session.idle_task is not None:
            session.idle_task.cancel()
            try:
                await session.idle_task
            except asyncio.CancelledError:
                pass
        if session.auto_capture_enabled and session.turns:
            await self._trigger_extraction(session)
        self._sessions.pop(session_id, None)

    async def flush_all(self) -> None:
        session_ids = list(self._sessions.keys())
        for sid in session_ids:
            await self.end_session(sid)

    async def _trigger_extraction(self, session: Session) -> None:
        if session.extraction_count >= EXTRACTION_MAX_PER_SESSION:
            log.info(
                json.dumps(
                    {
                        "event": "cost_ceiling_hit",
                        "session_id": session.id,
                        "extraction_count": session.extraction_count,
                    }
                )
            )
            return

        if not session.turns:
            return

        turns_text = "\n".join(f"{t.role}: {t.content}" for t in session.turns)

        facts = await self._extract_facts(turns_text, session.id)
        if facts:
            await self._persist_facts(facts, session)

        session.extraction_count += 1
        session.last_extraction_at = time.time()
        session.turns.clear()

    async def _extract_facts(self, turns_text: str, session_id: str) -> list[dict]:
        payload = await self._call_llm(
            EXTRACTION_SYSTEM_PROMPT,
            turns_text,
            session_id,
        )
        if payload is not None:
            facts = payload.get("facts", [])
            if isinstance(facts, list):
                return facts

        payload = await self._call_llm(
            EXTRACTION_STRICT_PROMPT,
            turns_text,
            session_id,
        )
        if payload is not None:
            facts = payload.get("facts", [])
            if isinstance(facts, list):
                return facts

        return []

    async def _call_llm(
        self, system_prompt: str, user_text: str, session_id: str
    ) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{OLLAMA_BASE}/api/chat",
                    json={
                        "model": EXTRACTION_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_text},
                        ],
                        "stream": False,
                        "format": "json",
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                content = body.get("message", {}).get("content", "")
        except Exception as exc:
            log.warning("extraction LLM call failed: %s", exc)
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            log.info(
                json.dumps(
                    {
                        "event": "extraction_failed",
                        "reason": "malformed_json",
                        "session_id": session_id,
                        "attempted_content": content[:200],
                    }
                )
            )
            return None

    async def _persist_facts(self, facts: list[dict], session: Session) -> None:
        for fact in facts:
            content = fact.get("content", "").strip()
            if not content:
                continue

            confidence = float(fact.get("confidence", 0.5))
            category = fact.get("category", "general")

            now = time.time()
            content_lower = content.lower()
            last_ts = self._last_debounce.get(content_lower, 0.0)
            if now - last_ts < DEBOUNCE_SECONDS:
                log.debug("debounced duplicate fact: %s", content[:60])
                continue
            self._last_debounce[content_lower] = now

            embedding = embed_one_sync(content)
            if not embedding:
                log.warning("skipping fact — embedding failed: %s", content[:60])
                continue

            await self._similarity_check_and_store(
                content, embedding, category, confidence, session
            )

        await self._maybe_snapshot()

    async def _similarity_check_and_store(
        self,
        content: str,
        embedding: list[float],
        category: str,
        confidence: float,
        session: Session,
    ) -> None:
        with self._db_lock:
            candidates = hybrid_search_for_auto(self._db, content, embedding, top_k=3)

        max_sim = 0.0
        best_match: Optional[dict] = None
        if candidates:
            best_match = candidates[0]
            max_sim = best_match.get("hybrid_score", 0.0)

        if max_sim > SIMILARITY_HIGH and best_match:
            await self._merge_step(
                content, embedding, category, confidence, session, best_match
            )
        elif max_sim > SIMILARITY_MED and best_match:
            await self._insert_memory(
                content,
                embedding,
                category,
                confidence,
                session,
                related_to_id=best_match["id"],
            )
        else:
            await self._insert_memory(content, embedding, category, confidence, session)

    async def _merge_step(
        self,
        new_content: str,
        embedding: list[float],
        category: str,
        confidence: float,
        session: Session,
        existing: dict,
    ) -> None:
        merge_prompt = MERGE_PROMPT.format(
            existing=existing["content"], new=new_content
        )
        result = await self._call_llm(merge_prompt, "", session.id)

        if result is None:
            await self._insert_memory(
                new_content, embedding, category, confidence, session
            )
            return

        decision = result.get("decision", "insert_as_variant")
        merged_content = result.get("merged_content", new_content)

        if decision == "skip_as_duplicate":
            log.debug("skipped duplicate: %s", new_content[:60])
            return
        elif decision == "update_existing":
            await self._update_existing(
                existing["id"], merged_content or new_content, session
            )
        else:
            await self._insert_memory(
                merged_content or new_content, embedding, category, confidence, session
            )

    async def _update_existing(
        self, memory_id: str, new_content: str, session: Session
    ) -> None:
        import sqlite_vec

        embedding = embed_one_sync(new_content)
        if not embedding:
            return

        blob = sqlite_vec.serialize_float32(embedding)

        with self._db_txn() as conn:
            row = conn.execute(
                "SELECT rowid, content FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
            if row is None:
                return
            rowid = row[0]
            old_content = row[1]

            if self._detect_contradiction(old_content, new_content):
                await self._insert_memory(
                    new_content,
                    embedding,
                    "general",
                    0.5,
                    session,
                    contradiction_of_id=memory_id,
                )
                return

            conn.execute(
                "UPDATE memories SET content = ? WHERE id = ?",
                (new_content, memory_id),
            )
            conn.execute(
                "UPDATE memories_fts SET content = ? WHERE rowid = ?",
                (new_content, rowid),
            )
            conn.execute("DELETE FROM memories_vec WHERE rowid = ?", (rowid,))
            conn.execute(
                "INSERT INTO memories_vec(rowid, embedding) VALUES (?, ?)",
                (rowid, blob),
            )

        log.info("updated memory %s (session=%s)", memory_id, session.id)

    def _detect_contradiction(self, existing: str, new: str) -> bool:
        existing_lower = existing.lower()
        new_lower = new.lower()

        contradiction_patterns = [
            (r"prefers? (\w+)", r"prefers? (\w+)"),
            (r"uses? (\w+)", r"uses? (\w+)"),
            (r"likes? (\w+)", r"likes? (\w+)"),
            (r"hates? (\w+)", r"hates? (\w+)"),
            (r"(?:is|are|am) (?:a |an )?(\w+)", r"(?:is|are|am) (?:not|n't) "),
            (r"(?:is|are|am) not ", r"(?:is|are|am) (?:a |an )?"),
        ]

        import re as _re

        for pat_existing, pat_new in contradiction_patterns:
            m1 = _re.search(pat_existing, existing_lower)
            m2 = _re.search(pat_new, new_lower)
            if m1 and m2:
                g1 = m1.group(1) if m1.lastindex else ""
                g2 = m2.group(1) if m2.lastindex else ""
                if g1 and g2 and g1 != g2:
                    return True
                if not g1 or not g2:
                    return True

        negation_words = ["not ", "n't ", "never ", "no longer "]
        has_neg_existing = any(n in existing_lower for n in negation_words)
        has_neg_new = any(n in new_lower for n in negation_words)
        if has_neg_existing != has_neg_new:
            existing_clean = existing_lower
            new_clean = new_lower
            for n in negation_words:
                existing_clean = existing_clean.replace(n, "")
                new_clean = new_clean.replace(n, "")
            if existing_clean.strip() and new_clean.strip():
                similarity = self._simple_string_similarity(existing_clean, new_clean)
                if similarity > 0.6:
                    return True

        return False

    @staticmethod
    def _simple_string_similarity(a: str, b: str) -> float:
        a_words = set(a.split())
        b_words = set(b.split())
        if not a_words or not b_words:
            return 0.0
        intersection = a_words & b_words
        union = a_words | b_words
        return len(intersection) / len(union)

    async def _insert_memory(
        self,
        content: str,
        embedding: list[float],
        category: str,
        confidence: float,
        session: Session,
        related_to_id: Optional[str] = None,
        contradiction_of_id: Optional[str] = None,
    ) -> None:
        import sqlite_vec

        memory_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).timestamp()
        blob = sqlite_vec.serialize_float32(embedding)
        raw_extraction = json.dumps(
            {
                "content": content,
                "confidence": confidence,
                "category": category,
            }
        )

        with self._db_txn() as conn:
            cur = conn.execute(
                "INSERT INTO memories (id, content, category, source, created_at) "
                "VALUES (?, ?, ?, 'auto', ?)",
                (memory_id, content, category, created_at),
            )
            rowid = cur.lastrowid
            conn.execute(
                "INSERT INTO memories_fts(rowid, content) VALUES (?, ?)",
                (rowid, content),
            )
            conn.execute(
                "INSERT INTO memories_vec(rowid, embedding) VALUES (?, ?)",
                (rowid, blob),
            )
            conn.execute(
                "INSERT OR REPLACE INTO memory_auto_meta "
                "(memory_id, session_id, extracted_at, model_used, confidence, "
                "related_to_id, contradiction_of_id, raw_extraction) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    memory_id,
                    session.id,
                    created_at,
                    EXTRACTION_MODEL,
                    confidence,
                    related_to_id,
                    contradiction_of_id,
                    raw_extraction,
                ),
            )

        has_conflict = contradiction_of_id is not None
        log.info(
            "auto-captured memory %s (session=%s, category=%s, conflict=%s)",
            memory_id,
            session.id,
            category,
            has_conflict,
        )

    async def _maybe_snapshot(self) -> None:
        now = time.time()
        if now - self._last_snapshot_at < 60.0:
            return
        self._last_snapshot_at = now
        try:
            await asyncio.to_thread(self._write_snapshot)
        except Exception as exc:
            log.warning("snapshot write failed: %s", exc)

    def _write_snapshot(self) -> None:
        with self._db_lock:
            rows = self._db.execute(
                "SELECT id, content, category, source, created_at "
                "FROM memories WHERE is_archived = 0 ORDER BY created_at DESC"
            ).fetchall()

        lines = [
            "# Butter Memory Snapshot",
            "",
            f"_Generated {datetime.now(timezone.utc).isoformat()} — {len(rows)} memories_",
            "",
        ]
        for row in rows:
            ts = datetime.fromtimestamp(row[4], tz=timezone.utc).isoformat()
            lines.append(f"## [{row[2]}] {row[0]}")
            header = f"_source={row[3]} · created={ts}_"
            if row[3] == "auto":
                meta_row = None
                with self._db_lock:
                    meta_row = self._db.execute(
                        "SELECT session_id, confidence, extracted_at "
                        "FROM memory_auto_meta WHERE memory_id = ?",
                        (row[0],),
                    ).fetchone()
                if meta_row:
                    header += f" · session_id={meta_row[0]} · confidence={meta_row[1]}"
            lines.append(header)
            lines.append("")
            lines.append(row[1])
            lines.append("")

        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text("\n".join(lines), encoding="utf-8")
        log.info("auto-capture snapshot written: %d memories", len(rows))

    def get_auto_meta(self, memory_id: str) -> Optional[dict]:
        with self._db_lock:
            row = self._db.execute(
                "SELECT memory_id, session_id, extracted_at, model_used, "
                "confidence, related_to_id, contradiction_of_id, raw_extraction "
                "FROM memory_auto_meta WHERE memory_id = ?",
                (memory_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "memory_id": row[0],
            "session_id": row[1],
            "extracted_at": row[2],
            "model_used": row[3],
            "confidence": row[4],
            "related_to_id": row[5],
            "contradiction_of_id": row[6],
            "raw_extraction": row[7],
        }
