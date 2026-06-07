<#
.SYNOPSIS
    Smoke-test the native Windows installer inside Windows Sandbox.

.DESCRIPTION
    This script is intended to run inside Windows Sandbox from a mapped,
    read-only checkout. It copies the checkout to the sandbox user's
    LOCALAPPDATA, runs the PowerShell installer from that writable copy, and
    writes logs/results to a mapped output folder so they survive after the
    sandbox closes.
#>

[CmdletBinding()]
param(
    [string]$RepoRoot = "C:\Users\WDAGUtilityAccount\Desktop\HermesAgent",
    [string]$OutputDir = "C:\Users\WDAGUtilityAccount\Desktop\hermes-sandbox-results",
    [string]$Branch = "main",
    [switch]$RemoteClone,
    [int]$InstallerTimeoutMinutes = 45
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message"
}

function Assert-PathExists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "$Label not found at $Path"
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Save-Summary {
    $result.last_heartbeat = (Get-Date).ToString("o")
    $result | ConvertTo-Json -Depth 5 | Set-Content -Path $summaryPath -Encoding UTF8
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $OutputDir "sandbox-smoke-$timestamp.log"
$summaryPath = Join-Path $OutputDir "sandbox-smoke-$timestamp.json"

$result = [ordered]@{
    ok = $false
    started_at = (Get-Date).ToString("o")
    repo_root = $RepoRoot
    output_dir = $OutputDir
    branch = $Branch
    remote_clone = [bool]$RemoteClone
    install_root = $null
    hermes_version = $null
    gateway_status_exit_code = $null
    current_step = "starting"
    installer_pid = $null
    installer_exit_code = $null
    last_heartbeat = $null
    error = $null
}

Save-Summary
Start-Transcript -Path $logPath -Force | Out-Null
try {
    $result.current_step = "prepare-install-root"
    Save-Summary
    Write-Step "Preparing sandbox install root"
    $installRoot = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent"
    $result.install_root = $installRoot
    Remove-Item (Join-Path $env:LOCALAPPDATA "hermes") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $env:USERPROFILE ".hermes") -Recurse -Force -ErrorAction SilentlyContinue

    if (-not $RemoteClone) {
        $result.current_step = "copy-checkout"
        Save-Summary
        Assert-PathExists (Join-Path $RepoRoot "scripts\install.ps1") "Mapped installer"
        Write-Step "Copying mapped checkout to writable install root"
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $installRoot) | Out-Null
        robocopy $RepoRoot $installRoot /MIR /XD .git .venv venv node_modules __pycache__ .pytest_cache .mypy_cache .ruff_cache /XF *.pyc | Out-Host
        if ($LASTEXITCODE -gt 7) {
            throw "robocopy failed with exit code $LASTEXITCODE"
        }
        $installer = Join-Path $installRoot "scripts\install.ps1"
        Push-Location $installRoot
    } else {
        $installer = Join-Path $RepoRoot "scripts\install.ps1"
        Assert-PathExists $installer "Mapped installer"
        Push-Location $env:TEMP
    }

    try {
        $result.current_step = "run-installer"
        Save-Summary
        Write-Step "Running installer"
        $installerStdout = Join-Path $OutputDir "sandbox-installer-$timestamp.stdout.log"
        $installerStderr = Join-Path $OutputDir "sandbox-installer-$timestamp.stderr.log"
        $installerArgs = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $installer,
            "-InstallRoot", $installRoot,
            "-Branch", $Branch,
            "-SkipSetup",
            "-SkipGateway",
            "-Force"
        )
        $installerProcess = Start-Process -FilePath "powershell.exe" `
            -ArgumentList $installerArgs `
            -PassThru `
            -NoNewWindow `
            -RedirectStandardOutput $installerStdout `
            -RedirectStandardError $installerStderr
        $result.installer_pid = $installerProcess.Id
        Save-Summary
        $deadline = (Get-Date).AddMinutes($InstallerTimeoutMinutes)
        while (-not $installerProcess.WaitForExit(10000)) {
            if ((Get-Date) -gt $deadline) {
                try {
                    Stop-Process -Id $installerProcess.Id -Force -ErrorAction SilentlyContinue
                } catch {}
                throw "install.ps1 timed out after $InstallerTimeoutMinutes minutes; see $installerStdout and $installerStderr"
            }
            Save-Summary
        }
        $result.installer_exit_code = $installerProcess.ExitCode
        Save-Summary
        if (Test-Path $installerStdout) {
            Get-Content -Path $installerStdout | Out-Host
        }
        if (Test-Path $installerStderr) {
            Get-Content -Path $installerStderr | Out-Host
        }
        if ($installerProcess.ExitCode -ne 0) {
            throw "install.ps1 failed with exit code $($installerProcess.ExitCode); see $installerStdout and $installerStderr"
        }
    } finally {
        Pop-Location
    }

    $result.current_step = "validate-files"
    Save-Summary
    Write-Step "Validating installed files"
    $shim = Join-Path $env:LOCALAPPDATA "hermes\bin\hermes.cmd"
    Assert-PathExists $shim "Hermes shim"
    Assert-PathExists (Join-Path $installRoot ".venv\Scripts\python.exe") "Hermes venv python"

    $result.current_step = "validate-hermes-version"
    Save-Summary
    Write-Step "Validating hermes command"
    $env:Path = "$(Split-Path -Parent $shim);$env:Path"
    $versionOutput = & $shim --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "hermes --version failed: $($versionOutput -join "`n")"
    }
    $result.hermes_version = ($versionOutput -join "`n").Trim()
    Write-Host $result.hermes_version

    $result.current_step = "validate-gateway-status"
    Save-Summary
    Write-Step "Validating gateway status does not crash"
    & $shim gateway status
    $result.gateway_status_exit_code = $LASTEXITCODE
    if ($LASTEXITCODE -ne 0) {
        throw "hermes gateway status failed with exit code $LASTEXITCODE"
    }

    $result.current_step = "validate-native-bash"
    Save-Summary
    Write-Step "Validating native terminal path"
    $bashPath = [Environment]::GetEnvironmentVariable("HERMES_GIT_BASH_PATH", "User")
    if (-not $bashPath) {
        $bashPath = $env:HERMES_GIT_BASH_PATH
    }
    Assert-PathExists $bashPath "HERMES_GIT_BASH_PATH"
    Invoke-Checked $bashPath --version

    $result.ok = $true
    $result.current_step = "complete"
} catch {
    $result.error = $_.Exception.Message
    Write-Host ""
    Write-Host "FAILED: $($result.error)" -ForegroundColor Red
    throw
} finally {
    $result.finished_at = (Get-Date).ToString("o")
    Save-Summary
    Stop-Transcript | Out-Null
    Write-Host ""
    Write-Host "Log: $logPath"
    Write-Host "Summary: $summaryPath"
}
