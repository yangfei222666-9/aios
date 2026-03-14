# Phase 5: Learning - Record results
$healingLog = "C:\Users\A\.openclaw\workspace\aios\agent_system\data\self_healing.jsonl"
$ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss+08:00")

$entry = @{
    timestamp = $ts
    result = "HEALING_OK"
    issues_found = 0
    issues_fixed = 0
    issues_failed = 0
    checks = @{
        processes = "OK - Node.js(1.72GB), Python(7 procs), all running"
        cpu = "OK - 38%"
        memory = "OK - 46.4% (14.45/31.16GB)"
        disk = "OK - C:73.5%, D:9.2%, E:24.6%, G:1.3%"
        logs = "OK - events.jsonl 0.09MB, data/ total 62.2MB"
        crit_events = "OK - 0 in last 15min"
        temp_folder = "OK - 104MB"
    }
    notes = @(
        "Node.js PID=23404 at 1.72GB (592MB/h avg over 2.9h uptime) - monitoring, not critical"
        "Memory server running (PID=8552,34868), voice proxy (PID=15940 188MB), dashboard servers active"
        "All systems nominal"
    )
} | ConvertTo-Json -Compress

Add-Content -Path $healingLog -Value $entry -Encoding UTF8
Write-Host "Logged to self_healing.jsonl"

# Check repeat patterns
if (Test-Path $healingLog) {
    $recentEntries = Get-Content $healingLog -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object {
        try { $_ | ConvertFrom-Json } catch {}
    }
    $failedCount = ($recentEntries | Where-Object { $_.result -like "HEALING_FAILED*" }).Count
    if ($failedCount -gt 3) {
        Write-Host "WARNING: $failedCount recent failures detected - would trigger Debugger Agent"
    } else {
        Write-Host "No repeat failure patterns detected"
    }
}

Write-Host "=== SELF-HEALING CYCLE COMPLETE ==="
