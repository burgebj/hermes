#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Canonical test runner for hermes-agent on Windows.
    Run this instead of calling pytest directly to match CI behavior.

.DESCRIPTION
    Enforces:
      * -n 4 xdist workers (CI has 4 cores)
      * TZ=UTC, LANG=C.UTF-8 (approximation on Windows)
      * Credential env vars blanked
      * Proper venv activation

    Usage:
      scripts\run_tests.ps1                          # full suite
      scripts\run_tests.ps1 tests\agent\              # one directory
      scripts\run_tests.ps1 --tb=long -v              # pass-through pytest args
#>

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$pytestArgs
)

$ErrorActionPreference = "Stop"

# Activate venv (prefer .venv, fall back to venv)
$venvPaths = @(
    Join-Path $PSScriptRoot "..\.venv\Scripts\Activate.ps1"
    Join-Path $PSScriptRoot "..\venv\Scripts\Activate.ps1"
)

$activated = $false
foreach ($vp in $venvPaths) {
    if (Test-Path $vp) {
        Write-Host "[run_tests.ps1] Activating $vp" -ForegroundColor Cyan
        . $vp
        $activated = $true
        break
    }
}

if (-not $activated) {
    Write-Host "[run_tests.ps1] No virtualenv found. Creating one..." -ForegroundColor Yellow
    $venvDir = Join-Path $PSScriptRoot "..\.venv"
    python -m venv $venvDir
    . (Join-Path $venvDir "Scripts\Activate.ps1")
    pip install uv
    uv sync
}

# Enforce deterministic environment
$env:TZ = "UTC"
$env:PYTHONHASHSEED = "0"
$env:LANG = "C.UTF-8"

# Blank credential env vars (belt-and-suspenders with conftest.py)
$credSuffixes = @("_API_KEY", "_TOKEN", "_SECRET", "_PASSWORD", "_KEY", "_ID", "_CLIENT_ID", "_CLIENT_SECRET")
$env.Keys | Where-Object {
    foreach ($suffix in $credSuffixes) {
        if ($_ -like "*$suffix") { return $true }
    }
    return $false
} | ForEach-Object {
    Set-Item -Path "env:$_" -Value ""
}

# Ensure pytest and xdist are installed
$check = python -m pytest --version 2>&1
if ($LASTEXITCODE -ne 0) {
    pip install pytest pytest-xdist pytest-asyncio
}

# Build args
$args = @("-n", "4", "--tb=short", "-v")
if ($pytestArgs) {
    $args += $pytestArgs
}

Write-Host "[run_tests.ps1] Running: python -m pytest $($args -join ' ')" -ForegroundColor Cyan
Write-Host "[run_tests.ps1] TZ=$env:TZ PYTHONHASHSEED=$env:PYTHONHASHSEED" -ForegroundColor Cyan

$result = python -m pytest @args 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "[run_tests.ps1] All tests passed." -ForegroundColor Green
} else {
    Write-Host "[run_tests.ps1] Tests failed with exit code $exitCode" -ForegroundColor Red
}

# Deactivate venv
if (Test-Path function:deactivate) {
    deactivate
}

exit $exitCode
