# TaijiOS MacBook Backup Script v1.0
# Date: 2026-03-10
# Purpose: Package essential content for MacBook backup

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$WorkspaceRoot = "C:\Users\A\.openclaw\workspace"
$BackupDate = Get-Date -Format "yyyy-MM-dd"
$BackupDir = "$WorkspaceRoot\backup_$BackupDate"
$BackupZip = "$WorkspaceRoot\TaijiOS-Backup-$BackupDate.zip"

Write-Host "=== TaijiOS MacBook Backup ===" -ForegroundColor Cyan
Write-Host "Date: $BackupDate" -ForegroundColor Gray
Write-Host ""

# Create temp backup directory
if (Test-Path $BackupDir) {
    Write-Host "Cleaning old backup directory..." -ForegroundColor Yellow
    Remove-Item $BackupDir -Recurse -Force
}
New-Item -ItemType Directory -Path $BackupDir | Out-Null

# 1. Copy essential directories
Write-Host "[1/3] Copying essential directories..." -ForegroundColor Green

$MustBackupDirs = @(
    "docs",
    "memory",
    "aios\agent_system\data",
    "aios\agent_system",
    "skill_auto_creation",
    "aios",
    "skills",
    "tests",
    "scripts",
    "research",
    "reports"
)

foreach ($dir in $MustBackupDirs) {
    $sourcePath = Join-Path $WorkspaceRoot $dir
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $BackupDir $dir
        Write-Host "  Copying $dir..." -ForegroundColor Gray
        Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
    } else {
        Write-Host "  Skipping $dir (not found)" -ForegroundColor DarkGray
    }
}

# 2. Copy essential files
Write-Host "[2/3] Copying essential files..." -ForegroundColor Green

$MustBackupFiles = @(
    "AGENTS.md",
    "SOUL.md",
    "USER.md",
    "IDENTITY.md",
    "TOOLS.md",
    "HEARTBEAT.md",
    "MEMORY.md",
    "BACKUP_CHECKLIST.md"
)

foreach ($file in $MustBackupFiles) {
    $sourcePath = Join-Path $WorkspaceRoot $file
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $BackupDir $file
        Write-Host "  Copying $file..." -ForegroundColor Gray
        Copy-Item -Path $sourcePath -Destination $destPath -Force
    } else {
        Write-Host "  Skipping $file (not found)" -ForegroundColor DarkGray
    }
}

# 3. Git history (if exists)
$gitPath = Join-Path $WorkspaceRoot ".git"
if (Test-Path $gitPath) {
    Write-Host "  Copying .git/ (Git history)..." -ForegroundColor Gray
    Copy-Item -Path $gitPath -Destination (Join-Path $BackupDir ".git") -Recurse -Force
} else {
    Write-Host "  Skipping .git/ (not found)" -ForegroundColor DarkGray
}

# 4. Create backup info file
Write-Host "[3/3] Creating backup info file..." -ForegroundColor Green

$backupInfo = "TaijiOS Backup Info`n`n"
$backupInfo += "Date: $BackupDate`n"
$backupInfo += "Source: Windows 11 Dev Machine`n"
$backupInfo += "Target: MacBook (Read-only copy)`n"
$backupInfo += "Type: Cold Backup (Archive)`n`n"
$backupInfo += "Content:`n"
$backupInfo += "- Design assets (docs/)`n"
$backupInfo += "- Memory assets (memory/)`n"
$backupInfo += "- Runtime assets (aios/agent_system/data/)`n"
$backupInfo += "- System assets (aios/agent_system/)`n"
$backupInfo += "- Skill auto-creation project (skill_auto_creation/)`n"
$backupInfo += "- Project source (aios/)`n"
$backupInfo += "- Git history (.git/)`n"
$backupInfo += "- Skills directory (skills/)`n"
$backupInfo += "- Test files (tests/)`n"
$backupInfo += "- Script tools (scripts/)`n"
$backupInfo += "- Config files (AGENTS.md, SOUL.md, etc.)`n"
$backupInfo += "- Research materials (research/)`n"
$backupInfo += "- Reports (reports/)`n`n"

Set-Content -Path (Join-Path $BackupDir "BACKUP_INFO.txt") -Value $backupInfo -Encoding UTF8

# 5. Calculate backup size
Write-Host ""
Write-Host "Calculating backup size..." -ForegroundColor Cyan

$backupSize = (Get-ChildItem -Path $BackupDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
$backupSizeMB = [math]::Round($backupSize / 1MB, 2)
$backupFileCount = (Get-ChildItem -Path $BackupDir -Recurse -File | Measure-Object).Count

Write-Host "  Total size: $backupSizeMB MB" -ForegroundColor Gray
Write-Host "  File count: $backupFileCount" -ForegroundColor Gray

# Append stats to BACKUP_INFO.txt
Add-Content -Path (Join-Path $BackupDir "BACKUP_INFO.txt") -Value "Total size: $backupSizeMB MB"
Add-Content -Path (Join-Path $BackupDir "BACKUP_INFO.txt") -Value "File count: $backupFileCount"

# 6. Compress backup
Write-Host ""
Write-Host "Compressing backup..." -ForegroundColor Cyan

if (Test-Path $BackupZip) {
    Remove-Item $BackupZip -Force
}

Compress-Archive -Path $BackupDir -DestinationPath $BackupZip -CompressionLevel Optimal

$zipSize = (Get-Item $BackupZip).Length
$zipSizeMB = [math]::Round($zipSize / 1MB, 2)

Write-Host "  Archive: $BackupZip" -ForegroundColor Gray
Write-Host "  Compressed size: $zipSizeMB MB" -ForegroundColor Gray

# 7. Clean temp directory
Write-Host ""
Write-Host "Cleaning temp directory..." -ForegroundColor Cyan
Remove-Item $BackupDir -Recurse -Force

# 8. Done
Write-Host ""
Write-Host "=== Backup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Backup file: $BackupZip" -ForegroundColor Cyan
Write-Host "Compressed size: $zipSizeMB MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy $BackupZip to MacBook" -ForegroundColor Gray
Write-Host "2. Extract on MacBook" -ForegroundColor Gray
Write-Host "3. Verify key files are complete" -ForegroundColor Gray
Write-Host ""
