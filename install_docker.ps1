# Docker Desktop 自动安装脚本
# 静默安装 + WSL2 后端 + 开机自启

$installer = "$env:TEMP\DockerDesktopInstaller.exe"

Write-Host "🚀 开始安装 Docker Desktop..."
Write-Host "   模式: 静默安装"
Write-Host "   后端: WSL 2"
Write-Host "   自启: 是"
Write-Host ""

# 静默安装参数
# install: 安装
# --quiet: 静默模式
# --accept-license: 接受许可
# --backend=wsl-2: 使用 WSL2（不用 Hyper-V）
$args = @(
    "install",
    "--quiet",
    "--accept-license",
    "--backend=wsl-2"
)

Start-Process -FilePath $installer -ArgumentList $args -Wait -NoNewWindow

Write-Host ""
Write-Host "✅ 安装完成"
Write-Host ""
Write-Host "⚠️  需要重启电脑才能生效"
Write-Host "   重启后 Docker Desktop 会自动启动"
