# AIOS Heartbeat 定时任务配置脚本
# 需要管理员权限运行

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Need admin rights. Right-click and Run as Administrator."
    pause
    exit 1
}

$scriptPath = "C:\Users\A\.openclaw\workspace\aios\agent_system\run_heartbeat.ps1"
$taskName = "AIOS Heartbeat"

# 删除旧任务（如果存在）
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 创建触发器：每 6 小时执行一次
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6)

# 创建动作
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-ExecutionPolicy Bypass -WindowStyle Hidden -File `"" + $scriptPath + "`"")

# 创建设置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false

# 创建主体（SYSTEM 账户）
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# 注册任务
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "AIOS Heartbeat - Every 6 hours" | Out-Null

Write-Host "[SUCCESS] Task created: $taskName"
Write-Host "[INFO] Trigger: Every 6 hours"
Write-Host "[INFO] Next run: $(Get-Date)"

# 验证任务
$task = Get-ScheduledTask -TaskName $taskName
Write-Host "[INFO] Task state: $($task.State)"

# 询问是否立即测试
$test = Read-Host "`nRun now for testing? (Y/N)"
if ($test -eq "Y" -or $test -eq "y") {
    Write-Host "[INFO] Starting task..."
    Start-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 3
    Write-Host "[INFO] Check heartbeat.log for results"
}

pause
