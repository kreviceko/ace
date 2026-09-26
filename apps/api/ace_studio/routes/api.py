"""JSON API for the Quasar SPA."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ace_studio.ace_client import AceStepClient, AceStepError, build_create_fields
from ace_studio.config import get_settings
from ace_studio.library import Library

router = APIRouter(prefix="/api")


class FormatRequest(BaseModel):
    prompt: str = ""
    lyrics: str = ""
    duration: float | None = None
    language: str = "en"
    bpm: int | None = None
    key: str | None = None
    time_signature: str | None = None


@router.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    client = AceStepClient(settings)
    ace = await client.health()
    return {
        "ok": True,
        "ace": ace,
        "library_count": len(Library(settings).list(1000)),
        "acestep_api_url": settings.acestep_api_url,
    }


@router.get("/library")
async def list_library() -> list[dict[str, Any]]:
    items = Library().list(200)
    return [
        {
            "id": i.id,
            "created_at": i.created_at,
            "mode": i.mode,
            "title": i.title,
            "prompt": i.prompt,
            "lyrics": i.lyrics,
            "audio_path": i.audio_path,
            "metas": i.metas(),
            "task_id": i.task_id,
        }
        for i in items
    ]


@router.get("/library/{item_id}")
async def get_library_item(item_id: str) -> dict[str, Any]:
    item = Library().get(item_id)
    if not item:
        raise HTTPException(404, "Song not found")
    return {
        "id": item.id,
        "created_at": item.created_at,
        "mode": item.mode,
        "title": item.title,
        "prompt": item.prompt,
        "lyrics": item.lyrics,
        "audio_path": item.audio_path,
        "metas": item.metas(),
        "task_id": item.task_id,
    }


@router.get("/library/{item_id}/audio")
async def get_library_audio(item_id: str) -> FileResponse:
    item = Library().get(item_id)
    if not item:
        raise HTTPException(404, "Song not found")
    path = Path(item.audio_path)
    if not path.exists():
        raise HTTPException(404, "Audio file missing")
    media = "audio/mpeg"
    if path.suffix.lower() == ".wav":
        media = "audio/wav"
    elif path.suffix.lower() == ".flac":
        media = "audio/flac"
    return FileResponse(path, media_type=media, filename=path.name)


@router.post("/lyrics/format")
async def format_lyrics(body: FormatRequest) -> dict[str, Any]:
    client = AceStepClient()
    try:
        return await client.format_input(
            prompt=body.prompt,
            lyrics=body.lyrics,
            duration=body.duration,
            language=body.language,
            bpm=body.bpm,
            key=body.key,
            time_signature=body.time_signature,
        )
    except AceStepError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/create")
async def create_song(
    payload: str = Form(...),
    src_audio: UploadFile | None = File(None),
    reference_audio: UploadFile | None = File(None),
) -> dict[str, Any]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"Invalid payload JSON: {exc}") from exc

    mode = (data.get("mode") or "custom").lower()
    library = Library()
    src_path = await _store_upload(src_audio, library.uploads_dir(), "src")
    ref_path = await _store_upload(reference_audio, library.uploads_dir(), "ref")

    if mode in {"remix", "edit"} and src_path is None:
        raise HTTPException(400, "Remix and Edit require src_audio")

    fields = build_create_fields(
        mode,
        sample_query=data.get("sample_query") or "",
        prompt=data.get("prompt") or "",
        lyrics=data.get("lyrics") or "",
        instrumental=bool(data.get("instrumental")),
        thinking=bool(data.get("thinking")),
        use_format=bool(data.get("use_format")),
        duration=data.get("duration"),
        bpm=data.get("bpm"),
        key=data.get("key") or "",
        time_signature=data.get("time_signature") or "",
        vocal_language=data.get("vocal_language") or "en",
        audio_cover_strength=float(data.get("audio_cover_strength") or 1.0),
        cover_noise_strength=float(data.get("cover_noise_strength") or 0.0),
        repainting_start=float(data.get("repainting_start") or 0.0),
        repainting_end=data.get("repainting_end"),
        lm_negative_prompt=data.get("negative_styles") or "",
        batch_size=1,
    )

    client = AceStepClient()
    try:
        submitted = await client.release_task(
            fields,
            src_audio_path=src_path,
            reference_audio_path=ref_path,
        )
    except AceStepError as exc:
        raise HTTPException(502, str(exc)) from exc

    task_id = submitted.get("task_id")
    if not task_id:
        raise HTTPException(502, f"No task_id returned: {submitted}")

    # Stash request context for finalize on poll
    meta_path = library.root / "jobs"
    meta_path.mkdir(parents=True, exist_ok=True)
    (meta_path / f"{task_id}.json").write_text(
        json.dumps({"mode": mode, "fields": fields, "submitted": submitted}, indent=2),
        encoding="utf-8",
    )

    return {"task_id": task_id, "status": submitted.get("status", "queued")}


@router.get("/jobs/{task_id}")
async def get_job(task_id: str) -> dict[str, Any]:
    client = AceStepClient()
    library = Library()
    try:
        items = await client.query_result([task_id])
    except AceStepError as exc:
        raise HTTPException(502, str(exc)) from exc

    if not items:
        return {"task_id": task_id, "status": 0, "stage": "unknown"}

    parsed = client.parse_task_result(items[0])
    status = parsed["status"]
    if status != 1:
        stage = "failed" if status == 2 else "running"
        error = None
        if status == 2:
            results = parsed.get("results") or []
            error = parsed.get("error")
            if results and isinstance(results[0], dict):
                error = results[0].get("error") or error
        return {"task_id": task_id, "status": status, "stage": stage, "error": error}

    # Success: download + library insert if not already present
    existing = next((i for i in library.list(50) if i.task_id == task_id), None)
    if existing:
        return {
            "task_id": task_id,
            "status": 1,
            "stage": "done",
            "song": _item_dict(existing),
            "id": existing.id,
        }

    results = parsed.get("results") or []
    if not results:
        raise HTTPException(502, "Task succeeded without audio results")
    first = results[0]
    file_field = first.get("file")
    if not file_field:
        raise HTTPException(502, "Missing file in result")

    ext = "mp3"
    if ".wav" in str(file_field):
        ext = "wav"
    elif ".flac" in str(file_field):
        ext = "flac"
    dest = library.library_audio_dir() / f"{task_id}.{ext}"
    try:
        await client.download_audio(file_field, dest)
    except AceStepError as exc:
        raise HTTPException(502, str(exc)) from exc

    job_meta = {}
    meta_file = library.root / "jobs" / f"{task_id}.json"
    if meta_file.exists():
        try:
            job_meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            job_meta = {}

    mode = job_meta.get("mode") or "custom"
    metas = first.get("metas") if isinstance(first.get("metas"), dict) else {}
    item = library.add(
        mode=mode,
        prompt=first.get("prompt") or "",
        lyrics=first.get("lyrics") or "",
        audio_path=dest,
        task_id=task_id,
        metas=metas,
        raw={"result": first, "job_meta": job_meta},
    )
    return {
        "task_id": task_id,
        "status": 1,
        "stage": "done",
        "song": _item_dict(item),
        "id": item.id,
    }


def _item_dict(item) -> dict[str, Any]:
    return {
        "id": item.id,
        "created_at": item.created_at,
        "mode": item.mode,
        "title": item.title,
        "prompt": item.prompt,
        "lyrics": item.lyrics,
        "audio_path": item.audio_path,
        "metas": item.metas(),
        "task_id": item.task_id,
    }


async def _store_upload(upload: UploadFile | None, dest_dir: Path, prefix: str) -> Path | None:
    if upload is None or not upload.filename:
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{prefix}_{Path(upload.filename).name}"
    with dest.open("wb") as out:
        shutil.copyfileobj(upload.file, out)
    return dest
