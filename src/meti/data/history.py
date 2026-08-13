"""SQLite history storage for METI snapshots."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from meti.config import get_settings


def _get_db_path() -> Path:
    settings = get_settings()
    path = Path(settings.history.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    path = _get_db_path()
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                raw_index REAL NOT NULL,
                tension_score INTEGER NOT NULL,
                oil_change REAL,
                gold_change REAL,
                btc_change REAL,
                lmt_change REAL,
                details TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(ts)"
        )
        conn.commit()


def save_snapshot(
    raw_index: float,
    tension_score: int,
    asset_changes: dict[str, float] | None = None,
    details: str | None = None,
) -> None:
    """Persist one snapshot."""
    init_db()
    asset_changes = asset_changes or {}
    ts = datetime.now(timezone.utc).isoformat()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO snapshots
            (ts, raw_index, tension_score, oil_change, gold_change, btc_change, lmt_change, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                raw_index,
                tension_score,
                asset_changes.get("CL=F"),
                asset_changes.get("GC=F"),
                asset_changes.get("BTC-USD"),
                asset_changes.get("LMT"),
                details,
            ),
        )
        conn.commit()


def get_recent_snapshots(days: int = 30, limit: int = 500) -> list[dict[str, Any]]:
    """Return recent snapshots ordered by time ascending."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT ts, raw_index, tension_score, oil_change, gold_change, btc_change, lmt_change
            FROM snapshots
            WHERE ts >= ?
            ORDER BY ts ASC
            LIMIT ?
            """,
            (cutoff, limit),
        ).fetchall()

    return [dict(r) for r in rows]


def prune_old_snapshots(keep_days: int | None = None) -> int:
    """Delete snapshots older than keep_days. Returns number of deleted rows."""
    settings = get_settings()
    days = keep_days if keep_days is not None else settings.history.keep_days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with _connect() as conn:
        cur = conn.execute("DELETE FROM snapshots WHERE ts < ?", (cutoff,))
        conn.commit()
        return cur.rowcount
