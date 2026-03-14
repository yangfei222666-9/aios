# Self-Healing Agent - Phase 1: Detection
$results = @{
    issues = @()
    stats = @{}
}

Write-Host "=== PHASE 1: DETECTION ==="

# 1. Process Status
Write-Host "`n--- Processes ---"
$nodeProcs = Get-Process node -ErrorAction SilentlyContinue
if ($nodeProcs) {
    $nodeInfo = $nodeProcs | ForEach-Object { "PID=$($_.Id) Mem=$([math]::Round($_.WorkingSet64/1MB,1))MB" }
    Write-Host "Node.js: RUNNING [$($nodeInfo -join '; ')]"
} else {
    Write-Host "Node.js: NOT FOUND"
}

$pyProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pyProcs) {
    $pyInfo = $pyProcs | ForEach-Object { "PID=$($_.Id) Mem=$([math]::Round($_.WorkingSet64/1MB,1))MB" }
    Write-Host "Python: RUNNING [$($pyInfo -join '; ')]"
} else {
    Write-Host "Python: NOT FOUND"
}

# 2. Memory & CPU
Write-Host "`n--- Resources ---"
$os = Get-CimInstance Win32_OperatingSystem
$memUsedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 2)
$memTotalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$memPct = [math]::Round(($memUsedGB / $memTotalGB) * 100, 1)
Write-Host "Memory: ${memUsedGB}GB / ${memTotalGB}GB (${memPct}%)"

$cpuLoad = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
Write-Host "CPU: ${cpuLoad}%"

if ($cpuLoad -gt 80) {
    Write-Host "  ISSUE: CPU > 80%"
    $top5 = Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 | ForEach-Object {
        "    $($_.ProcessName) PID=$($_.Id) CPU=$([math]::Round($_.CPU,1))s Mem=$([math]::Round($_.WorkingSet64/1MB,1))MB"
    }
    $top5 | ForEach-Object { Write-Host $_ }
}

# 3. Disk Space
Write-Host "`n--- Disk Space ---"
$diskIssues = 0
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -gt 0 } | ForEach-Object {
    $usedGB = [math]::Round($_.Used / 1GB, 2)
    $freeGB = [math]::Round($_.Free / 1GB, 2)
    $totalGB = $usedGB + $freeGB
    $pct = [math]::Round(($usedGB / $totalGB) * 100, 1)
    Write-Host "$($_.Name): ${usedGB}GB / ${totalGB}GB (${pct}%)"
    if ($pct -gt 90) {
        Write-Host "  ISSUE: Disk $($_.Name) > 90% full!"
        $diskIssues++
    }
}

# 4. Large Log Files
Write-Host "`n--- Log File Sizes ---"
$logFiles = @(
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl",
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\metrics.jsonl",
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl",
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\lessons.json"
)
$largeFiles = 0
foreach ($lf in $logFiles) {
    if (Test-Path $lf) {
        $sz = (Get-Item $lf).Length
        $szMB = [math]::Round($sz / 1MB, 2)
        $label = if ($szMB -gt 100) { " << OVERSIZED" } else { "" }
        Write-Host "  $([System.IO.Path]::GetFileName($lf)): ${szMB}MB${label}"
        if ($szMB -gt 100) { $largeFiles++ }
    } else {
        Write-Host "  $([System.IO.Path]::GetFileName($lf)): not found"
    }
}

# Also check workspace data folder total
$dataDir = "C:\Users\A\.openclaw\workspace\aios\agent_system\data"
if (Test-Path $dataDir) {
    $totalDataMB = [math]::Round((Get-ChildItem $dataDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    Write-Host "  [data/ total]: ${totalDataMB}MB"
}

# 5. Recent CRIT events
Write-Host "`n--- CRIT Events (last 15 min) ---"
$eventsFile = "C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl"
$critCount = 0
if (Test-Path $eventsFile) {
    $cutoff = (Get-Date).AddMinutes(-15).ToString("yyyy-MM-ddTHH:mm:ss")
    Get-Content $eventsFile -Tail 500 -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $ev = $_ | ConvertFrom-Json
            if ($ev.level -eq "CRIT" -and $ev.timestamp -gt $cutoff) {
                $critCount++
                if ($critCount -le 5) {
                    Write-Host "  [$($ev.timestamp)] $($ev.message)"
                }
            }
        } catch {}
    }
    if ($critCount -eq 0) { Write-Host "  None" }
    elseif ($critCount -gt 5) { Write-Host "  ... +$($critCount - 5) more" }
} else {
    Write-Host "  events.jsonl not found"
}

# 6. Top memory consumers (for leak detection)
Write-Host "`n--- Top Memory Processes ---"
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 8 | ForEach-Object {
    Write-Host "  $($_.ProcessName) PID=$($_.Id) Mem=$([math]::Round($_.WorkingSet64/1MB,1))MB"
}

Write-Host "`n=== DETECTION COMPLETE ==="
Write-Host "Summary: DiskIssues=$diskIssues LargeFiles=$largeFiles CritEvents=$critCount CPU=${cpuLoad}% Mem=${memPct}%"
