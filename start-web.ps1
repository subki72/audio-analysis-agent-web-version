<#
.SYNOPSIS
  Menjalankan VoiceScript Web UI — FastAPI backend + Vite React dev server.
.DESCRIPTION
  Script ini menjalankan kedua server secara bersamaan:
    1. FastAPI (uvicorn) di port 8000
    2. Vite React dev server di port 5173

  Tekan Ctrl+C untuk menghentikan kedua proses.
.EXAMPLE
  .\start-web.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        VoiceScript Web UI Launcher       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Check prerequisites ──────────────────────────────────
$pythonOk = Get-Command python -ErrorAction SilentlyContinue
$nodeOk   = Get-Command node -ErrorAction SilentlyContinue

if (-not $pythonOk) {
    Write-Host "[ERROR] Python tidak ditemukan di PATH." -ForegroundColor Red
    exit 1
}
if (-not $nodeOk) {
    Write-Host "[ERROR] Node.js tidak ditemukan di PATH." -ForegroundColor Red
    exit 1
}

# ── Check .env ────────────────────────────────────────────
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "[WARN] File .env tidak ditemukan. Pastikan GROQ_API_KEY sudah diset." -ForegroundColor Yellow
}

# ── Install npm deps if needed ────────────────────────────
$webDir = Join-Path $ProjectRoot "web"
$nmDir  = Join-Path $webDir "node_modules"
if (-not (Test-Path $nmDir)) {
    Write-Host "[INFO] Menginstal dependensi npm..." -ForegroundColor Yellow
    Push-Location $webDir
    npm install
    Pop-Location
}

Write-Host ""
Write-Host "[1/2] Menjalankan FastAPI backend di http://localhost:8000 ..." -ForegroundColor Green
Write-Host "[2/2] Menjalankan Vite dev server di http://localhost:5173 ..." -ForegroundColor Green
Write-Host ""
Write-Host "  Buka browser di: " -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Tekan Ctrl+C untuk berhenti." -ForegroundColor DarkGray
Write-Host ""

# ── Launch both processes ─────────────────────────────────
$backendJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location $root
    python -m uvicorn web_api:app --reload --port 8000 2>&1
} -ArgumentList $ProjectRoot

$frontendJob = Start-Job -ScriptBlock {
    param($webDir)
    Set-Location $webDir
    npm run dev 2>&1
} -ArgumentList $webDir

try {
    # Stream output from both jobs
    while ($true) {
        $backendJob, $frontendJob | ForEach-Object {
            $output = Receive-Job -Job $_ -ErrorAction SilentlyContinue
            if ($output) {
                $prefix = if ($_.Id -eq $backendJob.Id) { "[API]" } else { "[WEB]" }
                $color  = if ($_.Id -eq $backendJob.Id) { "Cyan" } else { "Magenta" }
                foreach ($line in $output) {
                    Write-Host "$prefix $line" -ForegroundColor $color
                }
            }
        }
        Start-Sleep -Milliseconds 500

        # Check if any job failed
        if ($backendJob.State -eq 'Failed') {
            Write-Host "[ERROR] Backend process terminated." -ForegroundColor Red
            break
        }
        if ($frontendJob.State -eq 'Failed') {
            Write-Host "[ERROR] Frontend process terminated." -ForegroundColor Red
            break
        }
    }
}
finally {
    Write-Host ""
    Write-Host "[INFO] Menghentikan server..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "[INFO] Selesai." -ForegroundColor Green
}
