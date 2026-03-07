# Site Monitor - Windows PowerShell 脚本
# 用于 Cron 或手动执行

# === 配置（根据你的环境修改）===
$ROOT = "C:\Users\A\.openclaw\workspace\aios\agent_system"
$PY = "C:\Program Files\Python312\python.exe"
$CFG = "$ROOT\monitors.yaml"
$STATE = "$ROOT\monitors_state.json"
$HB = "$ROOT\reports\heartbeat_monitor.md"
$LOGDIR = "$ROOT\logs"
$LOCK = "$ROOT\site_monitor.lock"

# Telegram（可选）
# $env:TG_BOT_TOKEN = "YOUR_TOKEN"
# $env:TG_CHAT_ID = "7986452220"

# 时区
$env:MONITOR_TZ = "Asia/Shanghai"

# 创建日志目录
New-Item -ItemType Directory -Force -Path $LOGDIR | Out-Null

# 切换到工作目录
Set-Location $ROOT

# 防止重叠执行（简单的文件锁）
if (Test-Path $LOCK) {
    $lockAge = (Get-Date) - (Get-Item $LOCK).LastWriteTime
    if ($lockAge.TotalMinutes -lt 10) {
        Write-Host "[SKIP] Another instance is running (lock age: $($lockAge.TotalMinutes) min)"
        exit 0
    } else {
        Write-Host "[WARN] Stale lock detected, removing..."
        Remove-Item $LOCK -Force
    }
}

# 创建锁文件
New-Item -ItemType File -Force -Path $LOCK | Out-Null

try {
    # 执行监控
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] Starting site monitor..."
    
    & $PY site_monitor.py `
        --config $CFG `
        --state $STATE `
        --heartbeat $HB `
        $args `
        2>&1 | Tee-Object -FilePath "$LOGDIR\site_monitor.log" -Append
    
    $exitCode = $LASTEXITCODE
    Write-Host "[$timestamp] Completed with exit code: $exitCode"
    
} finally {
    # 清理锁文件
    Remove-Item $LOCK -Force -ErrorAction SilentlyContinue
}

exit $exitCode
