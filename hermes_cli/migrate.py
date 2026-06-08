"""CLI handlers for ``hermes migrate ...``."""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from hermes_cli.colors import Colors, color
from hermes_cli.config import get_hermes_home, load_config, save_config


def cmd_migrate(args: Any) -> int:
    """Dispatcher for ``hermes migrate <subtype>``."""
    sub = getattr(args, "migrate_type", None)
    if sub == "xai":
        return cmd_migrate_xai(args)
    if sub == "state-postgres":
        return cmd_migrate_state_postgres(args)

    print(
        "usage: hermes migrate {xai,state-postgres} ...",
        file=sys.stderr,
    )
    return 2


def cmd_migrate_state_postgres(args: Any) -> int:
    """Copy SQLite session state into a PostgreSQL state backend."""
    from hermes_state import SessionDB, StateDatabaseConfig

    apply = bool(getattr(args, "apply", False))
    replace = bool(getattr(args, "replace", False))
    update_config = bool(getattr(args, "update_config", False))
    include_inactive = not bool(getattr(args, "active_only", False))
    sqlite_path = Path(getattr(args, "sqlite_path", None) or get_hermes_home() / "state.db").expanduser()
    dsn = getattr(args, "dsn", None)
    dsn_env = getattr(args, "dsn_env", None) or "HERMES_STATE_DATABASE_URL"

    if not dsn:
        import os
        dsn = os.environ.get(dsn_env)
    if not dsn:
        print(
            f"  {color('✗', Colors.RED)} PostgreSQL DSN required via --dsn or {dsn_env}",
            file=sys.stderr,
        )
        return 2
    if not sqlite_path.exists():
        print(
            f"  {color('✗', Colors.RED)} SQLite state DB not found: {sqlite_path}",
            file=sys.stderr,
        )
        return 1

    print()
    print(color("◆ State DB PostgreSQL Migration", Colors.CYAN, Colors.BOLD))
    print()
    print(f"  Source: {sqlite_path}")
    print(f"  Target: PostgreSQL ({_redact_dsn(dsn)})")
    print(f"  Mode: {'apply' if apply else 'dry-run'}")
    print()

    source_db = SessionDB(sqlite_path)
    session_count = _source_session_count(source_db, include_inactive=include_inactive)
    message_count = _source_message_count(source_db, include_inactive=include_inactive)
    print(f"  {color('✓', Colors.GREEN)} Source sessions: {session_count}")
    print(f"  {color('✓', Colors.GREEN)} Source messages: {message_count}")

    if not apply:
        source_db.close()
        print()
        print(color("Dry-run mode — no target writes or config changes.", Colors.DIM))
        print(color(
            "Re-run with `hermes migrate state-postgres --apply --dsn ...` "
            "to import into PostgreSQL.",
            Colors.DIM,
        ))
        return 0

    backup_path = None
    if not bool(getattr(args, "no_backup", False)):
        backup_path = _backup_sqlite_state(sqlite_path)
        print(f"  {color('✓', Colors.GREEN)} SQLite backup: {backup_path}")

    target_db = SessionDB(
        database_config=StateDatabaseConfig(
            backend="postgres",
            db_path=Path("state.db"),
            database_url=dsn,
        )
    )
    try:
        existing = _table_count(target_db, "sessions")
        if existing and not replace:
            print(
                f"  {color('✗', Colors.RED)} Target already has {existing} session(s); "
                "pass --replace to clear session/message rows first.",
                file=sys.stderr,
            )
            return 1
        if existing and replace:
            _clear_postgres_sessions(target_db)
            print(f"  {color('✓', Colors.GREEN)} Cleared existing target sessions/messages")

        imported = 0
        for session in _iter_source_sessions(source_db, include_inactive=include_inactive):
            target_db.import_session(session)
            imported += 1
        target_messages = _table_count(target_db, "messages")
        if imported != session_count or target_messages < message_count:
            raise RuntimeError(
                f"verification failed: imported={imported}/{session_count}, "
                f"target_messages={target_messages}/{message_count}"
            )
        print(f"  {color('✓', Colors.GREEN)} Imported sessions: {imported}")
        print(f"  {color('✓', Colors.GREEN)} Target messages: {target_messages}")
    except Exception as exc:
        print(f"  {color('✗', Colors.RED)} Migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        target_db.close()
        source_db.close()

    if update_config:
        config = load_config()
        sessions_cfg = config.setdefault("sessions", {})
        sessions_cfg["state_backend"] = "postgres"
        sessions_cfg["postgres_dsn"] = f"${{{dsn_env}}}"
        save_config(config)
        print(f"  {color('✓', Colors.GREEN)} Updated config to use PostgreSQL state backend")
        if getattr(args, "dsn", None):
            print(color(
                f"Set {dsn_env} in your shell or .env before restarting Hermes; "
                "the DSN was not written to config.yaml.",
                Colors.DIM,
            ))
    else:
        print()
        print(color(
            "Config not changed. Set sessions.state_backend=postgres and "
            "sessions.postgres_dsn (or re-run with --update-config) after reviewing the import.",
            Colors.DIM,
        ))

    print()
    print(color("Restart Hermes processes so they open the PostgreSQL backend.", Colors.DIM))
    return 0


def _table_count(db: Any, table: str) -> int:
    if table not in {"sessions", "messages"}:
        raise ValueError(f"unsupported table for migration count: {table}")
    sql = {
        "sessions": "SELECT COUNT(*) AS count FROM sessions",
        "messages": "SELECT COUNT(*) AS count FROM messages",
    }[table]
    row = db._conn.execute(sql).fetchone()
    return int(row["count"])


def _source_session_count(db: Any, *, include_inactive: bool) -> int:
    row = db._conn.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()
    return int(row["count"])


def _source_message_count(db: Any, *, include_inactive: bool) -> int:
    active_clause = "" if include_inactive else "m.active = 1"
    where = f" WHERE {active_clause}" if active_clause else ""
    row = db._conn.execute(
        "SELECT COUNT(*) AS count FROM messages m "
        "JOIN sessions s ON s.id = m.session_id"
        f"{where}"
    ).fetchone()
    return int(row["count"])


def _iter_source_sessions(db: Any, *, include_inactive: bool):
    """Yield exported sessions one at a time, with parents before children."""
    query = f"""
        WITH RECURSIVE ordered(id, depth) AS (
            SELECT s.id, 0
            FROM sessions s
            WHERE s.parent_session_id IS NULL
               OR s.parent_session_id NOT IN (SELECT id FROM sessions)
            UNION ALL
            SELECT child.id, ordered.depth + 1
            FROM sessions child
            JOIN ordered ON child.parent_session_id = ordered.id
        )
        SELECT s.*
        FROM sessions s
        JOIN ordered ON ordered.id = s.id
        ORDER BY ordered.depth, s.started_at, s.id
    """
    rows = db._conn.execute(query).fetchall()
    exported_ids = {row["id"] for row in rows}
    for row in rows:
        session = dict(row)
        if session.get("parent_session_id") not in exported_ids:
            session["parent_session_id"] = None
        session["messages"] = db.get_messages(session["id"], include_inactive=include_inactive)
        yield session


def _clear_postgres_sessions(db: Any) -> None:
    def _do(conn: Any) -> None:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM sessions")
        conn.execute(
            "SELECT setval(pg_get_serial_sequence('messages', 'id'), 1, false)"
        )
    db._execute_write(_do)


def _backup_sqlite_state(sqlite_path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = sqlite_path.with_name(f"{sqlite_path.name}.bak-pre-postgres-{ts}")
    shutil.copy2(sqlite_path, backup_path)
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{sqlite_path}{suffix}")
        if sidecar.exists():
            shutil.copy2(sidecar, Path(f"{backup_path}{suffix}"))
    return backup_path


def _redact_dsn(dsn: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    sensitive_keys = {"password", "passfile", "sslpassword"}

    def _redact_keyword_dsn(value: str) -> str:
        parts: list[str] = []
        i = 0
        length = len(value)
        while i < length:
            if value[i].isspace():
                start = i
                while i < length and value[i].isspace():
                    i += 1
                parts.append(value[start:i])
                continue

            token_start = i
            while i < length and not value[i].isspace() and value[i] != "=":
                i += 1
            key = value[token_start:i]
            while i < length and value[i].isspace():
                i += 1
            if i >= length or value[i] != "=":
                parts.append(value[token_start:i])
                continue
            i += 1
            while i < length and value[i].isspace():
                i += 1
            value_start = i
            if i < length and value[i] in {"'", '"'}:
                quote = value[i]
                i += 1
                while i < length:
                    if value[i] == "\\" and i + 1 < length:
                        i += 2
                    elif value[i] == quote:
                        i += 1
                        break
                    else:
                        i += 1
            else:
                while i < length and not value[i].isspace():
                    i += 1

            if key.lower() in sensitive_keys:
                parts.append(f"{value[token_start:value_start]}***")
            else:
                parts.append(value[token_start:i])
        return "".join(parts)

    try:
        parsed = urlsplit(dsn)
        if parsed.scheme and parsed.netloc:
            netloc = parsed.netloc
            if "@" in netloc:
                userinfo, host = netloc.rsplit("@", 1)
                user = userinfo.split(":", 1)[0]
                netloc = f"{user}:***@{host}"
            query = urlencode(
                [
                    (key, "***" if key.lower() in sensitive_keys else value)
                    for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                ],
                doseq=True,
            )
            return urlunsplit((parsed.scheme, netloc, parsed.path, query, parsed.fragment))
        return _redact_keyword_dsn(dsn)
    except Exception:
        return "<redacted>"


def cmd_migrate_xai(args: Any) -> int:
    """Run xAI May-15 model migration in dry-run or apply mode."""
    from hermes_cli.xai_retirement import (
        MIGRATION_GUIDE_URL,
        RETIREMENT_DATE,
        apply_migration,
        find_retired_xai_refs,
        format_issue,
    )

    apply = bool(getattr(args, "apply", False))
    no_backup = bool(getattr(args, "no_backup", False))

    config = load_config()
    issues = find_retired_xai_refs(config)

    print()
    print(color(
        f"◆ xAI Model Retirement Migration ({RETIREMENT_DATE})",
        Colors.CYAN, Colors.BOLD,
    ))
    print()

    if not issues:
        print(f"  {color('✓', Colors.GREEN)} No retired xAI models in config — nothing to migrate.")
        return 0

    print(f"  Found {len(issues)} retired xAI model reference(s):")
    print()
    for issue in issues:
        print(f"    {color('⚠', Colors.YELLOW)} {format_issue(issue)}")
    print()
    print(f"    {color('→', Colors.CYAN)} Migration guide: {MIGRATION_GUIDE_URL}")
    print()

    config_path = _resolve_config_path()

    if not apply:
        print(color("Dry-run mode — no changes written.", Colors.DIM))
        print(color(
            "Re-run with `hermes migrate xai --apply` to rewrite "
            f"{config_path} in-place (backup created automatically).",
            Colors.DIM,
        ))
        return 0

    if not config_path or not config_path.exists():
        print(
            f"  {color('✗', Colors.RED)} Could not locate config.yaml "
            f"(looked at: {config_path})",
            file=sys.stderr,
        )
        return 1

    try:
        result = apply_migration(
            config_path=config_path,
            issues=issues,
            backup=not no_backup,
        )
    except Exception as exc:
        print(
            f"  {color('✗', Colors.RED)} Migration failed: {exc}",
            file=sys.stderr,
        )
        return 1

    if not result.config_changed:
        print(f"  {color('⚠', Colors.YELLOW)} No changes written.")
        return 0

    if result.backup_path is not None:
        print(f"  {color('✓', Colors.GREEN)} Backup: {result.backup_path}")
    print(
        f"  {color('✓', Colors.GREEN)} Updated {len(result.issues_resolved)} "
        f"slot(s) in {result.file_path}"
    )
    print()
    print(color(
        "Run `hermes doctor` to confirm no retired xAI models remain.",
        Colors.DIM,
    ))
    return 0


def _resolve_config_path() -> Path:
    """Best-effort: locate the active config.yaml on disk."""
    from hermes_cli.config import get_hermes_home

    return get_hermes_home() / "config.yaml"
