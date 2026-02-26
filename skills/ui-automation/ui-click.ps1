# ui-click.ps1 - 鼠标点击操作
param(
    [int]$X,
    [int]$Y,
    [string]$Button = "Left",  # Left, Right, Middle
    [string]$Window = $null,
    [switch]$DoubleClick
)

Add-Type -AssemblyName System.Windows.Forms

# 如果指定了窗口，先激活窗口
if ($Window) {
    $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*$Window*" } | Select-Object -First 1
    if ($proc) {
        $null = [System.Windows.Forms.SendKeys]::SendWait("%")
        $proc.MainWindowHandle | Out-Null
        Start-Sleep -Milliseconds 200
    } else {
        Write-Error "窗口未找到: $Window"
        exit 1
    }
}

# 移动鼠标
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($X, $Y)
Start-Sleep -Milliseconds 100

# 点击
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Mouse {
    [DllImport("user32.dll")]
    public static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);
    
    public const int MOUSEEVENTF_LEFTDOWN = 0x02;
    public const int MOUSEEVENTF_LEFTUP = 0x04;
    public const int MOUSEEVENTF_RIGHTDOWN = 0x08;
    public const int MOUSEEVENTF_RIGHTUP = 0x10;
    public const int MOUSEEVENTF_MIDDLEDOWN = 0x20;
    public const int MOUSEEVENTF_MIDDLEUP = 0x40;
}
"@

switch ($Button) {
    "Left" {
        [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        Start-Sleep -Milliseconds 50
        [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        if ($DoubleClick) {
            Start-Sleep -Milliseconds 50
            [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            Start-Sleep -Milliseconds 50
            [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        }
    }
    "Right" {
        [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        Start-Sleep -Milliseconds 50
        [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    }
    "Middle" {
        [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        Start-Sleep -Milliseconds 50
        [Mouse]::mouse_event([Mouse]::MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
    }
}

Write-Host "✅ 点击完成: ($X, $Y) - $Button"
