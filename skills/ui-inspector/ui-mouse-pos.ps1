# ui-mouse-pos.ps1 - 获取鼠标位置
param(
    [switch]$Live
)

Add-Type -AssemblyName System.Windows.Forms

if ($Live) {
    Write-Host "实时监控鼠标位置（按 Ctrl+C 停止）..."
    while ($true) {
        $pos = [System.Windows.Forms.Cursor]::Position
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] X=$($pos.X), Y=$($pos.Y)" -NoNewline
        Write-Host "`r" -NoNewline
        Start-Sleep -Milliseconds 100
    }
} else {
    $pos = [System.Windows.Forms.Cursor]::Position
    Write-Host "鼠标位置: X=$($pos.X), Y=$($pos.Y)"
    
    # 输出 JSON 格式
    @{
        X = $pos.X
        Y = $pos.Y
    } | ConvertTo-Json
}
