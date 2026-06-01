#!/usr/bin/env python3
"""
Rebuild state.db from consolidated session JSON files.
Reads all session_*.json from sessions/ dir and imports into a fresh state.db.
"""
import json
import os
import glob
import time
import sqlite3
import re

SESSIONS_DIR = '/home/alfdib/Hermes/hermes-data/sessions'
DB_PATH = '/home/alfdib/Hermes/hermes-data/state.db.new'

# Schema from hermes_state.py (SCHEMA_VERSION = 11)
SCHEMA_VERSION = 11

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    user_id TEXT,
    model TEXT,
    model_config TEXT,
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    cost_source TEXT,
    pricing_version TEXT,
    title TEXT,
    api_call_count INTEGER DEFAULT 0,
    handoff_state TEXT,
    handoff_platform TEXT,
    handoff_error TEXT,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    reasoning_content TEXT,
    reasoning_details TEXT,
    codex_reasoning_items TEXT,
    codex_message_items TEXT
);

CREATE TABLE IF NOT EXISTS state_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source);
CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
"""

FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content
);

CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (
        new.id,
        COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
    );
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    DELETE FROM messages_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    DELETE FROM messages_fts WHERE rowid = old.id;
    INSERT INTO messages_fts(rowid, content) VALUES (
        new.id,
        COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
    );
END;
"""

FTS_TRIGRAM_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts_trigram USING fts5(
    content,
    tokenize='trigram'
);

CREATE TRIGGER IF NOT EXISTS messages_fts_trigram_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts_trigram(rowid, content) VALUES (
        new.id,
        COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
    );
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_trigram_delete AFTER DELETE ON messages BEGIN
    DELETE FROM messages_fts_trigram WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_trigram_update AFTER UPDATE ON messages BEGIN
    DELETE FROM messages_fts_trigram WHERE rowid = old.id;
    INSERT INTO messages_fts_trigram(rowid, content) VALUES (
        new.id,
        COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
    );
