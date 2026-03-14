Write-Host '=== Self-Healing Detection ==='

# 1. 进程检查
Write-Host "`n--- Process Status ---"
$nodeProcs = Get-Process node* -ErrorAction SilentlyContinue
$pythonProcs = Get-Process python* -ErrorAction SilentlyContinue

if ($nodeProcs) {
    Write-Host "✓ Node/OpenClaw: RUNNING ($($nodeProcs.Count) instances)"
} else {
    Write-Host "✗ Node/OpenClaw: NOT FOUND"
}

if ($pythonProcs) {
    Write-Host "✓ Python: RUNNING ($($pythonProcs.Count) instances)"
} else {
    Write-Host "✗ Python: NOT FOUND"
}

# 2. 资源检查
Write-Host "`n--- Resource Status ---"
$mem = Get-CimInstance Win32_OperatingSystem
$memUsedGB = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / 1MB, 2)
$memTotalGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
$memPercent = [math]::Round(($memUsedGB / $memTotalGB) * 100, 1)
Write-Host "Memory: $memUsedGB / $memTotalGB GB ($memPercent%)"

$cpu = Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average
$cpuPercent = [math]::Round($cpu.Average, 1)
Write-Host "CPU: $cpuPercent%"

# 3. 磁盘检查
Write-Host "`n--- Disk Status ---"
$diskIssues = 0
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -gt 0 } | ForEach-Object {
    $usedGB = [math]::Round($_.Used / 1GB, 2)
    $freeGB = [math]::Round($_.Free / 1GB, 2)
    $totalGB = $usedGB + $freeGB
    $percent = [math]::Round(($usedGB / $totalGB) * 100, 1)
    
    if ($percent -gt 90) {
        Write-Host "⚠️ $($_.Name): $usedGB / $totalGB GB ($percent%) - CRITICAL"
        $diskIssues++
    } else {
        Write-Host "✓ $($_.Name): $usedGB / $totalGB GB ($percent%)"
    }
}

# 4. 大日志文件检查
Write-Host "`n--- Log Files ---"
$logIssues = 0
$eventsFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl'
$metricsFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\metrics.jsonl'

if (Test-Path $eventsFile) {
    $size = (Get-Item $eventsFile).Length
    $sizeMB = [math]::Round($size / 1MB, 2)
    if ($size -gt 100MB) {
        Write-Host "⚠️ events.jsonl: $sizeMB MB - TOO LARGE"
        $logIssues++
    } else {
        Write-Host "✓ events.jsonl: $sizeMB MB"
    }
}

if (Test-Path $metricsFile) {
    $size = (Get-Item $metricsFile).Length
    $sizeMB = [math]::Round($size / 1MB, 2)
    if ($size -gt 100MB) {
        Write-Host "⚠️ metrics.jsonl: $sizeMB MB - TOO LARGE"
        $logIssues++
    } else {
        Write-Host "✓ metrics.jsonl: $sizeMB MB"
    }
}

# 5. CRIT 事件检查
Write-Host "`n--- Recent CRIT Events (last 15 min) ---"
$critCount = 0
if (Test-Path $eventsFile) {
    $cutoff = (Get-Date).AddMinutes(-15).ToString('yyyy-MM-ddTHH:mm:ss')
    Get-Content $eventsFile -Tail 500 | ForEach-Object {
        try {
            $evt = $_ | ConvertFrom-Json
            if ($evt.level -eq 'CRIT' -and $evt.timestamp -gt $cutoff) {
                Write-Host "⚠️ [$($evt.timestamp)] $($evt.message)"
                $critCount++
            }
        } catch {}
    }
    if ($critCount -eq 0) {
        Write-Host "✓ No CRIT events"
    }
}

# 总结
Write-Host "`n=== Summary ==="
$totalIssues = 0

if ($memPercent -gt 85) {
    Write-Host "⚠️ High memory usage: $memPercent%"
    $totalIssues++
}

if ($cpuPercent -gt 80) {
    Write-Host "⚠️ High CPU usage: $cpuPercent%"
    $totalIssues++
}

$totalIssues += $diskIssues + $logIssues + $critCount

if ($totalIssues -eq 0) {
    Write-Host "✓ All systems healthy"
} else {
    Write-Host "⚠️ Total issues detected: $totalIssues"
}

exit $totalIssues
