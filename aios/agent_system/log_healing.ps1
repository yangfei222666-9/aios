$timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
$record = @{
    timestamp = $timestamp
    status = 'HEALTHY'
    issues_detected = 0
    issues_fixed = 0
    checks = @{
        processes = @{
            node = 1
            python = 4
        }
        resources = @{
            memory_percent = 50.2
            cpu_percent = 50
        }
        disk = @{
            C = 70.8
            D = 9.2
            E = 24.6
            G = 1.3
        }
        logs = @{
            events_mb = 0.1
            metrics_mb = 0
        }
        crit_events = 0
    }
} | ConvertTo-Json -Compress

$logFile = 'C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl'
if (-not (Test-Path (Split-Path $logFile))) {
    New-Item -ItemType Directory -Path (Split-Path $logFile) -Force | Out-Null
}
Add-Content -Path $logFile -Value $record
Write-Host "✓ Logged to self_healing.jsonl"
