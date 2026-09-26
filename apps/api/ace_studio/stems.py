"""Demucs stem separation for library audio."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from ace_studio.config import Settings, ensure_data_dirs, get_settings


def demucs_available() -> bool:
    try:
        import demucs  # noqa: F401

        return True
    except ImportError:
        return False


def separate_stems(
    audio_path: Path,
    *,
    song_id: str,
    settings: Settings | None = None,
    model: str = "htdemucs",
) -> dict[str, Path]:
    settings = settings or get_settings()
    if not demucs_available():
        raise RuntimeError(
            "Demucs is not installed. Run: cd apps/api && uv sync --extra stems"
        )
    if not audio_path.exists():
        raise FileNotFoundError(str(audio_path))

    root = ensure_data_dirs(settings)
    out_root = root / "stems" / song_id
    if out_root.exists():
        shutil.rmtree(out_root, ignore_errors=True)
    out_root.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "demucs",
        "--name",
        model,
        "-o",
        str(out_root),
        str(audio_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or proc.stdout[-2000:] or "Demucs failed")

    # demucs writes out_root/<model>/<trackname>/*.wav
    wavs = list(out_root.rglob("*.wav"))
    if not wavs:
        raise RuntimeError("Demucs finished but produced no WAV stems")

    stems: dict[str, Path] = {}
    for wav in wavs:
        stems[wav.stem.lower()] = wav
    return stems


def zip_stems(stems: dict[str, Path], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, path in stems.items():
            zf.write(path, arcname=f"{name}{path.suffix}")
    return dest
