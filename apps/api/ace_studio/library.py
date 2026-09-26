"""SQLite-backed local library for generated songs."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ace_studio.config import Settings, ensure_data_dirs, get_settings


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LibraryItem:
    id: str
    created_at: str
    mode: str
    title: str
    prompt: str
    lyrics: str
    audio_path: str
    metas_json: str
    raw_json: str
    task_id: str

    def metas(self) -> dict[str, Any]:
        try:
            return json.loads(self.metas_json or "{}")
        except json.JSONDecodeError:
            return {}


class Library:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.root = ensure_data_dirs(self.settings)
        self.db_path = self.root / "library.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS songs (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    title TEXT NOT NULL,
                    prompt TEXT NOT NULL DEFAULT '',
                    lyrics TEXT NOT NULL DEFAULT '',
                    audio_path TEXT NOT NULL,
                    metas_json TEXT NOT NULL DEFAULT '{}',
                    raw_json TEXT NOT NULL DEFAULT '{}',
                    task_id TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.commit()

    def add(
        self,
        *,
        mode: str,
        prompt: str,
        lyrics: str,
        audio_path: Path,
        task_id: str = "",
        metas: dict[str, Any] | None = None,
        raw: dict[str, Any] | None = None,
        title: str | None = None,
    ) -> LibraryItem:
        item_id = uuid.uuid4().hex
        created = _utc_now()
        title = title or (prompt.strip().split("\n")[0][:80] if prompt.strip() else f"Song {item_id[:8]}")
        item = LibraryItem(
            id=item_id,
            created_at=created,
            mode=mode,
            title=title,
            prompt=prompt or "",
            lyrics=lyrics or "",
            audio_path=str(audio_path),
            metas_json=json.dumps(metas or {}),
            raw_json=json.dumps(raw or {}),
            task_id=task_id or "",
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO songs (
                    id, created_at, mode, title, prompt, lyrics,
                    audio_path, metas_json, raw_json, task_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.created_at,
                    item.mode,
                    item.title,
                    item.prompt,
                    item.lyrics,
                    item.audio_path,
                    item.metas_json,
                    item.raw_json,
                    item.task_id,
                ),
            )
            conn.commit()
        return item

    def list(self, limit: int = 100) -> list[LibraryItem]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM songs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def get(self, item_id: str) -> LibraryItem | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM songs WHERE id = ?", (item_id,)).fetchone()
        return self._row_to_item(row) if row else None

    def _row_to_item(self, row: sqlite3.Row) -> LibraryItem:
        return LibraryItem(
            id=row["id"],
            created_at=row["created_at"],
            mode=row["mode"],
            title=row["title"],
            prompt=row["prompt"],
            lyrics=row["lyrics"],
            audio_path=row["audio_path"],
            metas_json=row["metas_json"],
            raw_json=row["raw_json"],
            task_id=row["task_id"],
        )

    def library_audio_dir(self) -> Path:
        return self.root / "library"

    def uploads_dir(self) -> Path:
        return self.root / "uploads"
