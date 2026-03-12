# Run as Administrator
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\A\.openclaw\workspace\aios\agent_system\run_heartbeat.ps1"'
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Unregister-ScheduledTask -TaskName "AIOS Heartbeat" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName "AIOS Heartbeat" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "AIOS Heartbeat - Every 6 hours"
Write-Host "Task created successfully"
Get-ScheduledTask -TaskName "AIOS Heartbeat"
