# 太极OS 每日自动备份脚本
# 备份到 T7 移动硬盘 (G:)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd"
$logFile = "C:\Users\A\.openclaw\workspace\aios\agent_system\backup_log.txt"

function Write-Log {
    param($message)
    $time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$time - $message" | Tee-Object -FilePath $logFile -Append
}

Write-Log "========== 开始每日备份 =========="

# 检查 T7 是否连接
if (-not (Test-Path "G:\")) {
    Write-Log "错误：T7 移动硬盘 (G:) 未连接"
    exit 1
}

# 1. 执行 AIOS 备份
Write-Log "执行 AIOS 备份..."
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING='utf-8'
& "C:\Program Files\Python312\python.exe" -X utf8 backup.py

if ($LASTEXITCODE -ne 0) {
    Write-Log "AIOS 备份失败"
    exit 1
}

# 2. 复制到 T7
Write-Log "复制备份到 T7..."
$sourceBackup = "C:\Users\A\.openclaw\workspace\aios\backups\$timestamp"
$destBackup = "G:\taijios_backup\$timestamp"

if (Test-Path $sourceBackup) {
    robocopy $sourceBackup $destBackup /E /Z /R:3 /W:5 /NFL /NDL /NJH /NJS | Out-Null
    if ($LASTEXITCODE -le 7) {
        Write-Log "MRS 备份完成: $destBackup"
    } else {
        Write-Log "MRS 备份失败 (exit code: $LASTEXITCODE)"
    }
} else {
    Write-Log "警告：备份目录不存在 $sourceBackup"
}

# 3. 完整备份整个 workspace（包含所有内容）
Write-Log "完整备份整个 workspace..."
robocopy "C:\Users\A\.openclaw\workspace" "G:\taijios_full_workspace" /E /Z /R:3 /W:5 /XD node_modules .git __pycache__ /NFL /NDL /NJH /NJS | Out-Null

if ($LASTEXITCODE -le 7) {
    Write-Log "完整 workspace 备份完成"
    
    # 统计备份文件数和大小
    $fileCount = (Get-ChildItem "G:\taijios_full_workspace" -Recurse -File | Measure-Object).Count
    $totalSize = (Get-ChildItem "G:\taijios_full_workspace" -Recurse -File | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($totalSize / 1MB, 2)
    Write-Log "文件数: $fileCount | 总大小: $sizeMB MB"
} else {
    Write-Log "workspace 备份失败 (exit code: $LASTEXITCODE)"
}

# 4. 清理旧备份（保留最近 7 天）
Write-Log "清理旧备份..."
$oldBackups = Get-ChildItem "G:\taijios_backup" -Directory | 
    Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' } | 
    Sort-Object Name -Descending | 
    Select-Object -Skip 7

foreach ($old in $oldBackups) {
    Remove-Item $old.FullName -Recurse -Force
    Write-Log "删除旧备份: $($old.Name)"
}

Write-Log "每日备份完成！"
Write-Log "========================================"
