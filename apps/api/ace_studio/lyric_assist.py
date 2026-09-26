"""SpaceXAI (xAI) lyric writing assist — server-side only."""

from __future__ import annotations

from typing import Any, Literal

from openai import OpenAI

from ace_studio.config import Settings, get_settings

AssistAction = Literal["rhyme", "rewrite_line", "continue_verse", "suggest_hooks", "polish"]


SYSTEM = """You are a professional songwriter assisting with ACE-Step music generation.
Prefer clear, singable lines. Use section tags like [Verse], [Chorus], [Bridge] when returning full sections.
Keep language matching the user's lyrics. Do not add commentary outside the requested format."""


def assist_available(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return bool(settings.xai_api_key.strip())


def run_assist(
    *,
    action: AssistAction,
    lyrics: str = "",
    concept: str = "",
    line: str = "",
    style: str = "",
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    if not settings.xai_api_key.strip():
        raise RuntimeError(
            "SpaceXAI lyric assist needs XAI_API_KEY in the repo .env (server-side)."
        )

    prompt = _build_prompt(action, lyrics=lyrics, concept=concept, line=line, style=style)
    client = OpenAI(api_key=settings.xai_api_key, base_url=settings.xai_base_url)
    response = client.responses.create(
        model=settings.xai_model or "grok-4.7",
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    text = getattr(response, "output_text", None) or _extract_output_text(response)
    return {
        "action": action,
        "text": (text or "").strip(),
        "model": settings.xai_model or "grok-4.7",
    }


def _extract_output_text(response: Any) -> str:
    chunks: list[str] = []
    for item in getattr(response, "output", None) or []:
        for content in getattr(item, "content", None) or []:
            if getattr(content, "type", None) in {"output_text", "text"}:
                chunks.append(getattr(content, "text", "") or "")
    return "\n".join(c for c in chunks if c)


def _build_prompt(
    action: AssistAction,
    *,
    lyrics: str,
    concept: str,
    line: str,
    style: str,
) -> str:
    style_bit = f"\nStyle / genre cues: {style}" if style.strip() else ""
    concept_bit = f"\nSong concept: {concept}" if concept.strip() else ""
    lyrics_bit = f"\nCurrent lyrics:\n{lyrics}" if lyrics.strip() else ""

    if action == "rhyme":
        target = line.strip() or _last_nonempty_line(lyrics)
        return (
            f"Suggest 8–12 rhymes and near-rhymes for this line end, ranked by singability."
            f"\nLine: {target}{style_bit}{concept_bit}"
            f"\nReturn a plain bullet list only."
        )
    if action == "rewrite_line":
        target = line.strip() or _last_nonempty_line(lyrics)
        return (
            f"Rewrite this lyric line 5 alternate ways, keeping similar syllable count and meaning."
            f"\nLine: {target}{style_bit}{concept_bit}{lyrics_bit}"
            f"\nReturn a numbered list of lines only."
        )
    if action == "continue_verse":
        return (
            f"Continue the next 4–8 lyric lines after the current lyrics."
            f" Match rhyme scheme and section tags if present.{style_bit}{concept_bit}{lyrics_bit}"
            f"\nReturn only the new lines (include a section tag if starting a new section)."
        )
    if action == "suggest_hooks":
        return (
            f"Propose 5 chorus/hook options (2–4 lines each) for this song."
            f"{style_bit}{concept_bit}{lyrics_bit}"
            f"\nLabel each option Hook 1..5."
        )
    # polish
    return (
        f"Polish these lyrics for singability and clarity while preserving meaning and structure tags."
        f"{style_bit}{concept_bit}{lyrics_bit}"
        f"\nReturn the full polished lyrics only."
    )


def _last_nonempty_line(lyrics: str) -> str:
    for line in reversed((lyrics or "").splitlines()):
        stripped = line.strip()
        if stripped and not stripped.startswith("["):
            return stripped
    return ""
