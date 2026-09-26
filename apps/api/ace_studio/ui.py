"""Gradio Create UI mirroring AceMusic Simple / Custom / Remix / Edit."""

from __future__ import annotations

import shutil
import traceback
from pathlib import Path
from typing import Any

import gradio as gr

from ace_studio.ace_client import AceStepClient, AceStepError, build_create_fields
from ace_studio.config import get_settings
from ace_studio.library import Library


SECTION_TAGS = ["[Intro]", "[Verse]", "[Pre-Chorus]", "[Chorus]", "[Bridge]", "[Outro]", "[Instrumental]"]


def _save_upload(upload: Any, dest_dir: Path, prefix: str) -> Path | None:
    if upload is None:
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = Path(upload if isinstance(upload, (str, Path)) else getattr(upload, "name", upload))
    if not src.exists():
        return None
    dest = dest_dir / f"{prefix}_{src.name}"
    shutil.copy2(src, dest)
    return dest


async def _run_generation(
    mode: str,
    sample_query: str,
    prompt: str,
    lyrics: str,
    instrumental: bool,
    thinking: bool,
    use_format: bool,
    duration: float,
    bpm: float,
    key: str,
    time_signature: str,
    language: str,
    audio_cover_strength: float,
    cover_noise_strength: float,
    repaint_start: float,
    repaint_end: float,
    negative_styles: str,
    src_audio,
    ref_audio,
    progress=gr.Progress(),
) -> tuple[str | None, str, str]:
    client = AceStepClient()
    library = Library()
    progress(0.05, desc="Checking ACE-Step API...")

    health = await client.health()
    if not health.get("ok"):
        return None, "", f"ACE-Step API unreachable at {client.base_url}: {health.get('error')}"

    src_path = _save_upload(src_audio, library.uploads_dir(), "src")
    ref_path = _save_upload(ref_audio, library.uploads_dir(), "ref")

    if mode in {"remix", "edit"} and src_path is None:
        return None, "", "Remix and Edit require an uploaded source audio file."

    bpm_val = int(bpm) if bpm and bpm > 0 else None
    duration_val = float(duration) if duration and duration > 0 else None
    repaint_end_val = float(repaint_end) if repaint_end and repaint_end > 0 else -1.0

    fields = build_create_fields(
        mode,
        sample_query=sample_query.strip(),
        prompt=prompt.strip(),
        lyrics="" if instrumental else lyrics,
        instrumental=instrumental,
        thinking=thinking,
        use_format=use_format,
        duration=duration_val,
        bpm=bpm_val,
        key=key.strip(),
        time_signature=time_signature.strip(),
        vocal_language=language.strip() or "en",
        audio_cover_strength=audio_cover_strength,
        cover_noise_strength=cover_noise_strength,
        repainting_start=repaint_start,
        repainting_end=repaint_end_val,
        lm_negative_prompt=negative_styles.strip(),
        batch_size=1,
    )

    progress(0.15, desc="Submitting generation task...")
    try:
        submitted = await client.release_task(
            fields,
            src_audio_path=src_path,
            reference_audio_path=ref_path,
        )
        task_id = submitted.get("task_id")
        if not task_id:
            return None, "", f"No task_id returned: {submitted}"

        progress(0.3, desc=f"Generating (task {task_id[:8]}...) - first run may download models")
        finished = await client.wait_for_task(task_id)
        results = finished.get("results") or []
        if not results:
            return None, "", f"Task succeeded but returned no audio: {finished}"

        first = results[0]
        file_field = first.get("file")
        if not file_field:
            return None, "", f"Missing file in result: {first}"

        progress(0.85, desc="Downloading audio...")
        ext = "mp3"
        if ".wav" in str(file_field):
            ext = "wav"
        elif ".flac" in str(file_field):
            ext = "flac"
        dest = library.library_audio_dir() / f"{task_id}.{ext}"
        await client.download_audio(file_field, dest)

        metas = first.get("metas") or {}
        used_prompt = first.get("prompt") or prompt or sample_query
        used_lyrics = first.get("lyrics") or ("" if instrumental else lyrics)
        item = library.add(
            mode=mode,
            prompt=used_prompt,
            lyrics=used_lyrics,
            audio_path=dest,
            task_id=task_id,
            metas=metas if isinstance(metas, dict) else {},
            raw={"submission": submitted, "result": first, "fields": fields},
        )

        info = (
            f"**Saved:** {item.title}\n\n"
            f"- Mode: `{mode}`\n"
            f"- Task: `{task_id}`\n"
            f"- File: `{dest}`\n"
            f"- BPM: `{metas.get('bpm', '-')}` · Key: `{metas.get('keyscale', metas.get('key_scale', '-'))}`\n"
            f"- Duration: `{metas.get('duration', '-')}`"
        )
        progress(1.0, desc="Done")
        return str(dest), used_lyrics, info
    except AceStepError as exc:
        return None, lyrics, f"ACE-Step error: {exc}"
    except Exception as exc:  # noqa: BLE001
        return None, lyrics, f"Unexpected error: {exc}\n\n```\n{traceback.format_exc()[-2000:]}\n```"


