"""Thin async client for the official ACE-Step REST API."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from ace_studio.config import Settings, get_settings


class AceStepError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AceStepClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.acestep_api_url.rstrip("/")

    def _unwrap(self, body: dict[str, Any]) -> Any:
        if isinstance(body, dict) and "code" in body:
            if body.get("code") != 200:
                raise AceStepError(
                    body.get("error") or body.get("detail") or "ACE-Step API error",
                    status_code=body.get("code"),
                    payload=body,
                )
            return body.get("data")
        return body

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/health")
                resp.raise_for_status()
                return {"ok": True, "data": self._unwrap(resp.json())}
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": str(exc)}

    async def list_models(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/v1/models")
            resp.raise_for_status()
            data = self._unwrap(resp.json())
            return data if isinstance(data, dict) else {"models": data}

    async def format_input(
        self,
        *,
        prompt: str = "",
        lyrics: str = "",
        duration: float | None = None,
        bpm: int | None = None,
        key: str | None = None,
        time_signature: str | None = None,
        language: str = "en",
        temperature: float = 0.85,
    ) -> dict[str, Any]:
        param_obj: dict[str, Any] = {"language": language}
        if duration is not None:
            param_obj["duration"] = duration
        if bpm is not None:
            param_obj["bpm"] = bpm
        if key:
            param_obj["key"] = key
        if time_signature:
            param_obj["time_signature"] = time_signature

        payload = {
            "prompt": prompt,
            "lyrics": lyrics,
            "temperature": temperature,
            "param_obj": json.dumps(param_obj),
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(f"{self.base_url}/format_input", json=payload)
            if resp.status_code >= 400:
                raise AceStepError(resp.text, status_code=resp.status_code)
            return self._unwrap(resp.json()) or {}

    async def release_task(
        self,
        fields: dict[str, Any],
        *,
        src_audio_path: Path | None = None,
        reference_audio_path: Path | None = None,
    ) -> dict[str, Any]:
        """Submit a generation task. Uses multipart when audio files are present."""
        clean = {k: v for k, v in fields.items() if v is not None and v != ""}

        files: list[tuple[str, Any]] = []
        data: dict[str, str] = {}
        for key, value in clean.items():
            if isinstance(value, bool):
                data[key] = "true" if value else "false"
            elif isinstance(value, (dict, list)):
                data[key] = json.dumps(value)
            else:
                data[key] = str(value)

        open_handles: list[Any] = []
        try:
            if src_audio_path and src_audio_path.exists():
                handle = src_audio_path.open("rb")
                open_handles.append(handle)
                files.append(("src_audio", (src_audio_path.name, handle, "application/octet-stream")))
            if reference_audio_path and reference_audio_path.exists():
                handle = reference_audio_path.open("rb")
                open_handles.append(handle)
                files.append(
                    ("reference_audio", (reference_audio_path.name, handle, "application/octet-stream"))
                )

            async with httpx.AsyncClient(timeout=120.0) as client:
                if files:
                    resp = await client.post(f"{self.base_url}/release_task", data=data, files=files)
                else:
                    # Prefer JSON for text-only tasks
                    json_body = {k: clean[k] for k in clean}
                    resp = await client.post(f"{self.base_url}/release_task", json=json_body)

            if resp.status_code >= 400:
                raise AceStepError(resp.text, status_code=resp.status_code)
            data_out = self._unwrap(resp.json())
            return data_out if isinstance(data_out, dict) else {"raw": data_out}
        finally:
            for handle in open_handles:
                handle.close()

    async def query_result(self, task_ids: list[str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/query_result",
                json={"task_id_list": task_ids},
            )
            if resp.status_code >= 400:
                raise AceStepError(resp.text, status_code=resp.status_code)
            data = self._unwrap(resp.json())
            if isinstance(data, list):
                return data
            return []

    def parse_task_result(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a /query_result item into status + parsed result list."""
        status = item.get("status")
        raw = item.get("result")
        results: list[dict[str, Any]] = []
        if isinstance(raw, str) and raw.strip():
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    results = parsed
                elif isinstance(parsed, dict):
                    results = [parsed]
            except json.JSONDecodeError:
                results = []
        elif isinstance(raw, list):
            results = raw
        elif isinstance(raw, dict):
            results = [raw]
        return {
            "task_id": item.get("task_id"),
            "status": status,
            "results": results,
            "error": item.get("error") or item.get("message"),
        }

    async def wait_for_task(self, task_id: str) -> dict[str, Any]:
        deadline = asyncio.get_event_loop().time() + self.settings.poll_timeout_sec
        while True:
            items = await self.query_result([task_id])
            if not items:
                if asyncio.get_event_loop().time() > deadline:
                    raise AceStepError(f"Timed out waiting for task {task_id}")
                await asyncio.sleep(self.settings.poll_interval_sec)
                continue

            parsed = self.parse_task_result(items[0])
            status = parsed["status"]
            if status == 1:
                return parsed
            if status == 2:
                raise AceStepError(parsed.get("error") or f"Generation failed for {task_id}", payload=parsed)
            if asyncio.get_event_loop().time() > deadline:
                raise AceStepError(f"Timed out waiting for task {task_id}")
            await asyncio.sleep(self.settings.poll_interval_sec)

    async def download_audio(self, file_field: str, dest: Path) -> Path:
        """Download audio given a result `file` URL or path query."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        if file_field.startswith("http://") or file_field.startswith("https://"):
            url = file_field
        elif file_field.startswith("/"):
            url = f"{self.base_url}{file_field}"
        else:
            url = f"{self.base_url}/v1/audio?path={file_field}"

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                raise AceStepError(f"Failed to download audio: {resp.status_code} {resp.text[:200]}")
            dest.write_bytes(resp.content)
        return dest


def build_create_fields(
    mode: str,
    *,
    sample_query: str = "",
    prompt: str = "",
    lyrics: str = "",
    instrumental: bool = False,
    thinking: bool = True,
    use_format: bool = False,
    duration: float | None = None,
    bpm: int | None = None,
    key: str = "",
    time_signature: str = "",
    vocal_language: str = "en",
    audio_format: str = "mp3",
    audio_cover_strength: float = 1.0,
    cover_noise_strength: float = 0.0,
    repainting_start: float = 0.0,
    repainting_end: float | None = None,
    lm_negative_prompt: str = "",
    batch_size: int = 1,
    seed: int | None = None,
) -> dict[str, Any]:
    """Map AceMusic Create modes onto ACE-Step release_task fields."""
    mode = (mode or "custom").lower()
    fields: dict[str, Any] = {
        "audio_format": audio_format,
        "vocal_language": vocal_language,
        "batch_size": max(1, min(8, int(batch_size or 1))),
    }

    if duration is not None and duration > 0:
        fields["audio_duration"] = float(duration)
    if bpm:
        fields["bpm"] = int(bpm)
    if key:
        fields["key_scale"] = key
    if time_signature:
        fields["time_signature"] = time_signature
    if lm_negative_prompt:
        fields["lm_negative_prompt"] = lm_negative_prompt
    if seed is not None and seed >= 0:
        fields["use_random_seed"] = False
        fields["seed"] = int(seed)
    else:
        fields["use_random_seed"] = True

    if instrumental:
        # Empty lyrics + instrumental flag when supported; also clear lyrics.
        fields["lyrics"] = ""
        fields["instrumental"] = True
    else:
        if lyrics:
            fields["lyrics"] = lyrics

    if mode == "simple":
        fields["sample_mode"] = True
        fields["sample_query"] = sample_query or prompt
        fields["thinking"] = True
        fields["task_type"] = "text2music"
    elif mode == "remix":
        fields["task_type"] = "cover"
        fields["prompt"] = prompt or sample_query
        fields["audio_cover_strength"] = float(audio_cover_strength)
        fields["cover_noise_strength"] = float(cover_noise_strength)
        fields["thinking"] = False
    elif mode == "edit":
        fields["task_type"] = "repaint"
        fields["prompt"] = prompt or sample_query
        fields["repainting_start"] = float(repainting_start)
        if repainting_end is not None:
            fields["repainting_end"] = float(repainting_end)
        fields["chunk_mask_mode"] = "explicit"
        fields["thinking"] = False
    else:  # custom
        fields["task_type"] = "text2music"
        fields["prompt"] = prompt
        fields["thinking"] = bool(thinking)
        fields["use_format"] = bool(use_format)
        if sample_query and not prompt:
            fields["sample_query"] = sample_query
            fields["sample_mode"] = True

    return fields
