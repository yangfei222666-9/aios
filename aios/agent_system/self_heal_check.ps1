# Self-Healing Detection Script
$ErrorActionPreference = 'SilentlyContinue'
$issues = @()
$fixed = @()
$failed = @()

Write-Host "=== Phase 1: Detection ==="

# --- Processes ---
$nodeProcs = Get-Process -Name 'node' -ErrorAction SilentlyContinue
$pythonProcs = Get-Process -Name 'python','python3','python312' -ErrorAction SilentlyContinue
$nodeCount = if ($nodeProcs) { $nodeProcs.Count } else { 0 }
$pythonCount = if ($pythonProcs) { $pythonProcs.Count } else { 0 }
Write-Host "Node processes: $nodeCount"
Write-Host "Python processes: $pythonCount"

# --- Memory ---
$os = Get-CimInstance Win32_OperatingSystem
$usedMB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1024, 0)
$totalMB = [math]::Round($os.TotalVisibleMemorySize / 1024, 0)
$memPct = [math]::Round($usedMB * 100 / $totalMB, 1)
Write-Host "Memory: $usedMB MB / $totalMB MB ($memPct pct)"
if ($memPct -gt 85) {
    $issues += "HIGH_MEMORY:$memPct"
    Write-Host "  WARNING: Memory usage high"
}

# --- CPU ---
$cpu = (Get-CimInstance Win32_Processor).LoadPercentage
Write-Host "CPU: $cpu pct"
if ($cpu -gt 80) {
    $issues += "HIGH_CPU:$cpu"
    Write-Host "  WARNING: CPU usage high"
}

# --- Disk ---
Write-Host "--- Disk Space ---"
$diskIssues = @()
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -gt 0 } | ForEach-Object {
    $drv = $_
    $usedGB = [math]::Round($drv.Used / 1GB, 1)
    $freeGB = [math]::Round($drv.Free / 1GB, 1)
    $total = $usedGB + $freeGB
    if ($total -gt 0) {
        $pct = [math]::Round($usedGB * 100 / $total, 1)
        Write-Host "Disk $($drv.Name): $usedGB GB / $total GB ($pct pct)"
        if ($pct -gt 90) {
            $diskIssues += "DISK_FULL:$($drv.Name):$pct"
            Write-Host "  WARNING: Disk $($drv.Name) over 90pct"
        }
    }
}
$issues += $diskIssues

# --- Log File Sizes ---
Write-Host "--- Log File Sizes ---"
$dataDir = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data'
$bigLogs = @()
if (Test-Path $dataDir) {
    Get-ChildItem $dataDir -File | ForEach-Object {
        $f = $_
        $sizeMB = [math]::Round($f.Length / 1MB, 2)
        Write-Host "$($f.Name): $sizeMB MB"
        if ($f.Length -gt 100MB) {
            $bigLogs += $f.FullName
            Write-Host "  WARNING: $($f.Name) over 100MB"
        }
    }
}
foreach ($log in $bigLogs) { $issues += "BIG_LOG:$log" }

# --- CRIT Events ---
Write-Host "--- CRIT Events (last 15 min) ---"
$evFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl'
$critCount = 0
if (Test-Path $evFile) {
    $cutoff = (Get-Date).AddMinutes(-15)
    Get-Content $evFile -Tail 500 | ForEach-Object {
        try {
            $e = $_ | ConvertFrom-Json
            if ($e.level -eq 'CRIT') {
                $ts = [datetime]::Parse($e.timestamp)
                if ($ts -gt $cutoff) {
                    $critCount++
                    Write-Host "  CRIT: $($e.message)"
                }
            }
        } catch {}
    }
    Write-Host "CRIT events in last 15min: $critCount"
    if ($critCount -gt 0) { $issues += "CRIT_EVENTS:$critCount" }
} else {
    Write-Host "events.jsonl not found"
}

Write-Host ""
Write-Host "=== Phase 2: Diagnosis ==="
Write-Host "Issues detected: $($issues.Count)"
foreach ($issue in $issues) { Write-Host "  - $issue" }

Write-Host ""
Write-Host "=== Phase 3: Repair ==="

# Repair: Big logs
foreach ($issue in $issues) {
    if ($issue -like 'BIG_LOG:*') {
        $logPath = $issue.Substring(8)
        $archivePath = $logPath + '.archive_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.gz'
        Write-Host "Compressing large log: $logPath"
        try {
            Compress-Archive -Path $logPath -DestinationPath ($logPath + '.zip') -Force
            Remove-Item $logPath -Force
            Write-Host "  FIXED: Compressed and removed $logPath"
            $fixed += "BIG_LOG:$logPath"
        } catch {
            Write-Host "  FAILED: Could not compress $logPath - $_"
            $failed += "BIG_LOG:$logPath"
        }
    }
}

# Repair: Disk full - clean temp
foreach ($issue in $issues) {
    if ($issue -like 'DISK_FULL:*') {
        Write-Host "Cleaning temp files..."
        try {
            $tempPath = $env:TEMP
            $before = (Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer -and $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item -Force -ErrorAction SilentlyContinue
            $after = (Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            $freedMB = [math]::Round(($before - $after) / 1MB, 1)
            Write-Host "  Freed $freedMB MB from temp"
            $fixed += $issue
        } catch {
            Write-Host "  FAILED: Temp cleanup error - $_"
            $failed += $issue
        }
    }
}

# No repair needed for CPU/Memory (monitor only, not auto-kill)
foreach ($issue in $issues) {
    if ($issue -like 'HIGH_CPU:*' -or $issue -like 'HIGH_MEMORY:*') {
        Write-Host "Monitoring only (no auto-kill): $issue"
    }
}

Write-Host ""
Write-Host "=== Phase 4: Verification ==="
if ($fixed.Count -gt 0 -or $failed.Count -gt 0) {
    Start-Sleep -Seconds 5
    Write-Host "Post-repair check complete"
    Write-Host "Fixed: $($fixed.Count)"
    Write-Host "Failed: $($failed.Count)"
} else {
    Write-Host "No repairs needed"
}

Write-Host ""
Write-Host "=== Phase 5: Learning ==="
$healingFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl'
$record = @{
    timestamp = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
    issues_detected = $issues.Count
    issues_fixed = $fixed.Count
    issues_failed = $failed.Count
    issues = $issues
    fixed = $fixed
    failed = $failed
    cpu = $cpu
    memory_pct = $memPct
    node_procs = $nodeCount
    python_procs = $pythonCount
} | ConvertTo-Json -Compress
Add-Content -Path $healingFile -Value $record
Write-Host "Logged to self_healing.jsonl"

# Check repeat issues
if (Test-Path $healingFile) {
    $recentRecords = Get-Content $healingFile -Tail 20 | ForEach-Object {
        try { $_ | ConvertFrom-Json } catch {}
    }
    foreach ($issue in $issues) {
        $issueType = $issue.Split(':')[0]
        $repeatCount = ($recentRecords | Where-Object { $_.issues -contains $issue -or ($_.issues | Where-Object { $_ -like "$issueType*" }) }).Count
        if ($repeatCount -gt 3) {
            Write-Host "REPEAT_ISSUE: $issueType seen $repeatCount times - needs deep analysis"
        }
    }
}

Write-Host ""
Write-Host "=== Summary ==="
if ($issues.Count -eq 0) {
    Write-Host "HEALING_OK"
} elseif ($failed.Count -eq 0) {
    Write-Host "HEALING_FIXED:$($fixed.Count)"
} else {
    Write-Host "HEALING_FAILED:$($failed.Count)"
}
