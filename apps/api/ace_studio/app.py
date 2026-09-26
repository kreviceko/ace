"""ACE Studio FastAPI server — JSON API + Quasar SPA."""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ace_studio.config import ensure_data_dirs, get_settings
from ace_studio.routes.api import router as api_router

REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_DIST = REPO_ROOT / "apps" / "web" / "dist"


def create_app() -> FastAPI:
    settings = get_settings()
    ensure_data_dirs(settings)

    app = FastAPI(title="ACE Studio", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    if WEB_DIST.exists():
        assets = WEB_DIST / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str = ""):
            # Don't swallow API routes (already registered) or missing assets oddly
            candidate = WEB_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(WEB_DIST / "index.html")

    return app


def main() -> None:
    settings = get_settings()
    ensure_data_dirs(settings)
    print(f"ACE Studio API -> http://{settings.app_host}:{settings.app_port}")
    print(f"ACE-Step API expected at {settings.acestep_api_url}")
    if WEB_DIST.exists():
        print(f"Serving Quasar build from {WEB_DIST}")
    else:
        print(f"No web dist yet. Run: cd apps/web && npm run dev  (or npm run build)")
    uvicorn.run(
        "ace_studio.app:create_app",
        factory=True,
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
