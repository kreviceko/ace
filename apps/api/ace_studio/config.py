from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: apps/api/ace_studio/config.py → ../../../
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    acestep_api_url: str = "http://127.0.0.1:8001"
    acestep_path: str = str(REPO_ROOT.parent / "ACE-Step-1.5")
    acestep_config_path: str = "acestep-v15-turbo"
    acestep_lm_model_path: str = "acestep-5Hz-lm-0.6B"
    acestep_init_llm: bool = False
    app_host: str = "127.0.0.1"
    app_port: int = 8787
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.7"
    data_dir: str = str(DATA_ROOT)
    poll_interval_sec: float = 1.5
    poll_timeout_sec: float = 600.0


def get_settings() -> Settings:
    return Settings()


def ensure_data_dirs(settings: Settings | None = None) -> Path:
    root = Path((settings or get_settings()).data_dir)
    for name in ("uploads", "library", "exports", "stems"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def read_acestep_env(settings: Settings | None = None) -> dict[str, str]:
    """Read sibling ACE-Step .env for configured DiT/LM (overrides studio defaults when present)."""
    settings = settings or get_settings()
    env_path = Path(settings.acestep_path) / ".env"
    values: dict[str, str] = {
        "ACESTEP_CONFIG_PATH": settings.acestep_config_path,
        "ACESTEP_LM_MODEL_PATH": settings.acestep_lm_model_path,
        "ACESTEP_INIT_LLM": "true" if settings.acestep_init_llm else "false",
    }
    if not env_path.exists():
        return values
    try:
        text = env_path.read_text(encoding="utf-8-sig")
    except OSError:
        return values
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key in values and val:
            values[key] = val
    return values
