# Daily Incremental Backup Script
param(
    [string]$BackupRoot = "C:\Users\A\.openclaw\backups",
    [string]$WorkspaceRoot = "C:\Users\A\.openclaw\workspace"
)

$StartTime = Get-Date
$DateStr = Get-Date -Format "yyyy-MM-dd"
$BackupDir = Join-Path $BackupRoot $DateStr

# Source directories
$SourceDirs = @(
    "$WorkspaceRoot\aios\data",
    "$WorkspaceRoot\aios\agent_system\data",
    "$WorkspaceRoot\memory",
    "$WorkspaceRoot\models"
)

# Create backup directory
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# Today's date range
$Today = (Get-Date).Date
$Tomorrow = $Today.AddDays(1)

# Statistics
$TotalFiles = 0
$TotalSize = 0
$BackedUpFiles = @()

Write-Host "=== Incremental Backup Started ===" -ForegroundColor Cyan
Write-Host "Date: $DateStr"
Write-Host "Target: $BackupDir`n"

foreach ($SourceDir in $SourceDirs) {
    if (-not (Test-Path $SourceDir)) {
        Write-Host "[SKIP] $SourceDir (not found)" -ForegroundColor Yellow
        continue
    }

    Write-Host "[SCAN] $SourceDir" -ForegroundColor Green

    $ModifiedFiles = Get-ChildItem -Path $SourceDir -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $Today -and $_.LastWriteTime -lt $Tomorrow }

    foreach ($File in $ModifiedFiles) {
        $RelativePath = $File.FullName.Substring($WorkspaceRoot.Length + 1)
        $DestPath = Join-Path $BackupDir $RelativePath
        $DestDir = Split-Path $DestPath -Parent

        if (-not (Test-Path $DestDir)) {
            New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
        }

        Copy-Item -Path $File.FullName -Destination $DestPath -Force
        
        $TotalFiles++
        $TotalSize += $File.Length
        $BackedUpFiles += $RelativePath
    }
}

$EndTime = Get-Date
$Duration = ($EndTime - $StartTime).TotalSeconds
$SizeMB = [math]::Round($TotalSize / 1MB, 2)

# Generate report
$ReportPath = Join-Path $BackupDir "backup_report.txt"
$Report = "=== Incremental Backup Report ===`n"
$Report += "Date: $DateStr`n"
$Report += "Start: $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))`n"
$Report += "End: $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))`n"
$Report += "Duration: $([math]::Round($Duration, 2)) seconds`n`n"
$Report += "Statistics:`n"
$Report += "- Files: $TotalFiles`n"
$Report += "- Size: $SizeMB MB`n"
$Report += "- Location: $BackupDir`n`n"
$Report += "Files backed up:`n"
$Report += ($BackedUpFiles -join "`n")
$Report += "`n`nStatus: SUCCESS"

$Report | Out-File -FilePath $ReportPath -Encoding UTF8

Write-Host "`n=== Backup Complete ===" -ForegroundColor Cyan
Write-Host "Files: $TotalFiles"
Write-Host "Size: $SizeMB MB"
Write-Host "Duration: $([math]::Round($Duration, 2)) seconds"
Write-Host "Report: $ReportPath"

# Log to agent logger
$LoggerScript = "$WorkspaceRoot\aios\core\agent_logger.py"
if (Test-Path $LoggerScript) {
    $TempPy = Join-Path $env:TEMP "backup_log.py"
    $LogMsg = "Backup: $TotalFiles files, $SizeMB MB, $([math]::Round($Duration, 2))s"
    
    @"
import sys
sys.path.insert(0, r'$WorkspaceRoot\aios\core')
from agent_logger import log_agent_action
log_agent_action('backup', '$LogMsg', {'files': $TotalFiles, 'size_mb': $SizeMB, 'duration_sec': $Duration})
"@ | Out-File -FilePath $TempPy -Encoding UTF8
    
    python $TempPy 2>$null
    Remove-Item $TempPy -ErrorAction SilentlyContinue
}

Write-Output "SUCCESS|$TotalFiles|$SizeMB|$Duration"
