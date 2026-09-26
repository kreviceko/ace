# ACE Studio

Local music studio UI for **[ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5)**, with Create modes aligned to [AceMusic Create](https://acemusic.ai/playground/create):

| Mode | What it does |
|------|----------------|
| **Simple** | One description → full song (`sample_mode`) |
| **Custom** | Styles + lyrics + thinking / BPM / key / duration |
| **Remix** | Upload MP3 → cover (`task_type=cover`) |
| **Edit** | Repaint a time range (`task_type=repaint`) |

Also includes lyric formatting via ACE `/format_input`, a local SQLite library, and downloadable results.

## Requirements

- Windows / macOS / Linux
- Git, [uv](https://docs.astral.sh/uv/), Python 3.11–3.12 (uv installs 3.12 for ACE-Step)
- NVIDIA GPU recommended (this project defaults to **turbo + 0.6B LM** for ~8GB VRAM)
- ffmpeg on PATH (optional but useful)

## Quick start (Windows)

```powershell
git clone <this-repo-url> ace
cd ace
.\scripts\install.ps1
.\scripts\start.ps1
```

Open **http://127.0.0.1:8787**

`install.ps1` clones ACE-Step beside this repo as `../ACE-Step-1.5` and syncs dependencies.

### Manual two-process start

```powershell
# Terminal 1 — engine
cd ..\ACE-Step-1.5
uv run acestep-api

# Terminal 2 — studio UI
cd ..\ace\apps\api
uv run ace-studio
```

## Layout

```
ace/                      # this repo
  apps/api/               # Gradio UI + ACE client + library
  scripts/                # install.ps1 / start.ps1
  data/                   # uploads, library audio, exports
../ACE-Step-1.5/          # official engine (sibling clone)
```

## Config

Copy `.env.example` → `.env`:

```env
APP_PORT=8787
ACESTEP_API_URL=http://127.0.0.1:8001
ACESTEP_PATH=../ACE-Step-1.5
# Optional lyric assist later:
# XAI_API_KEY=
```

ACE-Step’s own `.env` (in the sibling repo) controls DiT/LM models. Defaults written by install:

- `acestep-v15-turbo`
- `acestep-5Hz-lm-0.6B` with `pt` backend
- `ACESTEP_OFFLOAD_TO_CPU=true`

For native stem extract / lego / complete you need a **base** DiT (`acestep-v15-base` or XL-base). Demucs-based stem export is planned next.

## First run notes

- The first generation downloads multi‑GB weights into the Hugging Face cache.
- Laptop GPUs (~8GB) should keep Thinking on with the 0.6B LM; disable Thinking if you OOM.
- Remix/Edit need a source audio upload (≤10 minutes recommended).

## Roadmap

- [x] Phase 0 — install ACE-Step + Create MVP UI
- [x] Simple / Custom / Remix / Edit
- [x] Format lyrics + library save/download
- [ ] ZIP export packs + LRC
- [ ] Interactive lyric assist (SpaceXAI)
- [ ] Stem export (Demucs + ACE extract)
- [ ] Quasar SPA frontend (optional upgrade from Gradio)

## License

App code: MIT (intended). ACE-Step and model weights remain under their upstream licenses.
