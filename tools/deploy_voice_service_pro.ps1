# deploy_voice_service_en.ps1
# OpenClaw Voice Service Deployment (ONLOGON)

param(
    [string]$TaskName = "OpenClaw-VoiceService",
    [int]$DelaySeconds = 10,
    [switch]$Highest,  # 需要管理员才建议开
    [switch]$RunNow    # 创建后立刻跑一次
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) {
    Write-Host $msg -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host $msg -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host $msg -ForegroundColor Yellow
}

function Write-Fail($msg) {
    Write-Host $msg -ForegroundColor Red
}

function Is-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Safe-Resolve([string]$p) {
    try {
        return (Resolve-Path -LiteralPath $p).Path
    } catch {
        return [System.IO.Path]::GetFullPath($p)
    }
}

function Run-Exe([string]$exe, [string[]]$args) {
    # 直接调用 exe，避免 cmd /c 拼字符串
    $out = & $exe @args 2>&1
    $code = $LASTEXITCODE
    return @{ Code = $code; Out = ($out | Out-String).TrimEnd() }
}

Write-Info "=== OpenClaw Voice Service Deployment ==="

# 关键：用脚本所在目录推断项目根目录
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$startScript = Join-Path $projectRoot "tools\start_voice_service.ps1"
$logDir = Join-Path $projectRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not (Test-Path -LiteralPath $startScript)) {
    Write-Fail "start script not found: $(Safe-Resolve $startScript)"
    exit 2
}

# Delay 格式：0000:10 (10秒) / 0000:30 (30秒) 都常见
$delay = ("0000:{0:00}" -f $DelaySeconds)
$rl = "LIMITED"
if ($Highest) {
    if (Is-Admin) {
        $rl = "HIGHEST"
    } else {
        Write-Warn "Not running as Administrator. Fallback to /RL LIMITED."
        $rl = "LIMITED"
    }
}

$absStart = Safe-Resolve $startScript
$tr = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$absStart`""

Write-Info "ProjectRoot : $(Safe-Resolve $projectRoot)"
Write-Info "StartScript : $absStart"
Write-Info "TaskName    : $TaskName"
Write-Info "Delay       : $delay"
Write-Info "RunLevel    : $rl"
Write-Info "TR          : $tr"

# 1) 删除旧任务（忽略错误）
Run-Exe "schtasks.exe" @("/Delete","/TN",$TaskName,"/F") | Out-Null

# 2) 创建任务
$r = Run-Exe "schtasks.exe" @("/Create","/TN",$TaskName,"/SC","ONLOGON","/DELAY",$delay,"/TR",$tr,"/RL",$rl,"/F")
if ($r.Code -ne 0) {
    Write-Fail "Create task failed (exit=$($r.Code))"
    if ($r.Out) {
        Write-Fail $r.Out
    }
    Write-Warn "Tip: If you need /RL HIGHEST, run PowerShell as Administrator."
    exit 1
}
Write-Ok "Task created successfully."

# 3) 查询确认
$q = Run-Exe "schtasks.exe" @("/Query","/TN",$TaskName,"/FO","LIST")
if ($q.Code -ne 0) {
    Write-Warn "Query task failed (exit=$($q.Code))"
    if ($q.Out) {
        Write-Warn $q.Out
    }
} else {
    Write-Ok "Task query OK."
}

# 4) 可选：立刻跑一次
if ($RunNow) {
    $run = Run-Exe "schtasks.exe" @("/Run","/TN",$TaskName)
    if ($run.Code -ne 0) {
        Write-Warn "Run task failed (exit=$($run.Code))"
        if ($run.Out) {
            Write-Warn $run.Out
        }
    } else {
        Write-Ok "Task started."
    }
}

Write-Ok "Deployment done."
exit 0