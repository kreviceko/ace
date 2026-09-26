"""ZIP export packs for library songs."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from ace_studio.library import LibraryItem


def build_export_zip(item: LibraryItem, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    audio = Path(item.audio_path)
    if not audio.exists():
        raise FileNotFoundError(f"Audio missing: {audio}")

    safe_title = _safe_name(item.title) or item.id[:8]
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(audio, arcname=f"{safe_title}{audio.suffix.lower() or '.mp3'}")
        zf.writestr(
            f"{safe_title}.lyrics.txt",
            item.lyrics or "",
        )
        meta = {
            "id": item.id,
            "title": item.title,
            "mode": item.mode,
            "created_at": item.created_at,
            "prompt": item.prompt,
            "lyrics": item.lyrics,
            "task_id": item.task_id,
            "metas": item.metas(),
        }
        zf.writestr(f"{safe_title}.metadata.json", json.dumps(meta, indent=2))

        lrc = _lrc_from_item(item)
        if lrc:
            zf.writestr(f"{safe_title}.lrc", lrc)

    return dest


def _lrc_from_item(item: LibraryItem) -> str | None:
    try:
        raw = json.loads(item.raw_json or "{}")
    except json.JSONDecodeError:
        raw = {}
    result = raw.get("result") if isinstance(raw, dict) else None
    if isinstance(result, dict):
        for key in ("lrc", "lyrics_lrc", "lrc_content"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip() + ("\n" if not val.endswith("\n") else "")
        metas = result.get("metas")
        if isinstance(metas, dict):
            val = metas.get("lrc")
            if isinstance(val, str) and val.strip():
                return val.strip() + "\n"
    # Minimal LRC fallback from plain lyrics (no timings)
    if item.lyrics.strip():
        lines = ["[00:00.00]"]
        for line in item.lyrics.splitlines():
            lines.append(line)
        return "\n".join(lines) + "\n"
    return None


def _safe_name(name: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in (name or "").strip())
    return "_".join(cleaned.split())[:80]