async def _format_lyrics(prompt: str, lyrics: str, duration: float, language: str) -> tuple[str, str, str]:
    client = AceStepClient()
    health = await client.health()
    if not health.get("ok"):
        return prompt, lyrics, f"ACE-Step API unreachable: {health.get('error')}"
    try:
        data = await client.format_input(
            prompt=prompt,
            lyrics=lyrics,
            duration=duration if duration and duration > 0 else None,
            language=language or "en",
        )
        new_prompt = data.get("caption") or data.get("prompt") or prompt
        new_lyrics = data.get("lyrics") or lyrics
        meta_bits = []
        for key in ("bpm", "key_scale", "time_signature", "duration", "vocal_language"):
            if data.get(key) not in (None, ""):
                meta_bits.append(f"{key}={data.get(key)}")
        note = "Formatted via ACE `/format_input`."
        if meta_bits:
            note += " " + ", ".join(meta_bits)
        return new_prompt, new_lyrics, note
    except AceStepError as exc:
        return prompt, lyrics, f"Format failed: {exc}"


async def _health_markdown() -> str:
    client = AceStepClient()
    settings = get_settings()
    health = await client.health()
    if not health.get("ok"):
        return (
            f"### Engine status\n"
            f"**Down** — cannot reach `{settings.acestep_api_url}`\n\n"
            f"`{health.get('error')}`\n\n"
            f"Start ACE-Step with `scripts/start.ps1` or "
            f"`uv run acestep-api` inside `{settings.acestep_path}`."
        )
    models_note = ""
    try:
        models = await client.list_models()
        default = models.get("default_model")
        names = [m.get("name") if isinstance(m, dict) else str(m) for m in models.get("models", [])]
        models_note = f"\n- Default model: `{default}`\n- Loaded: {', '.join(f'`{n}`' for n in names) or '—'}"
    except Exception:  # noqa: BLE001
        models_note = "\n- Models: (could not list)"
    return f"### Engine status\n**OK** — `{settings.acestep_api_url}`{models_note}"


def _library_table() -> list[list[str]]:
    items = Library().list(50)
    rows = []
    for item in items:
        rows.append([item.created_at[:19], item.mode, item.title, item.audio_path, item.id])
    return rows


