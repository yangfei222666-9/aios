Write-Host "=== Phase 1: Detection ==="

# 1. 检查关键进程
Write-Host "--- Process Status ---"
$nodeProcs = Get-Process node -ErrorAction SilentlyContinue
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue

if ($nodeProcs) {
    Write-Host ("Node/OpenClaw: RUNNING (" + $nodeProcs.Count + " instances)")
} else {
    Write-Host "Node/OpenClaw: NOT FOUND"
}

if ($pythonProcs) {
    Write-Host ("Python: RUNNING (" + $pythonProcs.Count + " instances)")
} else {
    Write-Host "Python: NOT FOUND"
}

# 2. 资源监控
Write-Host ""
Write-Host "--- Resource Check ---"
$mem = Get-CimInstance Win32_OperatingSystem
$memUsedGB = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / 1MB, 2)
$memTotalGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
$memPercent = [math]::Round(($memUsedGB / $memTotalGB) * 100, 1)
Write-Host ("Memory: " + $memUsedGB + " GB / " + $memTotalGB + " GB (" + $memPercent + "%)")

$cpuLoad = (Get-CimInstance Win32_Processor).LoadPercentage
Write-Host ("CPU: " + $cpuLoad + "%")

# 3. 磁盘空间
Write-Host ""
Write-Host "--- Disk Space ---"
$diskIssues = @()
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -gt 0 } | ForEach-Object {
    $usedGB = [math]::Round($_.Used / 1GB, 2)
    $freeGB = [math]::Round($_.Free / 1GB, 2)
    $totalGB = $usedGB + $freeGB
    if ($totalGB -gt 0) {
        $percent = [math]::Round(($usedGB / $totalGB) * 100, 1)
        Write-Host ($_.Name + ": " + $usedGB + " GB / " + $totalGB + " GB (" + $percent + "%)")
        if ($percent -gt 90) {
            $diskIssues += $_.Name
        }
    }
}

# 4. 检查大日志文件
Write-Host ""
Write-Host "--- Large Log Files (>100MB) ---"
$logPaths = @(
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl",
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\metrics.jsonl"
)
$largeLogs = @()
foreach ($path in $logPaths) {
    if (Test-Path $path) {
        $item = Get-Item $path
        $sizeMB = [math]::Round($item.Length / 1MB, 2)
        Write-Host ($item.Name + ": " + $sizeMB + " MB")
        if ($item.Length -gt 100MB) {
            $largeLogs += $item.FullName
        }
    }
}
if ($largeLogs.Count -eq 0) { Write-Host "None over 100MB" }

# 5. 检查最近 CRIT 事件
Write-Host ""
Write-Host "--- Recent CRIT Events (last 15 min) ---"
$eventsFile = "C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl"
$critCount = 0
if (Test-Path $eventsFile) {
    $cutoff = (Get-Date).AddMinutes(-15)
    $lines = Get-Content $eventsFile -Tail 200
    foreach ($line in $lines) {
        try {
            $evt = $line | ConvertFrom-Json
            if ($evt.level -eq "CRIT") {
                $evtTime = [datetime]::Parse($evt.timestamp)
                if ($evtTime -gt $cutoff) {
                    Write-Host ("[" + $evt.timestamp + "] " + $evt.message)
                    $critCount++
                }
            }
        } catch {}
    }
    if ($critCount -eq 0) { Write-Host "None" }
} else {
    Write-Host "events.jsonl not found"
}

# 输出摘要供后续使用
Write-Host ""
Write-Host "=== SUMMARY ==="
Write-Host ("NODE_RUNNING=" + ($null -ne $nodeProcs).ToString())
Write-Host ("PYTHON_RUNNING=" + ($null -ne $pythonProcs).ToString())
Write-Host ("CPU_LOAD=" + $cpuLoad)
Write-Host ("MEM_PERCENT=" + $memPercent)
Write-Host ("DISK_ISSUES=" + ($diskIssues -join ","))
Write-Host ("LARGE_LOGS=" + ($largeLogs -join ","))
Write-Host ("CRIT_COUNT=" + $critCount)
