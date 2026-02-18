# 启动语音服务（计划任务调用）
$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = "C:\Program Files\Python312\python.exe"

# 这里改成你真正的入口（按你项目实际情况选一个）
# 例1：wake_listener
$Entry = Join-Path $ProjectRoot "tools\wake_listener.py"

# 例2：voice_wake_service
# $Entry = Join-Path $ProjectRoot "tools\voice_wake_service.py"

# 可选：配置文件
# $Config = Join-Path $ProjectRoot "openclaw.yaml"

$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("voice_service_boot_" + (Get-Date -Format "yyyyMMdd") + ".log")

# 用 cmd 包一层，方便重定向到文件（避免计划任务吞输出）
$cmd = "`"$Python`" `"$Entry`""
# 若需要配置文件：$cmd = "`"$Python`" `"$Entry`" `"$Config`""

cmd /c "$cmd >> `"$LogFile`" 2>>&1"
exit 0