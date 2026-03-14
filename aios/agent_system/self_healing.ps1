# AIOS Self-Healing Agent
# 完整闭环：检测 → 诊断 → 修复 → 验证 → 学习

param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = 'Continue'
$timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
$issues = @()
$fixes = @()

Write-Host "=== AIOS Self-Healing Agent ===" -ForegroundColor Cyan
Write-Host "Time: $timestamp"
if ($DryRun) { Write-Host "Mode: DRY RUN (no actions will be taken)" -ForegroundColor Yellow }
Write-Host ""

# ============================================
# Phase 1: Detection
# ============================================
Write-Host "Phase 1: Detection" -ForegroundColor Green

# 1.1 进程检查
$nodeProcs = Get-Process node* -ErrorAction SilentlyContinue
$pythonProcs = Get-Process python* -ErrorAction SilentlyContinue

if (-not $nodeProcs) {
    $issue = @{
        type = 'process_down'
        severity = 'CRITICAL'
        target = 'OpenClaw Gateway'
        message = 'OpenClaw Gateway process not running'
    }
    $issues += $issue
}

# 1.2 资源检查
$mem = Get-CimInstance Win32_OperatingSystem
$memUsedGB = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / 1MB, 2)
$memTotalGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
$memPercent = [math]::Round(($memUsedGB / $memTotalGB) * 100, 1)

if ($memPercent -gt 85) {
    $issue = @{
        type = 'high_memory'
        severity = 'WARNING'
        target = 'System'
        message = "Memory usage critical: $memPercent%"
        value = $memPercent
    }
    $issues += $issue
}

$cpu = Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average
$cpuPercent = [math]::Round($cpu.Average, 1)

if ($cpuPercent -gt 80) {
    $issue = @{
        type = 'high_cpu'
        severity = 'WARNING'
        target = 'System'
        message = "CPU usage high: $cpuPercent%"
        value = $cpuPercent
    }
    $issues += $issue
}

# 1.3 磁盘检查
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -gt 0 } | ForEach-Object {
    $usedGB = [math]::Round($_.Used / 1GB, 2)
    $freeGB = [math]::Round($_.Free / 1GB, 2)
    $totalGB = $usedGB + $freeGB
    $percent = [math]::Round(($usedGB / $totalGB) * 100, 1)
    
    if ($percent -gt 90) {
        $issue = @{
            type = 'disk_full'
            severity = 'CRITICAL'
            target = "Disk $($_.Name)"
            message = "Disk $($_.Name) usage critical: $percent%"
            value = $percent
        }
        $issues += $issue
    }
}

# 1.4 日志文件检查
$eventsFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\events.jsonl'
$metricsFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\metrics.jsonl'

if (Test-Path $eventsFile) {
    $size = (Get-Item $eventsFile).Length
    if ($size -gt 100MB) {
        $issue = @{
            type = 'log_too_large'
            severity = 'WARNING'
            target = 'events.jsonl'
            message = "events.jsonl too large: $([math]::Round($size / 1MB, 2)) MB"
            value = $size
        }
        $issues += $issue
    }
}

if (Test-Path $metricsFile) {
    $size = (Get-Item $metricsFile).Length
    if ($size -gt 100MB) {
        $issue = @{
            type = 'log_too_large'
            severity = 'WARNING'
            target = 'metrics.jsonl'
            message = "metrics.jsonl too large: $([math]::Round($size / 1MB, 2)) MB"
            value = $size
        }
        $issues += $issue
    }
}

# 1.5 CRIT 事件检查
if (Test-Path $eventsFile) {
    $cutoff = (Get-Date).AddMinutes(-15).ToString('yyyy-MM-ddTHH:mm:ss')
    $critEvents = @()
    Get-Content $eventsFile -Tail 500 | ForEach-Object {
        try {
            $evt = $_ | ConvertFrom-Json
            if ($evt.level -eq 'CRIT' -and $evt.timestamp -gt $cutoff) {
                $critEvents += $evt
            }
        } catch {}
    }
    
    if ($critEvents.Count -gt 0) {
        $issue = @{
            type = 'crit_events'
            severity = 'WARNING'
            target = 'Event Log'
            message = "$($critEvents.Count) CRIT events in last 15 minutes"
            value = $critEvents.Count
        }
        $issues += $issue
    }
}

