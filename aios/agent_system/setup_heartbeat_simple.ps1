# Simplified version - Run as Administrator
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-ExecutionPolicy Bypass -File "C:\Users\A\.openclaw\workspace\aios\agent_system\run_heartbeat.ps1"'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
$settings = New-ScheduledTaskSettingsSet
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Unregister-ScheduledTask -TaskName "AIOS Heartbeat" -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -TaskName "AIOS Heartbeat" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "AIOS Heartbeat - Every 6 hours"

Write-Host "`n[SUCCESS] Task registered"
Get-ScheduledTask -TaskName "AIOS Heartbeat" | Format-List TaskName, State, LastRunTime, NextRunTime
