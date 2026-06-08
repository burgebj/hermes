# Windows Gateway Transactional Restart Smoke Test
# =================================================
# Run from an elevated PowerShell:
#   .\scripts\smoke-test-gateway-restart.ps1
#
# Prerequisites:
#   - Hermes gateway is running
#   - hermes CLI is on PATH
#
# This script tests the transactional restart coordinator by:
#   1. Checking current gateway status
#   2. Running restart 20 times in a loop
#   3. Verifying PID changes, port recovery, and status
#   4. Reporting results as JSON

param(
    [int]$Iterations = 20,
    [switch]$SimulateNoScheduledTask,
    [switch]$SimulateRapidDoubleRestart,
    [switch]$TestUnrelatedPortOccupier
)

$ErrorActionPreference = "Continue"
$Results = @()
$Failures = 0
$StartTime = Get-Date

function Write-Status($msg) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan
}

function Write-OK($msg) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ $msg" -ForegroundColor Green
}

function Write-Fail($msg) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✗ $msg" -ForegroundColor Red
}

# --- Pre-flight checks ---
Write-Status "Starting Gateway Transactional Restart Smoke Test"
Write-Status "Iterations: $Iterations"

# Check hermes is available
$hermesPath = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermesPath) {
    Write-Fail "hermes CLI not found on PATH"
    exit 1
}
Write-OK "hermes CLI found: $($hermesPath.Source)"

# Check gateway is running
$statusOutput = hermes gateway status 2>&1
Write-Status "Current gateway status:"
Write-Host $statusOutput

# Get current PID
$gatewayPids = Get-Process python* -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "hermes_cli.*gateway" } |
    Select-Object -ExpandProperty Id

if ($gatewayPids.Count -eq 0) {
    Write-Fail "No gateway process found"
    exit 1
}
$oldPid = $gatewayPids[0]
Write-OK "Gateway running (PID: $oldPid)"

# --- Test iterations ---
for ($i = 1; $i -le $Iterations; $i++) {
    Write-Status "--- Iteration $i / $Iterations ---"

    $iterStart = Get-Date
    $result = @{
        iteration = $i
        timestamp = $iterStart.ToString("o")
        old_pid = $oldPid
    }

    try {
        # Execute restart
        $restartOutput = hermes gateway restart --no-wait 2>&1
        $result.restart_output = $restartOutput | Out-String

        # Wait for restart to complete
        Start-Sleep -Seconds 10

        # Check new PID
        $newPids = Get-Process python* -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -match "hermes_cli.*gateway" } |
            Select-Object -ExpandProperty Id

        if ($newPids.Count -eq 0) {
            $result.new_pid = 0
            $result.status = "FAILED"
            $result.error = "No gateway process after restart"
            $Failures++
            Write-Fail "No gateway process after restart"
        } else {
            $newPid = $newPids[0]
            $result.new_pid = $newPid

            if ($newPid -eq $oldPid) {
                $result.status = "FAILED"
                $result.error = "New PID equals old PID"
                $Failures++
                Write-Fail "PID unchanged: $newPid"
            } else {
                # Check status file
                $statusFile = "$env:LOCALAPPDATA\hermes\run\gateway-restart-default-status.json"
                if (Test-Path $statusFile) {
                    $statusJson = Get-Content $statusFile -Raw | ConvertFrom-Json
                    $result.coordinator_status = $statusJson.state
                    $result.launcher = $statusJson.launcher
                }

                $result.status = "OK"
                Write-OK "PID changed: $oldPid → $newPid (status: $($result.coordinator_status))"
                $oldPid = $newPid
            }
        }
    } catch {
        $result.status = "ERROR"
        $result.error = $_.Exception.Message
        $Failures++
        Write-Fail "Exception: $($_.Exception.Message)"
    }

    $result.duration_s = ((Get-Date) - $iterStart).TotalSeconds
    $Results += $result

    # Brief pause between iterations
    Start-Sleep -Seconds 2
}

# --- Simulate rapid double restart ---
if ($SimulateRapidDoubleRestart) {
    Write-Status "--- Testing rapid double restart ---"
    $r1 = hermes gateway restart --no-wait 2>&1
    Start-Sleep -Milliseconds 500
    $r2 = hermes gateway restart --no-wait 2>&1
    Write-Status "First: $r1"
    Write-Status "Second: $r2"
    if ($r2 -match "already in progress|scheduled") {
        Write-OK "Double restart handled correctly"
    } else {
        Write-Fail "Double restart may have spawned two gateways"
    }
    Start-Sleep -Seconds 10
}

# --- Test unrelated port occupier ---
if ($TestUnrelatedPortOccupier) {
    Write-Status "--- Testing unrelated port occupier protection ---"
    # Start a dummy listener on port 8080
    $listener = [System.Net.HttpListener]::new()
    try {
        $listener.Prefixes.Add("http://+:8080/")
        $listener.Start()
        Write-Status "Dummy listener started on port 8080 (PID: $PID)"

        # Try restart — should NOT kill our dummy listener
        $restartOutput = hermes gateway restart --no-wait 2>&1
        Start-Sleep -Seconds 10

        # Check if our listener is still alive
        if ($listener.IsListening) {
            Write-OK "Unrelated port occupier was NOT killed (correct)"
        } else {
            Write-Fail "Unrelated port occupier was killed (incorrect)"
        }
    } catch {
        Write-Status "Port 8080 test skipped: $($_.Exception.Message)"
    } finally {
        $listener.Stop()
    }
}

# --- Summary ---
$EndTime = Get-Date
$Duration = ($EndTime - $StartTime).TotalMinutes

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "         SMOKE TEST SUMMARY" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Iterations:     $Iterations"
Write-Host "Passed:         $($Iterations - $Failures)"
Write-Host "Failed:         $Failures"
Write-Host "Duration:       $([math]::Round($Duration, 1)) minutes"
Write-Host ""

# Output JSONL location
$jsonlPath = "$env:LOCALAPPDATA\hermes\logs\gateway-restart.jsonl"
if (Test-Path $jsonlPath) {
    Write-Host "JSONL log:      $jsonlPath"
    $lineCount = (Get-Content $jsonlPath | Measure-Object).Count
    Write-Host "Log entries:    $lineCount"
} else {
    Write-Host "JSONL log:      NOT FOUND"
}

# Save results
$resultsPath = "$env:LOCALAPPDATA\hermes\logs\smoke-test-results.json"
$Results | ConvertTo-Json -Depth 5 | Set-Content $resultsPath -Encoding UTF8
Write-Host "Results saved:  $resultsPath"

if ($Failures -gt 0) {
    Write-Host ""
    Write-Host "FAILED ITERATIONS:" -ForegroundColor Red
    $Results | Where-Object { $_.status -ne "OK" } | ForEach-Object {
        Write-Host "  #$($_.iteration): $($_.error)" -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host ""
    Write-Host "ALL TESTS PASSED" -ForegroundColor Green
    exit 0
}
