# ============================================================================
# Windows Scheduled Task Setup Script
# ============================================================================
# Features:
#   - Create scheduled task named WeatherCrawler_Daily
#   - Execute daily at 08:00
#   - Retry on failure (max 3 times, 10 min interval)
#   - Requires Administrator privileges
# ============================================================================

param(
    [string]$TaskName = "WeatherCrawler_Daily",
    [string]$ExecutionTime = "08:00",
    [string]$City = "Beijing"
)

# Check administrator privileges
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Startup script path
$RunScript = Join-Path $ScriptDir "run_weather_crawler.ps1"

# Check if startup script exists
if (-not (Test-Path $RunScript)) {
    Write-Host "ERROR: Startup script not found: $RunScript" -ForegroundColor Red
    exit 1
}

Write-Host "===== Configuring Scheduled Task =====" -ForegroundColor Cyan
Write-Host "Task Name: $TaskName"
Write-Host "Execution Time: Daily at $ExecutionTime"
Write-Host "Query City: $City"
Write-Host "Startup Script: $RunScript"
Write-Host ""

try {
    # Check if task already exists
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Write-Host "WARNING: Task '$TaskName' already exists" -ForegroundColor Yellow
        $Confirm = Read-Host "Delete and recreate? (Y/N)"
        if ($Confirm -eq "Y" -or $Confirm -eq "y") {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "Old task deleted" -ForegroundColor Green
        } else {
            Write-Host "Operation cancelled" -ForegroundColor Yellow
            exit 0
        }
    }

    # Create task action
    $Action = New-ScheduledTaskAction `
        -Execute "PowerShell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`" -City $City" `
        -WorkingDirectory $ScriptDir

    # Create trigger (daily at 08:00)
    $Trigger = New-ScheduledTaskTrigger -Daily -At $ExecutionTime

    # Create task settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 10) `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -MultipleInstances IgnoreNew

    # Create task principal (use current user)
    $Principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType S4U `
        -RunLevel Limited

    # Register task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Daily weather data collection (City: $City)" | Out-Null

    Write-Host ""
    Write-Host "===== Task Created Successfully =====" -ForegroundColor Green
    Write-Host "Task Name: $TaskName"
    Write-Host "Execution Time: Daily at $ExecutionTime"
    Write-Host "Retry on Failure: Max 3 times, 10 min interval"
    Write-Host ""

    # Display task information
    $Task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "Task Status: $($Task.State)"
    Write-Host "Next Run: $((Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime)"
    Write-Host ""

    # Ask if user wants to test run
    $TestRun = Read-Host "Test run now? (Y/N)"
    if ($TestRun -eq "Y" -or $TestRun -eq "y") {
        Write-Host "Starting task..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
        
        # Check task status
        $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "Last Run Time: $($TaskInfo.LastRunTime)"
        Write-Host "Last Run Result: $($TaskInfo.LastTaskResult) (0 = success)"
        
        # Display log file location
        $LogFile = Join-Path $ScriptDir "weather_crawler.log"
        if (Test-Path $LogFile) {
            Write-Host ""
            Write-Host "View log: $LogFile" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "===== Configuration Complete =====" -ForegroundColor Green
    Write-Host "Task management commands:"
    Write-Host "  View task: Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Manual run: Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Disable: Disable-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Enable: Enable-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Delete: Unregister-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "===== Configuration Failed =====" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Details: $($_.ScriptStackTrace)" -ForegroundColor Red
    exit 1
}
