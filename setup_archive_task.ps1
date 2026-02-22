# Create Scheduled Task for File Archive
# Run this script as Administrator

$TaskName = "OpenClaw_FileArchive"
$ScriptPath = "C:\Users\A\.openclaw\workspace\archive_files.ps1"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task '$TaskName' already exists. Removing..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create task action
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""

# Create trigger (daily at 23:00)
$trigger = New-ScheduledTaskTrigger -Daily -At "23:00"

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" `
    -LogonType Interactive -RunLevel Highest

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

# Register task
try {
    Register-ScheduledTask -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Auto-archive temporary and old test files daily at 23:00" `
        -Force | Out-Null
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Scheduled Task Created Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Task Name: $TaskName"
    Write-Host "Schedule: Daily at 23:00"
    Write-Host "Script: $ScriptPath"
    Write-Host ""
    Write-Host "To view task: Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "To run now: Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "To remove: Unregister-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
}
catch {
    Write-Host "Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this script as Administrator:" -ForegroundColor Yellow
    Write-Host "Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    exit 1
}
