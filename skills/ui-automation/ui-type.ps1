# ui-type.ps1 - 键盘输入操作
param(
    [Parameter(Mandatory=$true)]
    [string]$Text,
    [switch]$PressEnter,
    [int]$DelayMs = 50
)

Add-Type -AssemblyName System.Windows.Forms

# 输入文本
foreach ($char in $Text.ToCharArray()) {
    [System.Windows.Forms.SendKeys]::SendWait($char)
    Start-Sleep -Milliseconds $DelayMs
}

# 按回车
if ($PressEnter) {
    Start-Sleep -Milliseconds 100
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
}

Write-Host "✅ 输入完成: $Text"
