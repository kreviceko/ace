# ACE Studio

Local music studio for **[ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5)** — dark **Quasar / Vue 3** UI + FastAPI, with Create modes aligned to [AceMusic Create](https://acemusic.ai/playground/create):

| Mode | What it does |
|------|----------------|
| **Simple** | One description → full song (`sample_mode`) |
| **Custom** | Styles + lyrics + thinking / BPM / key / duration |
| **Remix** | Upload MP3 → cover (`task_type=cover`) |
| **Edit** | Repaint a time range (`task_type=repaint`) |

Also includes a Lyrics lab, ACE `/format_input`, local SQLite library, and downloadable results.

### Typical workflow (this project)

1. **Remix MP3** — upload a demo/melody sketch  
2. Add a **lyric concept** and/or **placeholder lyrics** for timing  
3. **Draft lyrics** (needs LM) or keep placeholders  
4. Generate the cover/remix  
5. Use **Simple** for album-style experiments from a description  


## Requirements

- Windows / macOS / Linux
- Git, [uv](https://docs.astral.sh/uv/), Python 3.11–3.12 (uv installs 3.12 for ACE-Step)
- NVIDIA GPU recommended (this project defaults to **turbo** for ~8GB VRAM)
- **System RAM: 32GB recommended.** 16GB can work with DiT-only (`ACESTEP_INIT_LLM=false`) if the Windows pagefile is large enough (32GB+). Loading ACE-Step weights needs a large virtual-memory commit; error `os error 1455` / “paging file is too small” means grow the pagefile or free RAM.
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
  apps/web/               # Quasar + Vue 3 SPA (Create / Library / Lyrics / Settings)
  apps/api/               # FastAPI BFF + ACE client + library
  scripts/                # install.ps1 / start.ps1
  data/                   # uploads, library audio, exports
../ACE-Step-1.5/          # official engine (sibling clone)
```

### Frontend dev

```powershell
cd apps\web
npm install
npm run dev          # http://127.0.0.1:9000  (proxies /api → :8787)

# separate terminal
cd apps\api
uv run ace-studio    # http://127.0.0.1:8787
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

- [x] Phase 0 — install ACE-Step beside the app
- [x] Quasar dark studio (Create / Library / Lyrics / Settings)
- [x] Simple / Custom / Remix / Edit API + UI
- [x] Format lyrics + library save/download
- [ ] ZIP export packs + LRC
- [ ] Interactive lyric assist (SpaceXAI)
- [ ] Stem export (Demucs + ACE extract)
- [ ] Waveform Edit mask UI

## License

App code: MIT (intended). ACE-Step and model weights remain under their upstream licenses.
