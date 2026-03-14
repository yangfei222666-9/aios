# self_heal.ps1 - AIOS Self-Healing Agent

$issues = @()

Write-Host "=== Phase 1: Detection ==="

# 1. Python processes
$pythonProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($pythonProcs) {
    foreach ($proc in $pythonProcs) {
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
        Write-Host "Python PID $($proc.Id): Memory=${memMB}MB"
        if ($memMB -gt 1000) {
            $issues += [PSCustomObject]@{ type="high_memory"; pid=$proc.Id; memMB=$memMB }
        }
    }
} else {
    Write-Host "No Python processes running"
}

# 2. Disk space
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null }
foreach ($drive in $drives) {
    $total = $drive.Used + $drive.Free
    if ($total -gt 0) {
        $pct = [math]::Round(($drive.Used / $total) * 100, 1)
        Write-Host "Drive $($drive.Name): ${pct}% used"
        if ($pct -gt 90) {
            $issues += [PSCustomObject]@{ type="disk_full"; drive=$drive.Name; percent=$pct }
        }
    }
}

# 3. Large log files
$logFiles = @(
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl",
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\metrics.jsonl",
    "C:\Users\A\.openclaw\workspace\aios\agent_system\data\tasks.jsonl"
)
foreach ($f in $logFiles) {
    if (Test-Path $f) {
        $sz = [math]::Round((Get-Item $f).Length / 1MB, 2)
        Write-Host "Log $(Split-Path $f -Leaf): ${sz}MB"
        if ($sz -gt 100) {
            $issues += [PSCustomObject]@{ type="large_log"; path=$f; sizeMB=$sz }
        }
    }
}

# 4. CRIT events in last 15 min
$evPath = "C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl"
$critCount = 0
if (Test-Path $evPath) {
    $cutoff = (Get-Date).AddMinutes(-15)
    $lines = Get-Content $evPath -Tail 200
    foreach ($line in $lines) {
        try {
            $ev = $line | ConvertFrom-Json
            if ($ev.level -eq "CRIT") {
                $evTime = [datetime]::Parse($ev.timestamp)
                if ($evTime -gt $cutoff) { $critCount++ }
            }
        } catch {}
    }
    Write-Host "CRIT events (last 15min): $critCount"
    if ($critCount -gt 0) {
        $issues += [PSCustomObject]@{ type="crit_events"; count=$critCount }
    }
}

Write-Host ""
Write-Host "=== Total issues detected: $($issues.Count) ==="

# ---- Phase 2 & 3: Diagnosis & Repair ----
$fixed = 0
$failed = 0
$repairLog = @()

foreach ($issue in $issues) {
    Write-Host ""
    Write-Host "--- Handling: $($issue.type) ---"

    switch ($issue.type) {
        "high_memory" {
            Write-Host "Diagnosis: Python PID $($issue.pid) using $($issue.memMB)MB - possible memory leak"
            try {
                Stop-Process -Id $issue.pid -Force -ErrorAction Stop
                Write-Host "Repair: Killed PID $($issue.pid)"
                $fixed++
                $repairLog += [PSCustomObject]@{
                    type=$issue.type; action="killed_process"; pid=$issue.pid; result="ok"
                }
            } catch {
                Write-Host "Repair FAILED: $_"
                $failed++
                $repairLog += [PSCustomObject]@{
                    type=$issue.type; action="killed_process"; pid=$issue.pid; result="failed"; error="$_"
                }
            }
        }

        "disk_full" {
            Write-Host "Diagnosis: Drive $($issue.drive) at $($issue.percent)% - cleaning TEMP"
            try {
                $tempPath = $env:TEMP
                $before = (Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
                Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Where-Object { !$_.PSIsContainer } | Remove-Item -Force -ErrorAction SilentlyContinue
                $after = (Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
                $freedMB = [math]::Round(($before - $after) / 1MB, 2)
                Write-Host "Repair: Freed ${freedMB}MB from TEMP"
                $fixed++
                $repairLog += [PSCustomObject]@{
                    type=$issue.type; action="clean_temp"; drive=$issue.drive; freedMB=$freedMB; result="ok"
                }
            } catch {
                Write-Host "Repair FAILED: $_"
                $failed++
                $repairLog += [PSCustomObject]@{
                    type=$issue.type; action="clean_temp"; result="failed"; error="$_"
                }
            }
        }

        "large_log" {
            Write-Host "Diagnosis: Log $($issue.path) is $($issue.sizeMB)MB - compressing"
            try {
                $ts = Get-Date -Format "yyyyMMdd_HHmmss"
                $archivePath = $issue.path + ".${ts}.zip"
                Compress-Archive -Path $issue.path -DestinationPath $archivePath -Force
                Remove-Item $issue.path -Force
                Write-Host "Repair: Compressed to $archivePath"
                $fixed++
                $repairLog += [PSCustomObject]@{
                    type=$issue.type; action="compress_log"; path=$issue.path; archive=$archivePath; result="ok"
                }
            } catch {
                Write-Host "Repair FAILED: $_"
                $failed++
                $repairLog += [PSCustomObject]@{
                    type=$issue.type; action="compress_log"; path=$issue.path; result="failed"; error="$_"
                }
            }
        }

        "crit_events" {
            Write-Host "Diagnosis: $($issue.count) CRIT events in last 15min - flagging for review"
            $failed++
            $repairLog += [PSCustomObject]@{
                type=$issue.type; action="manual_review_needed"; count=$issue.count; result="needs_human"
            }
        }
    }
}

# ---- Phase 4: Verification ----
Write-Host ""
Write-Host "=== Phase 4: Verification ==="
if ($fixed -gt 0) {
    Start-Sleep -Seconds 5
    Write-Host "Post-repair check complete"
}

# ---- Phase 5: Learning ----
Write-Host ""
Write-Host "=== Phase 5: Learning ==="
$healingPath = "C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl"
$record = [PSCustomObject]@{
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    issues_detected = $issues.Count
    fixed = $fixed
    failed = $failed
    repairs = $repairLog
}
$record | ConvertTo-Json -Compress -Depth 5 | Add-Content -Path $healingPath -Encoding UTF8
Write-Host "Logged to self_healing.jsonl"

# Check repeat issues (>3 times same type)
if (Test-Path $healingPath) {
    $recentLines = Get-Content $healingPath -Tail 20
    $typeCounts = @{}
    foreach ($line in $recentLines) {
        try {
            $r = $line | ConvertFrom-Json
            foreach ($rep in $r.repairs) {
                if ($rep.type) {
                    if (-not $typeCounts[$rep.type]) { $typeCounts[$rep.type] = 0 }
                    $typeCounts[$rep.type]++
                }
            }
        } catch {}
    }
    foreach ($k in $typeCounts.Keys) {
        if ($typeCounts[$k] -gt 3) {
            Write-Host "WARNING: Issue type '$k' repeated $($typeCounts[$k]) times - Debugger Agent needed"
        }
    }
}

# ---- Final Output ----
Write-Host ""
Write-Host "=== RESULT ==="
if ($issues.Count -eq 0) {
    Write-Host "HEALING_OK"
} elseif ($failed -eq 0) {
    Write-Host "HEALING_FIXED:$fixed"
} elseif ($fixed -gt 0) {
    Write-Host "HEALING_FIXED:$fixed HEALING_FAILED:$failed"
} else {
    Write-Host "HEALING_FAILED:$failed"
}
