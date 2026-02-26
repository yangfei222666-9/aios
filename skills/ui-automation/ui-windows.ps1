# ui-windows.ps1 - 窗口管理
param(
    [string]$Filter = $null,
    [switch]$Json
)

$windows = Get-Process | Where-Object { $_.MainWindowTitle -ne "" } | ForEach-Object {
    [PSCustomObject]@{
        ProcessName = $_.ProcessName
        Title = $_.MainWindowTitle
        Id = $_.Id
        Handle = $_.MainWindowHandle
    }
}

if ($Filter) {
    $windows = $windows | Where-Object { $_.Title -like "*$Filter*" }
}

if ($Json) {
    $windows | ConvertTo-Json
} else {
    $windows | Format-Table -AutoSize
}
