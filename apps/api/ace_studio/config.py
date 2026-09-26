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
    app_host: str = "127.0.0.1"
    app_port: int = 8787
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4-1-fast-non-reasoning"
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
