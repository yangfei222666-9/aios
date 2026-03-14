[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Phase 2: Diagnosis ==="

# Node process 1709MB - 诊断
Write-Host "`n--- Node Process Diagnosis ---"
$nodeProc = Get-Process node -ErrorAction SilentlyContinue | Sort-Object WorkingSet64 -Descending | Select-Object -First 1
if ($nodeProc) {
    $memMB = [math]::Round($nodeProc.WorkingSet64 / 1MB, 2)
    Write-Host "PID: $($nodeProc.Id)"
    Write-Host "Memory: ${memMB}MB"
    Write-Host "CPU Time: $($nodeProc.CPU)s"
    Write-Host "Start Time: $($nodeProc.StartTime)"
    
    # 获取命令行
    $wmi = Get-WmiObject Win32_Process -Filter "ProcessId = $($nodeProc.Id)" -ErrorAction SilentlyContinue
    if ($wmi) {
        Write-Host "CommandLine: $($wmi.CommandLine)"
    }
    
    # 判断是否异常
    if ($memMB -gt 1500) {
        Write-Host "STATUS: HIGH_MEMORY - ${memMB}MB exceeds 1500MB threshold"
        $isOpenClaw = $wmi.CommandLine -like "*openclaw*"
        Write-Host "Is OpenClaw: $isOpenClaw"
    }
}

# 检查 Dashboard 进程
Write-Host "`n--- Dashboard Process Check ---"
$dashProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.WorkingSet64 -gt 50MB }
if ($dashProcs) {
    foreach ($p in $dashProcs) {
        $wmi = Get-WmiObject Win32_Process -Filter "ProcessId = $($p.Id)" -ErrorAction SilentlyContinue
        Write-Host "PID $($p.Id): $([math]::Round($p.WorkingSet64/1MB,2))MB - $($wmi.CommandLine)"
    }
} else {
    Write-Host "No large Python processes"
}

# 检查 Dashboard 端口
Write-Host "`n--- Dashboard Port Check ---"
$ports = @(8888, 8889, 7788)
foreach ($port in $ports) {
    $conn = netstat -ano | Select-String ":$port " | Select-String "LISTENING"
    if ($conn) {
        Write-Host "Port ${port}: LISTENING"
    } else {
        Write-Host "Port ${port}: NOT LISTENING"
    }
}

Write-Host "`n=== Diagnosis Complete ==="
