# Memory Server 自动启动脚本
# 用途：每次系统启动时自动启动 Memory Server

$ErrorActionPreference = "Stop"

# 设置编码
$env:PYTHONUTF8 = 1
$env:PYTHONIOENCODING = 'utf-8'

# 切换到 agent_system 目录
$AGENT_SYSTEM_DIR = "C:\Users\A\.openclaw\workspace\aios\agent_system"
Set-Location $AGENT_SYSTEM_DIR

# 检查 Memory Server 是否已在运行
$existingProcess = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*memory_server.py*"
}

if ($existingProcess) {
    Write-Host "[INFO] Memory Server 已在运行 (PID: $($existingProcess.Id))"
    exit 0
}

# 启动 Memory Server
Write-Host "[INFO] 启动 Memory Server..."
Start-Process -FilePath "C:\Program Files\Python312\python.exe" `
    -ArgumentList "-X utf8 memory_server.py" `
    -WorkingDirectory $AGENT_SYSTEM_DIR `
    -WindowStyle Hidden

# 等待 2 秒检查启动状态
Start-Sleep -Seconds 2

# 验证启动
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:7788/status" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[SUCCESS] Memory Server 启动成功！"
        Write-Host "[INFO] 访问地址: http://127.0.0.1:7788"
    }
} catch {
    Write-Host "[ERROR] Memory Server 启动失败或未响应"
    exit 1
}
