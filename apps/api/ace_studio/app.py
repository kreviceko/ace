"""Entry point: Gradio Create UI for ACE Studio."""

from __future__ import annotations

import gradio as gr

from ace_studio.config import ensure_data_dirs, get_settings
from ace_studio.ui import build_ui


def main() -> None:
    settings = get_settings()
    ensure_data_dirs(settings)
    demo = build_ui()
    print(f"ACE Studio -> http://{settings.app_host}:{settings.app_port}")
    print(f"ACE-Step API expected at {settings.acestep_api_url}")
    demo.queue().launch(
        server_name=settings.app_host,
        server_port=settings.app_port,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(primary_hue="violet", secondary_hue="slate"),
    )


if __name__ == "__main__":
    main()
