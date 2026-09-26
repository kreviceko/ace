#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SiblingAce = Join-Path (Split-Path -Parent $RepoRoot) "ACE-Step-1.5"
$ApiDir = Join-Path $RepoRoot "apps\api"
$LogDir = Join-Path $env:TEMP "ace-studio-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $SiblingAce)) {
    throw "ACE-Step not found at $SiblingAce. Run .\scripts\install.ps1 first."
}

function Test-PortOpen([int]$Port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("127.0.0.1", $Port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

Write-Host "==> Starting ACE-Step API on :8001" -ForegroundColor Cyan
if (Test-PortOpen 8001) {
    Write-Host "Port 8001 already in use — assuming ACE-Step API is running."
} else {
    $aceLog = Join-Path $LogDir "acestep-api.log"
    Start-Process -FilePath "uv" -ArgumentList @("run", "acestep-api") `
        -WorkingDirectory $SiblingAce `
        -RedirectStandardOutput $aceLog `
        -RedirectStandardError $aceLog `
        -WindowStyle Minimized
    Write-Host "ACE-Step API starting (log: $aceLog)"
}

Write-Host "==> Waiting for ACE-Step /health ..."
$deadline = (Get-Date).AddMinutes(30)
$healthy = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 3
    }
}
if (-not $healthy) {
    Write-Warning "ACE-Step /health not ready yet (models may still be downloading). Studio will still start."
} else {
    Write-Host "ACE-Step API is healthy." -ForegroundColor Green
}

Write-Host "==> Starting ACE Studio UI on :8787" -ForegroundColor Cyan
Push-Location $ApiDir
try {
    uv run ace-studio
} finally {
    Pop-Location
}
