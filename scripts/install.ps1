#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SiblingAce = Join-Path (Split-Path -Parent $RepoRoot) "ACE-Step-1.5"
$ApiDir = Join-Path $RepoRoot "apps\api"

Write-Host "==> ACE Studio install" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"

function Ensure-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { return }
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv not found on PATH after install. Restart the shell and re-run."
    }
}

Ensure-Uv

if (-not (Test-Path $SiblingAce)) {
    Write-Host "==> Cloning ACE-Step 1.5 to $SiblingAce"
    git clone --depth 1 https://github.com/ACE-Step/ACE-Step-1.5.git $SiblingAce
} else {
    Write-Host "==> ACE-Step already present at $SiblingAce"
}

Write-Host "==> Syncing ACE-Step (Python 3.12)"
Push-Location $SiblingAce
try {
    uv python install 3.12
    uv sync --python 3.12
    if (-not (Test-Path ".env")) {
        @"
ACESTEP_CONFIG_PATH=acestep-v15-turbo
ACESTEP_LM_MODEL_PATH=acestep-5Hz-lm-0.6B
ACESTEP_LM_BACKEND=pt
ACESTEP_INIT_LLM=true
ACESTEP_API_HOST=127.0.0.1
ACESTEP_API_PORT=8001
ACESTEP_OFFLOAD_TO_CPU=true
"@ | Set-Content -Path ".env" -Encoding UTF8
        Write-Host "Wrote ACE-Step .env defaults for ~8GB VRAM (edit as needed)."
    }
} finally {
    Pop-Location
}

Write-Host "==> Syncing ACE Studio API"
Push-Location $ApiDir
try {
    uv sync
} finally {
    Pop-Location
}

$WebDir = Join-Path $RepoRoot "apps\web"
Write-Host "==> Installing Quasar UI deps"
Push-Location $WebDir
try {
    npm install
} finally {
    Pop-Location
}

$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $RepoRoot ".env.example") $EnvFile
    Write-Host "Created $EnvFile"
}

New-Item -ItemType Directory -Force -Path `
    (Join-Path $RepoRoot "data\uploads"),
    (Join-Path $RepoRoot "data\library"),
    (Join-Path $RepoRoot "data\exports"),
    (Join-Path $RepoRoot "data\stems") | Out-Null

Write-Host ""
Write-Host "Install complete." -ForegroundColor Green
Write-Host "Next: .\scripts\start.ps1"
Write-Host "First generation downloads model weights (multi-GB)."