def build_ui() -> gr.Blocks:
    settings = get_settings()

    with gr.Blocks(title="ACE Studio") as demo:
        gr.Markdown(
            """
# ACE Studio
Local Create UI for **ACE-Step 1.5** — AceMusic-style **Simple / Custom / Remix / Edit**.
"""
        )
        status_md = gr.Markdown("Checking engine…")
        refresh_status = gr.Button("Refresh engine status", size="sm")

        with gr.Tabs():
            with gr.Tab("Create"):
                mode = gr.Radio(
                    choices=["simple", "custom", "remix", "edit"],
                    value="custom",
                    label="Mode",
                    info="Matches AceMusic Create: Simple · Custom · Remix · Edit",
                )

                with gr.Row():
                    with gr.Column(scale=3):
                        sample_query = gr.Textbox(
                            label="Simple description",
                            placeholder="a soft indie love song for a rainy evening",
                            lines=2,
                            visible=False,
                        )
                        prompt = gr.Textbox(
                            label="Styles / caption",
                            placeholder="Describe the styles of the song...",
                            lines=3,
                        )
                        lyrics = gr.Textbox(
                            label="Lyrics",
                            placeholder="Write lyrics for the song, or leave blank for instrumental...",
                            lines=12,
                        )
                        tag_dd = gr.Dropdown(
                            choices=SECTION_TAGS,
                            label="Insert structure tag",
                            value=None,
                            allow_custom_value=False,
                        )

                        def _insert_tag(current: str, tag: str | None) -> str:
                            if not tag:
                                return current or ""
                            base = current or ""
                            sep = "" if base.endswith("\n") or not base else "\n"
                            return f"{base}{sep}{tag}\n"

                        tag_dd.change(_insert_tag, inputs=[lyrics, tag_dd], outputs=[lyrics])
                        with gr.Row():
                            instrumental = gr.Checkbox(label="Instrumental", value=False)
                            thinking = gr.Checkbox(
                                label="Thinking (LM planner)",
                                value=False,
                                info="Needs ACESTEP_INIT_LLM=true and free system RAM for the 5Hz LM",
                            )
                            use_format = gr.Checkbox(label="Format with LM", value=False)
                        negative_styles = gr.Textbox(label="Negative styles", placeholder="Negative Styles")

                    with gr.Column(scale=2):
                        duration = gr.Slider(0, 600, value=120, step=5, label="Duration (sec, 0=auto)")
                        bpm = gr.Number(label="BPM (0=auto)", value=0, precision=0)
                        key = gr.Textbox(label="Key", placeholder="e.g. C Major / Am")
                        time_signature = gr.Dropdown(
                            choices=["", "2", "3", "4", "6"],
                            value="",
                            label="Time signature",
                        )
                        language = gr.Textbox(label="Vocal language", value="en")
                        src_audio = gr.Audio(
                            label="Source audio (Remix / Edit)",
                            type="filepath",
                            visible=True,
                        )
                        ref_audio = gr.Audio(
                            label="Reference audio (Custom, optional)",
                            type="filepath",
                        )
                        audio_cover_strength = gr.Slider(
                            0.0, 1.0, value=1.0, step=0.05, label="Cover Strength (Remix)"
                        )
                        cover_noise_strength = gr.Slider(
                            0.0, 1.0, value=0.0, step=0.05, label="Remix Strength (noise)"
                        )
                        repaint_start = gr.Number(label="Edit start (sec)", value=0)
                        repaint_end = gr.Number(label="Edit end (sec, 0=end)", value=0)

                with gr.Row():
                    format_btn = gr.Button("Format lyrics / caption")
                    generate_btn = gr.Button("Generate", variant="primary")

                audio_out = gr.Audio(label="Result", type="filepath")
                lyrics_out = gr.Textbox(label="Lyrics used", lines=8)
                info_out = gr.Markdown()

            with gr.Tab("Library"):
                lib_refresh = gr.Button("Refresh library")
                lib_table = gr.Dataframe(
                    headers=["created", "mode", "title", "path", "id"],
                    datatype=["str", "str", "str", "str", "str"],
                    interactive=False,
                    wrap=True,
                )
                gr.Markdown("Audio files live under `data/library/`. Use Create → Generate to add songs.")

            with gr.Tab("Settings"):
                gr.Markdown(
                    f"""
### Config
- App: `http://{settings.app_host}:{settings.app_port}`
- ACE-Step API: `{settings.acestep_api_url}`
- ACE-Step path: `{settings.acestep_path}`
- Data: `{settings.data_dir}`

Optional lyric assist (SpaceXAI) uses `XAI_API_KEY` in the repo `.env` (not required for Create).
"""
                )

        def _mode_visibility(selected: str):
            is_simple = selected == "simple"
            needs_src = selected in {"remix", "edit"}
            is_remix = selected == "remix"
            is_edit = selected == "edit"
            return (
                gr.update(visible=is_simple),
                gr.update(visible=not is_simple, label="Styles / caption" if selected != "simple" else "Styles"),
                gr.update(visible=needs_src),
                gr.update(visible=selected == "custom"),
                gr.update(visible=is_remix),
                gr.update(visible=is_remix),
                gr.update(visible=is_edit),
                gr.update(visible=is_edit),
                gr.update(visible=selected in {"custom", "simple"}),
            )

        mode.change(
            _mode_visibility,
            inputs=[mode],
            outputs=[
                sample_query,
                prompt,
                src_audio,
                ref_audio,
                audio_cover_strength,
                cover_noise_strength,
                repaint_start,
                repaint_end,
                thinking,
            ],
        )

        generate_btn.click(
            _run_generation,
            inputs=[
                mode,
                sample_query,
                prompt,
                lyrics,
                instrumental,
                thinking,
                use_format,
                duration,
                bpm,
                key,
                time_signature,
                language,
                audio_cover_strength,
                cover_noise_strength,
                repaint_start,
                repaint_end,
                negative_styles,
                src_audio,
                ref_audio,
            ],
            outputs=[audio_out, lyrics_out, info_out],
        )

        format_btn.click(
            _format_lyrics,
            inputs=[prompt, lyrics, duration, language],
            outputs=[prompt, lyrics, info_out],
        )

        refresh_status.click(_health_markdown, outputs=[status_md])
        demo.load(_health_markdown, outputs=[status_md])
        lib_refresh.click(_library_table, outputs=[lib_table])
        demo.load(_library_table, outputs=[lib_table])

    return demo
