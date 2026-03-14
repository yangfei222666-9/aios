[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Phase 5: Learning - 记录本次自愈结果
$healingRecord = @{
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    run_id = [System.Guid]::NewGuid().ToString()
    issues_detected = @(
        @{
            type = "HIGH_MEMORY_NODE"
            pid = 23404
            memory_mb = 1685.61
            threshold_mb = 1500
            is_openclaw = $false
            action = "MONITOR_ONLY"
            result = "SKIPPED - not OpenClaw process"
        },
        @{
            type = "ZOMBIE_PROCESS"
            name = "SystemSettings"
            pid = 35012
            action = "MONITOR_ONLY"
            result = "SKIPPED - system process, low risk"
        }
    )
    services_healthy = @("memory_server_7788", "dashboard_v34_8888", "dashboard_v40_8889")
    disk_status = @{
        C = "72.92%"
        D = "9.25%"
        E = "24.65%"
        G = "1.26%"
    }
    crit_events_15min = 0
    outcome = "HEALING_OK"
    notes = "All critical services healthy. Node high memory is non-OpenClaw process (likely VS Code or other dev tool). SystemSettings zombie is benign Windows process."
}

$jsonLine = $healingRecord | ConvertTo-Json -Compress -Depth 5
$outputPath = "C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl"

# 确保目录存在
$dir = Split-Path $outputPath
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

Add-Content -Path $outputPath -Value $jsonLine -Encoding UTF8
Write-Host "Recorded to self_healing.jsonl"

# 检查重复问题次数
$repeatCount = 0
if (Test-Path $outputPath) {
    $repeatCount = (Get-Content $outputPath | ConvertFrom-Json -ErrorAction SilentlyContinue | 
        Where-Object { $_.issues_detected | Where-Object { $_.type -eq "HIGH_MEMORY_NODE" } }).Count
    Write-Host "HIGH_MEMORY_NODE occurrence count: $repeatCount"
    if ($repeatCount -gt 3) {
        Write-Host "TRIGGER: Debugger Agent needed for deep analysis"
    }
}

Write-Host "=== Phase 5: Learning Complete ==="
Write-Host "HEALING_OK"