Write-Host "✓ Detection complete: $($issues.Count) issues found" -ForegroundColor $(if ($issues.Count -eq 0) { 'Green' } else { 'Yellow' })

if ($issues.Count -eq 0) {
    Write-Host "`n✓ All systems healthy - HEALING_OK" -ForegroundColor Green
    
    # 记录健康状态
    $record = New-Object PSObject -Property @{
        timestamp = $timestamp
        status = 'HEALTHY'
        issues_detected = 0
        issues_fixed = 0
    }
    $recordJson = $record | ConvertTo-Json -Compress
    
    $logFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl'
    Add-Content -Path $logFile -Value $recordJson
    
    exit 0
}

# ============================================
# Phase 2: Diagnosis
# ============================================
Write-Host "`nPhase 2: Diagnosis" -ForegroundColor Green

foreach ($issue in $issues) {
    Write-Host "⚠️ [$($issue.severity)] $($issue.message)" -ForegroundColor Yellow
}

# ============================================
# Phase 3: Repair
# ============================================
Write-Host "`nPhase 3: Repair" -ForegroundColor Green

foreach ($issue in $issues) {
    $fixed = $false
    
    switch ($issue.type) {
        'process_down' {
            if (-not $DryRun) {
                Write-Host "→ Attempting to restart OpenClaw Gateway..."
                try {
                    # 尝试重启 Gateway
                    Start-Process "openclaw" -ArgumentList "gateway", "restart" -NoNewWindow -Wait
                    Start-Sleep -Seconds 5
                    $nodeProcs = Get-Process node* -ErrorAction SilentlyContinue
                    if ($nodeProcs) {
                        Write-Host "✓ OpenClaw Gateway restarted successfully" -ForegroundColor Green
                        $fixed = $true
                    }
                } catch {
                    Write-Host "✗ Failed to restart: $_" -ForegroundColor Red
                }
            } else {
                Write-Host "[DRY RUN] Would restart OpenClaw Gateway"
            }
        }
        
        'high_memory' {
            Write-Host "→ High memory detected, checking for memory leaks..."
            # 识别内存占用最高的进程
            $topProcs = Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5
            foreach ($proc in $topProcs) {
                $memMB = [math]::Round($proc.WorkingSet / 1MB, 2)
                Write-Host "  - $($proc.Name): $memMB MB"
            }
            Write-Host "ℹ️ Manual intervention may be required" -ForegroundColor Cyan
        }
        
        'high_cpu' {
            Write-Host "→ High CPU detected, checking processes..."
            $topProcs = Get-Process | Sort-Object CPU -Descending | Select-Object -First 5
            foreach ($proc in $topProcs) {
                Write-Host "  - $($proc.Name): $([math]::Round($proc.CPU, 2))s"
            }
            Write-Host "ℹ️ Manual intervention may be required" -ForegroundColor Cyan
        }
        
        'disk_full' {
            if (-not $DryRun) {
                Write-Host "→ Cleaning temporary files..."
                try {
                    # 清理 Windows Temp
                    $tempPath = $env:TEMP
                    $before = (Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
                    Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
                    $after = (Get-ChildItem $tempPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
                    $cleaned = [math]::Round(($before - $after) / 1MB, 2)
                    Write-Host "✓ Cleaned $cleaned MB from temp files" -ForegroundColor Green
                    $fixed = $true
                } catch {
                    Write-Host "✗ Failed to clean temp: $_" -ForegroundColor Red
                }
            } else {
                Write-Host "[DRY RUN] Would clean temporary files"
            }
        }
        
        'log_too_large' {
            if (-not $DryRun) {
                Write-Host "→ Compressing large log file: $($issue.target)..."
                try {
                    $logPath = if ($issue.target -eq 'events.jsonl') { $eventsFile } else { $metricsFile }
                    $archivePath = "$logPath.$timestamp.zip"
                    Compress-Archive -Path $logPath -DestinationPath $archivePath -Force
                    Remove-Item $logPath -Force
                    New-Item $logPath -ItemType File | Out-Null
                    Write-Host "✓ Compressed and reset $($issue.target)" -ForegroundColor Green
                    $fixed = $true
                } catch {
                    Write-Host "✗ Failed to compress log: $_" -ForegroundColor Red
                }
            } else {
                Write-Host "[DRY RUN] Would compress $($issue.target)"
            }
        }
        
        'crit_events' {
            Write-Host "→ $($issue.value) CRIT events detected - review required"
            Write-Host "ℹ️ Check events.jsonl for details" -ForegroundColor Cyan
        }
    }
    
    if ($fixed) {
        $fixes += $issue
    }
}

# ============================================
# Phase 4: Verification
# ============================================
if ($fixes.Count -gt 0 -and -not $DryRun) {
    Write-Host "`nPhase 4: Verification" -ForegroundColor Green
    Write-Host "Waiting 30 seconds for systems to stabilize..."
    Start-Sleep -Seconds 30
    
    # 重新检查
    Write-Host "Re-checking fixed issues..."
    foreach ($fix in $fixes) {
        switch ($fix.type) {
            'process_down' {
                $nodeProcs = Get-Process node* -ErrorAction SilentlyContinue
                if ($nodeProcs) {
                    Write-Host "✓ OpenClaw Gateway is running" -ForegroundColor Green
                } else {
                    Write-Host "✗ OpenClaw Gateway still down - FAILED" -ForegroundColor Red
                }
            }
        }
    }
}

# ============================================
# Phase 5: Learning
# ============================================
Write-Host "`nPhase 5: Learning" -ForegroundColor Green

$record = @{
    timestamp = $timestamp
    status = if ($fixes.Count -eq $issues.Count) { 'FIXED' } elseif ($fixes.Count -gt 0) { 'PARTIAL' } else { 'FAILED' }
    issues_detected = $issues.Count
    issues_fixed = $fixes.Count
    issues = $issues
    fixes = $fixes
} | ConvertTo-Json -Compress -Depth 10

$logFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl'
if (-not (Test-Path (Split-Path $logFile))) {
    New-Item -ItemType Directory -Path (Split-Path $logFile) -Force | Out-Null
}
Add-Content -Path $logFile -Value $record

Write-Host "✓ Logged to self_healing.jsonl"

# 检查重复问题
$recentRecords = Get-Content $logFile -Tail 10 | ForEach-Object { $_ | ConvertFrom-Json }
$issueTypes = $issues | ForEach-Object { $_.type }
foreach ($type in $issueTypes) {
    $count = ($recentRecords | Where-Object { $_.issues.type -contains $type }).Count
    if ($count -ge 3) {
        Write-Host "⚠️ Issue '$type' occurred $count times recently - consider deeper analysis" -ForegroundColor Yellow
    }
}

# ============================================
# Summary
# ============================================
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Issues detected: $($issues.Count)"
Write-Host "Issues fixed: $($fixes.Count)"

if ($fixes.Count -eq $issues.Count -and $issues.Count -gt 0) {
    Write-Host "`n✓ HEALING_FIXED:$($fixes.Count)" -ForegroundColor Green
    exit 0
} elseif ($fixes.Count -gt 0) {
    Write-Host "`n⚠️ HEALING_PARTIAL:$($fixes.Count)/$($issues.Count)" -ForegroundColor Yellow
    exit 1
} elseif ($issues.Count -gt 0) {
    Write-Host "`n✗ HEALING_FAILED:$($issues.Count)" -ForegroundColor Red
    exit 2
} else {
    Write-Host "`n✓ HEALING_OK" -ForegroundColor Green
    exit 0
}
