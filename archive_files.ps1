# Project File Auto-Archive Script
# Function: Scan temporary files and archive to date-classified directories

param(
    [string]$WorkspacePath = "C:\Users\A\.openclaw\workspace",
    [int]$DaysOld = 7
)

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

# Archive target directory
$ArchiveDate = Get-Date -Format "yyyy-MM-dd"
$ArchiveDir = Join-Path $WorkspacePath "archive\$ArchiveDate"

# Create archive directory
if (-not (Test-Path $ArchiveDir)) {
    New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null
}

# Define temporary file patterns
$TempExtensions = @("*.tmp", "*.log", "*.bak")
$TestFilePatterns = @("*test*.py", "*test*.js", "*debug*.py", "*debug*.txt")

# Statistics variables
$ArchivedFiles = @()
$TotalSize = 0
$ErrorCount = 0

Write-Host "Starting file archive scan..." -ForegroundColor Cyan
Write-Host "Workspace: $WorkspacePath"
Write-Host "Archive Dir: $ArchiveDir"
Write-Host "Keep Days: $DaysOld days"
Write-Host ""

# Scan temporary files (.tmp, .log, .bak)
foreach ($ext in $TempExtensions) {
    try {
        $files = Get-ChildItem -Path $WorkspacePath -Filter $ext -Recurse -File -ErrorAction SilentlyContinue |
                 Where-Object { $_.FullName -notlike "*\archive\*" }
        
        foreach ($file in $files) {
            try {
                $TotalSize += $file.Length
                $RelativePath = $file.FullName.Substring($WorkspacePath.Length + 1)
                $TargetPath = Join-Path $ArchiveDir $RelativePath
                $TargetDir = Split-Path $TargetPath -Parent
                
                if (-not (Test-Path $TargetDir)) {
                    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
                }
                
                Move-Item -Path $file.FullName -Destination $TargetPath -Force
                $ArchivedFiles += @{
                    Path = $RelativePath
                    Size = $file.Length
                    Type = "temp"
                }
                Write-Host "[OK] Archived: $RelativePath" -ForegroundColor Green
            }
            catch {
                $ErrorCount++
                Write-Host "[FAIL] $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "Error scanning $ext : $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Scan test files older than N days
$CutoffDate = (Get-Date).AddDays(-$DaysOld)
foreach ($pattern in $TestFilePatterns) {
    try {
        $files = Get-ChildItem -Path $WorkspacePath -Filter $pattern -Recurse -File -ErrorAction SilentlyContinue |
                 Where-Object { 
                     $_.LastWriteTime -lt $CutoffDate -and 
                     $_.FullName -notlike "*\archive\*" -and
                     $_.FullName -notlike "*\node_modules\*" -and
                     $_.FullName -notlike "*\.git\*"
                 }
        
        foreach ($file in $files) {
            try {
                $TotalSize += $file.Length
                $RelativePath = $file.FullName.Substring($WorkspacePath.Length + 1)
                $TargetPath = Join-Path $ArchiveDir $RelativePath
                $TargetDir = Split-Path $TargetPath -Parent
                
                if (-not (Test-Path $TargetDir)) {
                    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
                }
                
                Move-Item -Path $file.FullName -Destination $TargetPath -Force
                $ArchivedFiles += @{
                    Path = $RelativePath
                    Size = $file.Length
                    Type = "old_test"
                    LastModified = $file.LastWriteTime.ToString("yyyy-MM-dd")
                }
                Write-Host "[OK] Archived: $RelativePath (older than $DaysOld days)" -ForegroundColor Green
            }
            catch {
                $ErrorCount++
                Write-Host "[FAIL] $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "Error scanning $pattern : $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Calculate duration
$Duration = (Get-Date) - $StartTime
$DurationSec = [math]::Round($Duration.TotalSeconds, 2)

# Generate archive report
$Report = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    archive_date = $ArchiveDate
    workspace = $WorkspacePath
    archive_dir = $ArchiveDir
    files_count = $ArchivedFiles.Count
    total_size_bytes = $TotalSize
    total_size_mb = [math]::Round($TotalSize / 1MB, 2)
    duration_sec = $DurationSec
    error_count = $ErrorCount
    files = $ArchivedFiles
}

$ReportPath = Join-Path $ArchiveDir "archive_report.json"
$Report | ConvertTo-Json -Depth 10 | Out-File -FilePath $ReportPath -Encoding UTF8

# Output summary
Write-Host ""
Write-Host "==================== Archive Complete ====================" -ForegroundColor Cyan
Write-Host "Files Archived: $($ArchivedFiles.Count)" -ForegroundColor White
Write-Host "Total Size: $([math]::Round($TotalSize / 1MB, 2)) MB" -ForegroundColor White
Write-Host "Duration: $DurationSec seconds" -ForegroundColor White
Write-Host "Errors: $ErrorCount" -ForegroundColor $(if ($ErrorCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "Report: $ReportPath" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan

# Log to Agent system
try {
    $PythonPath = "python"
    $LoggerScript = Join-Path $WorkspacePath "aios\agent_system\agent_logger.py"
    
    if (Test-Path $LoggerScript) {
        # Create temporary log data
        $LogData = @{
            task_id = "archive_$ArchiveDate"
            task_type = "file_archive"
            success = ($ErrorCount -eq 0)
            duration_sec = $DurationSec
            human_intervention = $false
            notes = "Archived $($ArchivedFiles.Count) files, total size $([math]::Round($TotalSize / 1MB, 2)) MB"
        }
        
        # Use Python to log
        $LogJson = $LogData | ConvertTo-Json -Compress
        $PythonCode = @"
import sys
import json
sys.path.insert(0, r'$WorkspacePath')
from aios.agent_system.agent_logger import AgentLogger
logger = AgentLogger()
logger.log_task('automation_archive', $LogJson)
print('Log recorded')
"@
        
        $PythonCode | & $PythonPath -c "exec(input())"
        Write-Host "[OK] Logged to Agent system" -ForegroundColor Green
    }
}
catch {
    Write-Host "[WARN] Agent logging failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Return status code
if ($ErrorCount -eq 0) {
    exit 0
} else {
    exit 1
}
