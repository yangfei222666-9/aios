# 太极OS (TaijiOS) - 快速启动脚本
# 用于日常开发的一键启动脚本

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('all', 'memory', 'dashboard', 'heartbeat', 'verify')]
    [string]$Mode = 'all'
)

# 设置编码
$env:PYTHONUTF8 = 1
$env:PYTHONIOENCODING = 'utf-8'

# Python 路径
$PYTHON = "C:\Program Files\Python312\python.exe"

# 项目路径
$PROJECT_ROOT = "C:\Users\A\.openclaw\workspace\aios"
$AGENT_SYSTEM = "$PROJECT_ROOT\agent_system"
$DASHBOARD = "$PROJECT_ROOT\dashboard\AIOS-Dashboard-v3.4"

# 颜色输出
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# 检查进程是否运行
function Test-ProcessRunning {
    param(
        [string]$ProcessName,
        [int]$Port
    )
    
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -TimeoutSec 2 -ErrorAction SilentlyContinue
        return $true
    } catch {
        return $false
    }
}

# 启动 Memory Server
function Start-MemoryServer {
    Write-Info "启动 Memory Server..."
    
    if (Test-ProcessRunning -ProcessName "memory_server" -Port 7788) {
        Write-Warning "Memory Server 已在运行"
        return
    }
    
    Set-Location $AGENT_SYSTEM
    Start-Process -FilePath $PYTHON -ArgumentList "-X utf8 memory_server.py" -WindowStyle Normal
    
    # 等待启动
    Start-Sleep -Seconds 3
    
    if (Test-ProcessRunning -ProcessName "memory_server" -Port 7788) {
        Write-Success "Memory Server 启动成功 (http://127.0.0.1:7788)"
    } else {
        Write-Error "Memory Server 启动失败"
    }
}

# 启动 Dashboard
function Start-Dashboard {
    Write-Info "启动 Dashboard..."
    
    if (Test-ProcessRunning -ProcessName "server" -Port 8888) {
        Write-Warning "Dashboard 已在运行"
        return
    }
    
    Set-Location $DASHBOARD
    Start-Process -FilePath $PYTHON -ArgumentList "-X utf8 server.py" -WindowStyle Normal
    
    # 等待启动
    Start-Sleep -Seconds 3
    
    if (Test-ProcessRunning -ProcessName "server" -Port 8888) {
        Write-Success "Dashboard 启动成功 (http://127.0.0.1:8888)"
    } else {
        Write-Error "Dashboard 启动失败"
    }
}

# 运行 Heartbeat
function Start-Heartbeat {
    Write-Info "运行 Heartbeat..."
    
    Set-Location $AGENT_SYSTEM
    & $PYTHON -X utf8 heartbeat_v5.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Heartbeat 运行完成"
    } else {
        Write-Error "Heartbeat 运行失败"
    }
}

# 验证开发环境
function Start-Verify {
    Write-Info "验证开发环境..."
    
    Set-Location $PROJECT_ROOT
    & $PYTHON -X utf8 verify_dev_env.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "开发环境验证通过"
    } else {
        Write-Error "开发环境验证失败"
    }
}

# 主逻辑
Write-Host ""
Write-Host "太极OS (TaijiOS) - 快速启动脚本" -ForegroundColor Magenta
Write-Host "版本: v1.0" -ForegroundColor Magenta
Write-Host "日期: 2026-03-10" -ForegroundColor Magenta
Write-Host ""

switch ($Mode) {
    'all' {
        Write-Info "启动所有服务..."
        Start-MemoryServer
        Start-Dashboard
        Write-Info "所有服务启动完成"
        Write-Info "按任意键运行 Heartbeat..."
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        Start-Heartbeat
    }
    'memory' {
        Start-MemoryServer
    }
    'dashboard' {
        Start-Dashboard
    }
    'heartbeat' {
        Start-Heartbeat
    }
    'verify' {
        Start-Verify
    }
}

Write-Host ""
Write-Info "完成！"
Write-Host ""
