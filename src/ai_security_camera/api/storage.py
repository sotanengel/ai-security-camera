"""SQLite persistence for events (requirements D-004)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_security_camera.api.schemas import EventCreate, EventOut, utc_now


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class EventStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn = _connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                template_id TEXT NOT NULL,
                detector_summary TEXT NOT NULL,
                vlm_json TEXT,
                media_uri TEXT
            );
            """,
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def session(self) -> Generator[sqlite3.Connection, None, None]:
        yield self._conn

    def create_event(self, body: EventCreate) -> EventOut:
        eid = str(uuid.uuid4())
        created = utc_now().isoformat()
        vlm_text: str | None
        if body.vlm is not None:
            vlm_text = json.dumps(body.vlm, ensure_ascii=False)
        else:
            vlm_text = None
        self._conn.execute(
            """
            INSERT INTO events (id, created_at, template_id, detector_summary, vlm_json, media_uri)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (eid, created, body.template_id, body.detector_summary, vlm_text, body.media_uri),
        )
        self._conn.commit()
        return self.get_event(eid)

    def get_event(self, eid: str) -> EventOut:
        cur = self._conn.execute(
            "SELECT * FROM events WHERE id = ?",
            (eid,),
        )
        row = cur.fetchone()
        if row is None:
            msg = "not found"
            raise KeyError(msg)
        return self._row_to_out(row)

    def list_events(self, limit: int = 50) -> list[EventOut]:
        cur = self._conn.execute(
            "SELECT * FROM events ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_out(r) for r in cur.fetchall()]

    def _row_to_out(self, row: sqlite3.Row) -> EventOut:
        raw = row["vlm_json"]
        vlm: dict[str, Any] | None
        if raw:
            vlm = json.loads(raw)
        else:
            vlm = None
        return EventOut(
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            template_id=row["template_id"],
            detector_summary=row["detector_summary"],
            vlm_json=vlm,
            media_uri=row["media_uri"],
        )
