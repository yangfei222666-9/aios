# Phase 2: Diagnosis - Node.js memory check
Write-Host "=== PHASE 2: DIAGNOSIS ==="

# Check Node.js (OpenClaw Gateway) memory - 1.75GB is high
$nodeProc = Get-Process -Id 23404 -ErrorAction SilentlyContinue
if ($nodeProc) {
    $memMB = [math]::Round($nodeProc.WorkingSet64 / 1MB, 1)
    $startTime = $nodeProc.StartTime
    $uptime = (Get-Date) - $startTime
    $uptimeHrs = [math]::Round($uptime.TotalHours, 1)
    $memPerHour = if ($uptimeHrs -gt 0) { [math]::Round($memMB / $uptimeHrs, 1) } else { 0 }
    
    Write-Host "Node.js PID=23404:"
    Write-Host "  Memory: ${memMB}MB"
    Write-Host "  Started: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "  Uptime: ${uptimeHrs}h"
    Write-Host "  Avg mem/hour: ${memPerHour}MB/h"
    
    if ($memMB -gt 1500) {
        Write-Host "  STATUS: Memory is HIGH (>1.5GB) but this is OpenClaw gateway - normal for long sessions"
        Write-Host "  VERDICT: MONITOR (not critical yet, would be concerning >2.5GB)"
    }
}

# Check Python processes
Write-Host "`n--- Python Processes ---"
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $memMB = [math]::Round($_.WorkingSet64 / 1MB, 1)
    $cmdLine = ""
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        if ($cmdLine.Length -gt 120) { $cmdLine = $cmdLine.Substring(0, 120) + "..." }
    } catch {}
    Write-Host "  PID=$($_.Id) Mem=${memMB}MB CMD=$cmdLine"
}

# Check TEMP folder size
Write-Host "`n--- TEMP Folder ---"
$tempPath = $env:TEMP
$tempSizeMB = [math]::Round((Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
Write-Host "  TEMP size: ${tempSizeMB}MB"

Write-Host "`n=== DIAGNOSIS COMPLETE ==="
