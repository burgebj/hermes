<#
.SYNOPSIS
    Build native Windows release packaging artifacts.

.DESCRIPTION
    Creates a small Windows release zip containing the native installer and
    validation harness, writes its SHA256, and renders Winget manifest YAML
    files into dist/windows/winget. This script does not publish anything.
#>

[CmdletBinding()]
param(
    [string]$Version,
    [string]$ReleaseTag,
    [string]$OutputDir,
    [string]$AssetBaseUrl
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if (-not $PSScriptRoot) {
    $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

function Get-ProjectVersion {
    $pyproject = Get-Content -LiteralPath (Join-Path $repoRoot "pyproject.toml") -Raw
    $match = [regex]::Match($pyproject, '(?m)^version\s*=\s*"([^"]+)"')
    if (-not $match.Success) {
        throw "Could not find project.version in pyproject.toml"
    }
    return $match.Groups[1].Value
}

function Copy-RequiredFile {
    param(
        [Parameter(Mandatory=$true)][string]$RelativePath,
        [Parameter(Mandatory=$true)][string]$StagingRoot
    )
    $source = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path $source)) {
        throw "Required packaging input is missing: $RelativePath"
    }
    $destination = Join-Path $StagingRoot $RelativePath
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
}

function Get-Sha256Hex {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (Get-Command "Get-FileHash" -ErrorAction SilentlyContinue) {
        return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    }

    $stream = [IO.File]::OpenRead($Path)
    try {
        $sha = [Security.Cryptography.SHA256]::Create()
        try {
            $bytes = $sha.ComputeHash($stream)
            return (($bytes | ForEach-Object { $_.ToString("x2") }) -join "")
        } finally {
            $sha.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

if (-not $Version) {
    $Version = Get-ProjectVersion
}
if (-not $ReleaseTag) {
    $ReleaseTag = "v$Version"
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "dist\windows"
}
if (-not $AssetBaseUrl) {
    $AssetBaseUrl = "https://github.com/NousResearch/hermes-agent/releases/download/$ReleaseTag"
}

$outFull = [IO.Path]::GetFullPath($OutputDir)
$stagingRoot = Join-Path $outFull "staging\hermes-agent-windows-$Version"
$zipPath = Join-Path $outFull "hermes-agent-windows-$Version.zip"
$shaPath = "$zipPath.sha256"
$wingetOut = Join-Path $outFull "winget"

Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $shaPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $stagingRoot, $wingetOut | Out-Null

$requiredFiles = @(
    "README.md",
    "scripts\install.ps1",
    "scripts\install.cmd",
    "scripts\windows-sandbox-validate.ps1",
    "scripts\windows-sandbox-smoke.ps1",
    "website\docs\user-guide\windows-native.md"
)

foreach ($relativePath in $requiredFiles) {
    Copy-RequiredFile -RelativePath $relativePath -StagingRoot $stagingRoot
}

$packageReadme = @"
# Hermes Agent Windows Bootstrap

Version: $Version

Run from PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\install.ps1
```

Or from CMD:

```cmd
scripts\install.cmd
```

The installer provisions Hermes under `%LOCALAPPDATA%\hermes` without WSL.
See `website/docs/user-guide/windows-native.md` for details.
"@
Set-Content -LiteralPath (Join-Path $stagingRoot "WINDOWS-PACKAGE.md") -Value $packageReadme -Encoding UTF8

Compress-Archive -Path (Join-Path $stagingRoot "*") -DestinationPath $zipPath -Force
$sha256 = Get-Sha256Hex -Path $zipPath
Set-Content -LiteralPath $shaPath -Value "$sha256  $(Split-Path -Leaf $zipPath)" -Encoding ASCII

$installerUrl = "$AssetBaseUrl/$(Split-Path -Leaf $zipPath)"
$templates = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot "winget") -Filter "*.yaml.in"
foreach ($template in $templates) {
    $content = Get-Content -LiteralPath $template.FullName -Raw
    $content = $content.Replace("{{VERSION}}", $Version)
    $content = $content.Replace("{{INSTALLER_URL}}", $installerUrl)
    $content = $content.Replace("{{INSTALLER_SHA256}}", $sha256)
    $targetName = $template.Name -replace '\.in$', ''
    Set-Content -LiteralPath (Join-Path $wingetOut $targetName) -Value $content -Encoding UTF8
}

Write-Host "Windows package built:"
Write-Host "  $zipPath"
Write-Host "  $shaPath"
Write-Host "Winget manifests:"
Write-Host "  $wingetOut"
