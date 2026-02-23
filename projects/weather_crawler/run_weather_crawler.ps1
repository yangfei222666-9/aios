# ============================================================================
# Weather Crawler Startup Script
# ============================================================================
# Features:
#   - Activate Python virtual environment (if exists)
#   - Run weather crawler (default: Beijing)
#   - Log to weather_crawler.log
#   - Error handling and notification
# ============================================================================

param(
    [string]$City = "Beijing",
    [string]$VenvPath = "venv"
)

# Set error handling
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Log file path
$LogFile = Join-Path $ScriptDir "weather_crawler.log"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Log function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry -Encoding UTF8
}

# Start execution
Write-Log "===== Start Weather Crawler ====="
Write-Log "Query City: $City"

try {
    # Check if Python is available
    $PythonCmd = $null
    $VenvPython = Join-Path $ScriptDir "$VenvPath\Scripts\python.exe"
    
    if (Test-Path $VenvPython) {
        # Use Python from virtual environment
        $PythonCmd = $VenvPython
        Write-Log "Using virtual environment: $VenvPath"
    } elseif (Test-Path "C:\Program Files\Python312\python.exe") {
        # Use Python 3.12
        $PythonCmd = "C:\Program Files\Python312\python.exe"
        Write-Log "Using Python 3.12"
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        # Use system Python
        $PythonCmd = (Get-Command python).Source
        Write-Log "Using system Python"
    } else {
        throw "Python interpreter not found. Please install Python or create virtual environment"
    }

    # Check if crawler script exists
    $CrawlerScript = Join-Path $ScriptDir "weather_crawler.py"
    if (-not (Test-Path $CrawlerScript)) {
        throw "Crawler script not found: $CrawlerScript"
    }

    # Execute crawler
    Write-Log "Executing: $PythonCmd $CrawlerScript --city $City"
    
    # Capture output and errors
    $process = Start-Process -FilePath $PythonCmd -ArgumentList "$CrawlerScript --city $City" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$ScriptDir\temp_output.txt" -RedirectStandardError "$ScriptDir\temp_error.txt"
    
    # Read output
    if (Test-Path "$ScriptDir\temp_output.txt") {
        $Output = Get-Content "$ScriptDir\temp_output.txt" -Raw
        Add-Content -Path $LogFile -Value $Output -Encoding UTF8
        Remove-Item "$ScriptDir\temp_output.txt" -Force
    }
    
    # Read errors
    if (Test-Path "$ScriptDir\temp_error.txt") {
        $ErrorOutput = Get-Content "$ScriptDir\temp_error.txt" -Raw
        if ($ErrorOutput) {
            Add-Content -Path $LogFile -Value $ErrorOutput -Encoding UTF8
        }
        Remove-Item "$ScriptDir\temp_error.txt" -Force
    }
    
    # Check execution result
    if ($process.ExitCode -eq 0) {
        Write-Log "Crawler executed successfully" "SUCCESS"
        
        # Check output file
        $OutputFile = Join-Path $ScriptDir "weather_data.json"
        if (Test-Path $OutputFile) {
            $FileSize = (Get-Item $OutputFile).Length
            Write-Log "Data saved: $OutputFile (Size: $FileSize bytes)"
        }
        
        exit 0
    } else {
        throw "Crawler execution failed with exit code: $($process.ExitCode)"
    }

} catch {
    # Error handling
    $ErrorMsg = $_.Exception.Message
    Write-Log "Execution failed: $ErrorMsg" "ERROR"
    Write-Log "Error details: $($_.ScriptStackTrace)" "ERROR"
    
    # Optional: Send notification (requires configuration)
    # Send-Notification -Title "Weather Crawler Failed" -Message $ErrorMsg
    
    exit 1
} finally {
    Write-Log "===== Execution Completed ====="
    Write-Log ""
}
