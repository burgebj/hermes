<#
.SYNOPSIS
    Launch a repeatable Windows Sandbox installer validation run.

.DESCRIPTION
    Generates a temporary .wsb file for the current checkout, maps this repo
    read-only into the sandbox, maps a writable results directory back to the
    host, and runs scripts/windows-sandbox-smoke.ps1 at sandbox logon.

    The sandbox is disposable. Copy anything important from the results folder
    before closing it.
#>

[CmdletBinding()]
param(
    [string]$RepoRoot,
    [string]$OutputDir,
    [string]$Branch = "main",
    [switch]$RemoteClone,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

function Escape-Xml([string]$Value) {
    return [Security.SecurityElement]::Escape($Value)
}

if (-not $PSScriptRoot) {
    $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if (-not $OutputDir) {
    $OutputDir = Join-Path (Resolve-Path $RepoRoot).Path "sandbox-results"
}

$repoFull = [IO.Path]::GetFullPath($RepoRoot)
$outFull = [IO.Path]::GetFullPath($OutputDir)

if (-not (Test-Path (Join-Path $repoFull "scripts\windows-sandbox-smoke.ps1"))) {
    throw "RepoRoot does not look like Hermes Agent: $repoFull"
}

New-Item -ItemType Directory -Force -Path $outFull | Out-Null

$guestRepo = "C:\Users\WDAGUtilityAccount\Desktop\HermesAgent"
$guestOut = "C:\Users\WDAGUtilityAccount\Desktop\hermes-sandbox-results"
$remoteFlag = if ($RemoteClone) { " -RemoteClone" } else { "" }
$command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$guestRepo\scripts\windows-sandbox-smoke.ps1`" -RepoRoot `"$guestRepo`" -OutputDir `"$guestOut`" -Branch `"$Branch`"$remoteFlag"

$wsb = @"
<Configuration>
  <Networking>Enable</Networking>
  <ClipboardRedirection>Enable</ClipboardRedirection>
  <PrinterRedirection>Disable</PrinterRedirection>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$(Escape-Xml $repoFull)</HostFolder>
      <SandboxFolder>$guestRepo</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>$(Escape-Xml $outFull)</HostFolder>
      <SandboxFolder>$guestOut</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>$(Escape-Xml $command)</Command>
  </LogonCommand>
</Configuration>
"@

$wsbPath = Join-Path $outFull "hermes-installer-validation.wsb"
Set-Content -Path $wsbPath -Value $wsb -Encoding UTF8

Write-Host "Windows Sandbox config written:"
Write-Host "  $wsbPath"
Write-Host ""
Write-Host "Results will be written to:"
Write-Host "  $outFull"

if ($NoLaunch) {
    exit 0
}

$sandbox = Get-Command "WindowsSandbox.exe" -ErrorAction SilentlyContinue
if (-not $sandbox) {
    throw "WindowsSandbox.exe was not found. Enable Windows Sandbox in Windows Features, reboot, then rerun."
}

Start-Process -FilePath $sandbox.Source -ArgumentList "`"$wsbPath`""