END;
"""


def parse_session_datetime(dt_str):
    """Parse ISO format datetime to Unix timestamp."""
    if isinstance(dt_str, (int, float)):
        return float(dt_str)
    try:
        dt_str = dt_str.replace('Z', '+00:00')
        from datetime import datetime
        # Try ISO format
        dt = datetime.fromisoformat(dt_str)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return time.time()


def extract_title_from_messages(messages):
    """Try to infer a title from the first user message."""
    for msg in messages:
        if msg.get('role') == 'user' and msg.get('content'):
            text = msg['content']
            if isinstance(text, str):
                text = text.strip()[:60]
                if text:
                    return text
    return None


def import_sessions():
    # Remove old DB if exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA_SQL)
    
    # Create FTS tables separately
    conn.executescript(FTS_SQL)
    conn.executescript(FTS_TRIGRAM_SQL)
    
    # Set schema version
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    conn.execute("INSERT INTO state_meta (key, value) VALUES (?, ?)", ('db_version', str(SCHEMA_VERSION)))
    conn.execute("INSERT INTO state_meta (key, value) VALUES (?, ?)", ('initialized_at', str(time.time())))
    
    conn.commit()
    
    # Scan session files
    session_files = sorted(glob.glob(os.path.join(SESSIONS_DIR, 'session_*.json')))
    print(f"Found {len(session_files)} session files")
    
    total_messages = 0
    total_sessions = 0
    errors = 0
    
    for fpath in session_files:
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  ERROR reading {os.path.basename(fpath)}: {e}")
            errors += 1
            continue
        
        session_id = data.get('session_id', '')
        if not session_id:
            session_id = os.path.splitext(os.path.basename(fpath))[0].replace('session_', '')
        
        started_at = parse_session_datetime(data.get('session_start', time.time()))
        last_updated = parse_session_datetime(data.get('last_updated', started_at))
        model = data.get('model', '')
        base_url = data.get('base_url', '')
        platform = data.get('platform', 'cli')
        system_prompt = data.get('system_prompt', '')
        message_count = data.get('message_count', 0)
        messages = data.get('messages', [])
        
        # Calculate token counts from messages if available
        input_tokens = 0
        output_tokens = 0
        for msg in messages:
            tc = msg.get('token_count', 0) or 0
            if msg.get('role') in ('user', 'system'):
                input_tokens += tc
            elif msg.get('role') == 'assistant':
                output_tokens += tc
        
        # Count tool calls
        tool_call_count = 0
        for msg in messages:
            if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                try:
                    tc = json.loads(msg['tool_calls']) if isinstance(msg['tool_calls'], str) else msg['tool_calls']
                    tool_call_count += len(tc) if isinstance(tc, list) else 0
                except (json.JSONDecodeError, TypeError):
                    pass
        
        api_call_count = sum(1 for msg in messages if msg.get('role') == 'assistant')
        title = extract_title_from_messages(messages)
        
        # Determine source
        source = platform or 'cli'
        
        try:
            conn.execute("""
                INSERT OR IGNORE INTO sessions 
                (id, source, model, system_prompt, started_at, ended_at, message_count, 
                 tool_call_count, input_tokens, output_tokens, api_call_count, title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, source, model, system_prompt, 
                started_at, last_updated, message_count,
                tool_call_count, input_tokens, output_tokens, api_call_count, title
            ))
        except sqlite3.IntegrityError:
            print(f"  SKIP duplicate session: {session_id}")
            continue
        
        # Insert messages
        for idx, msg in enumerate(messages):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            tool_call_id = msg.get('tool_call_id', '')
            tool_name = msg.get('tool_name', '')
            token_count = msg.get('token_count', 0)
            finish_reason = msg.get('finish_reason', '')
            
            # Handle tool_calls - serialize to JSON string
            tool_calls = msg.get('tool_calls')
            if tool_calls and not isinstance(tool_calls, str):
                tool_calls = json.dumps(tool_calls)
            
            # Handle reasoning content
            reasoning = msg.get('reasoning', '')
            reasoning_content = msg.get('reasoning_content', '')
            
            # Timestamp - approximate from position in conversation
            msg_timestamp = started_at + (idx * 0.5)  # ~0.5s per message
            
            conn.execute("""
                INSERT INTO messages 
                (session_id, role, content, tool_call_id, tool_calls, tool_name,
                 timestamp, token_count, finish_reason, reasoning, reasoning_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, role, content, tool_call_id or None,
                tool_calls or None, tool_name or None,
                msg_timestamp, token_count or 0,
                finish_reason or None, reasoning or None,
                reasoning_content or None
            ))
        
        total_messages += len(messages)
        total_sessions += 1
        
        if total_sessions % 10 == 0:
            conn.commit()
            print(f"  Progress: {total_sessions} sessions, {total_messages} messages...")
    
    conn.commit()
    
    # Verify
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sessions")
    s_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM messages")
    m_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM messages_fts")
    fts_count = cur.fetchone()[0]
    
    print(f"\n=== IMPORT RESULTS ===")
    print(f"Sessions imported: {s_count}")
    print(f"Messages imported: {m_count}")
    print(f"FTS5 entries: {fts_count}")
    print(f"Errors: {errors}")
    
    conn.close()
    
    # Rename to state.db
    final_path = '/home/alfdib/Hermes/hermes-data/state.db'
    if os.path.exists(final_path):
        os.rename(final_path, final_path + '.old')
    os.rename(DB_PATH, final_path)
    # Remove WAL/SHM from old DB
    for ext in ['-wal', '-shm']:
        old = final_path + '.old' + ext
        if os.path.exists(old):
            os.remove(old)
    print(f"\nNew database written to: {final_path}")
    db_size = os.path.getsize(final_path)
    old_size = os.path.getsize(final_path + '.old') if os.path.exists(final_path + '.old') else 0
    print(f"New DB size: {db_size} bytes (old: {old_size} bytes)")


if __name__ == '__main__':
    import_sessions()