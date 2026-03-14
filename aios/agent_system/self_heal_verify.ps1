[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Phase 4: Verification ==="

# 检查关键服务是否健康
Write-Host "`n--- Service Health Check ---"

# 1. Memory Server
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:7788/status" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Memory Server (7788): OK"
    }
} catch {
    Write-Host "Memory Server (7788): FAILED - $_"
}

# 2. Dashboard v3.4
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8888" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Dashboard v3.4 (8888): OK"
    }
} catch {
    Write-Host "Dashboard v3.4 (8888): FAILED - $_"
}

# 3. Dashboard v4.0
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8889" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Dashboard v4.0 (8889): OK"
    }
} catch {
    Write-Host "Dashboard v4.0 (8889): FAILED - $_"
}

# 4. 检查磁盘空间是否健康
Write-Host "`n--- Disk Health ---"
$cDrive = Get-PSDrive C
$pct = [math]::Round(($cDrive.Used / ($cDrive.Used + $cDrive.Free)) * 100, 2)
if ($pct -lt 90) {
    Write-Host "C: Drive: OK (${pct}% used)"
} else {
    Write-Host "C: Drive: WARNING (${pct}% used)"
}

# 5. 检查是否有僵尸进程
Write-Host "`n--- Zombie Process Check ---"
$zombies = Get-Process | Where-Object { $_.Responding -eq $false }
if ($zombies) {
    Write-Host "Found $($zombies.Count) non-responding processes:"
    $zombies | Select-Object Name, Id | Format-Table
} else {
    Write-Host "No zombie processes detected"
}

Write-Host "`n=== Verification Complete ==="
