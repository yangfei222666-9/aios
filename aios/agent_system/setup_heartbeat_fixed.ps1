# AIOS Heartbeat - Fixed Version (4 daily triggers)
# Run as Administrator

$taskName = "AIOS Heartbeat"
$scriptPath = "C:\Users\A\.openclaw\workspace\aios\agent_system\run_heartbeat.ps1"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

$trigger1 = New-ScheduledTaskTrigger -Daily -At "00:00"
$trigger2 = New-ScheduledTaskTrigger -Daily -At "06:00"
$trigger3 = New-ScheduledTaskTrigger -Daily -At "12:00"
$trigger4 = New-ScheduledTaskTrigger -Daily -At "18:00"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger @($trigger1,$trigger2,$trigger3,$trigger4) `
        -Principal $principal `
        -Settings $settings `
        -Description "AIOS Heartbeat - 4 times daily" `
        -ErrorAction Stop

    Write-Host "[SUCCESS] REGISTER_OK"
    Write-Host ""
    Write-Host "Task registered. Verifying..."
    Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State
    Get-ScheduledTaskInfo -TaskName $taskName | Format-List LastRunTime, NextRunTime
} catch {
    Write-Host "[ERROR] REGISTER_FAIL"
    Write-Host $_.Exception.Message
}
