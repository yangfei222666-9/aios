$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Need admin rights. Right-click and Run as Administrator."
    pause
    exit 1
}

$scriptPath = "C:\Users\A\.openclaw\workspace\aios\agent_system\start_memory_server.ps1"
$taskName = "AIOS Memory Server"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-ExecutionPolicy Bypass -WindowStyle Hidden -File `"" + $scriptPath + "`"")
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Auto-start AIOS Memory Server" | Out-Null

Write-Host "OK: Scheduled task created - $taskName"
Write-Host "Memory Server will auto-start on next boot."

pause
