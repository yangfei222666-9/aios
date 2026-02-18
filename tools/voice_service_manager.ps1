# 语音唤醒服务管理脚本
# 用于 Windows 平台的服务管理

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "start", "stop", "restart", "status", "test")]
    [string]$Action = "status"
)

$ServiceName = "OpenClawVoiceWake"
$PythonPath = "python"
$ScriptPath = "tools\voice_wake_service.py"
$WorkingDir = "C:\Users\A\.openclaw\workspace"
$LogDir = "logs"

function Test-ServiceExists {
    param([string]$Name)
    $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
    return [bool]$service
}

function Install-Service {
    Write-Host "安装语音唤醒服务..." -ForegroundColor Cyan
    
    # 检查 NSSM (Non-Sucking Service Manager)
    $nssmPath = "C:\nssm\nssm.exe"
    if (-not (Test-Path $nssmPath)) {
        Write-Host "下载 NSSM..." -ForegroundColor Yellow
        $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
        $tempZip = "$env:TEMP\nssm.zip"
        
        try {
            Invoke-WebRequest -Uri $nssmUrl -OutFile $tempZip
            Expand-Archive -Path $tempZip -DestinationPath "C:\nssm" -Force
            Remove-Item $tempZip -Force
            Write-Host "NSSM 安装完成" -ForegroundColor Green
        } catch {
            Write-Host "NSSM 下载失败: $_" -ForegroundColor Red
            return $false
        }
    }
    
    # 创建服务
    Write-Host "创建服务: $ServiceName" -ForegroundColor Cyan
    & $nssmPath install $ServiceName $PythonPath $ScriptPath
    
    # 配置服务
    & $nssmPath set $ServiceName AppDirectory $WorkingDir
    & $nssmPath set $ServiceName AppStdout "$WorkingDir\$LogDir\service_stdout.log"
    & $nssmPath set $ServiceName AppStderr "$WorkingDir\$LogDir\service_stderr.log"
    & $nssmPath set $ServiceName AppRotateFiles 1
    & $nssmPath set $ServiceName AppRotateOnline 1
    & $nssmPath set $ServiceName AppRotateSeconds 86400  # 每天轮转
    & $nssmPath set $ServiceName AppRotateBytes 10485760  # 10MB
    
    Write-Host "服务安装完成" -ForegroundColor Green
    return $true
}

function Start-ServiceCustom {
    if (Test-ServiceExists -Name $ServiceName) {
        Write-Host "启动服务: $ServiceName" -ForegroundColor Cyan
        Start-Service -Name $ServiceName
        Write-Host "服务已启动" -ForegroundColor Green
    } else {
        Write-Host "服务不存在，请先安装" -ForegroundColor Red
    }
}

function Stop-ServiceCustom {
    if (Test-ServiceExists -Name $ServiceName) {
        Write-Host "停止服务: $ServiceName" -ForegroundColor Cyan
        Stop-Service -Name $ServiceName -Force
        Write-Host "服务已停止" -ForegroundColor Green
    } else {
        Write-Host "服务不存在" -ForegroundColor Yellow
    }
}

function Restart-ServiceCustom {
    Stop-ServiceCustom
    Start-Sleep -Seconds 2
    Start-ServiceCustom
}

function Get-ServiceStatus {
    if (Test-ServiceExists -Name $ServiceName) {
        $service = Get-Service -Name $ServiceName
        Write-Host "服务状态:" -ForegroundColor Cyan
        Write-Host "  名称: $($service.Name)"
        Write-Host "  显示名: $($service.DisplayName)"
        Write-Host "  状态: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
        Write-Host "  启动类型: $($service.StartType)"
        
        # 检查日志文件
        $logPath = "$WorkingDir\$LogDir\voice_wake.log"
        if (Test-Path $logPath) {
            $logInfo = Get-Item $logPath
            Write-Host "  日志文件: $logPath"
            Write-Host "  日志大小: $([math]::Round($logInfo.Length/1KB, 2)) KB"
            Write-Host "  最后修改: $($logInfo.LastWriteTime)"
            
            # 显示最后5行日志
            Write-Host "`n最近日志:" -ForegroundColor Cyan
            Get-Content $logPath -Tail 5 | ForEach-Object {
                Write-Host "  $_"
            }
        }
    } else {
        Write-Host "服务未安装" -ForegroundColor Yellow
    }
}

function Test-ServiceFunction {
    Write-Host "测试语音唤醒功能..." -ForegroundColor Cyan
    
    # 检查依赖
    Write-Host "检查 Python 模块..." -ForegroundColor Yellow
    $modules = @("sounddevice", "vosk", "numpy")
    foreach ($module in $modules) {
        try {
            python -c "import $module; print('✅ $module')" 2>$null
        } catch {
            Write-Host "❌ $module 未安装" -ForegroundColor Red
        }
    }
    
    # 检查模型文件
    Write-Host "`n检查语音模型..." -ForegroundColor Yellow
    $modelPath = "C:\Users\A\.openclaw\models\vosk-cn"
    if (Test-Path $modelPath) {
        Write-Host "✅ 模型目录存在: $modelPath" -ForegroundColor Green
        $size = (Get-ChildItem $modelPath -Recurse | Measure-Object -Property Length -Sum).Sum
        Write-Host "   模型大小: $([math]::Round($size/1MB, 2)) MB"
    } else {
        Write-Host "❌ 模型目录不存在" -ForegroundColor Red
    }
    
    # 运行简单测试
    Write-Host "`n运行功能测试..." -ForegroundColor Yellow
    try {
        Set-Location $WorkingDir
        python tools\voice_wake_simple.py
        Write-Host "`n✅ 功能测试通过" -ForegroundColor Green
    } catch {
        Write-Host "`n❌ 功能测试失败: $_" -ForegroundColor Red
    }
}

# 主逻辑
Write-Host "`n=== OpenClaw 语音唤醒服务管理 ===" -ForegroundColor Magenta
Write-Host "工作目录: $WorkingDir" -ForegroundColor Gray
Write-Host "脚本路径: $ScriptPath" -ForegroundColor Gray
Write-Host "`n执行操作: $Action" -ForegroundColor Cyan

switch ($Action) {
    "install" {
        Install-Service
    }
    "start" {
        Start-ServiceCustom
    }
    "stop" {
        Stop-ServiceCustom
    }
    "restart" {
        Restart-ServiceCustom
    }
    "status" {
        Get-ServiceStatus
    }
    "test" {
        Test-ServiceFunction
    }
}

Write-Host "`n操作完成" -ForegroundColor Green