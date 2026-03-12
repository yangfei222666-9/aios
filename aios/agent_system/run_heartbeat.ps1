# AIOS Heartbeat 自动启动脚本
# 每 6 小时执行一次

$ErrorActionPreference = "Stop"

# 设置编码
$env:PYTHONUTF8 = 1
$env:PYTHONIOENCODING = 'utf-8'

# 切换到 agent_system 目录
$AGENT_SYSTEM_DIR = "C:\Users\A\.openclaw\workspace\aios\agent_system"
Set-Location $AGENT_SYSTEM_DIR

# 记录执行时间
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[$timestamp] Starting Heartbeat..."

# 执行 Heartbeat
& "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py

# 记录完成
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[$timestamp] Heartbeat completed"
