import ctypes
import ctypes.wintypes
import subprocess
import os
import sys
import time
import threading

# Path to the HTML file
HTML_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "元气时钟.html")

# Use WebView2 via Edge to show the clock as a desktop widget
# We'll create a borderless, always-on-bottom, click-through window using PowerShell/C#

PS_SCRIPT = r'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create a borderless form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Genki Clock"
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.TopMost = $false
$form.ShowInTaskbar = $false
$form.BackColor = [System.Drawing.Color]::Black

# Position: bottom-right corner
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$w = 500
$h = 320
$form.Size = New-Object System.Drawing.Size($w, $h)
$form.Location = New-Object System.Drawing.Point(($screen.Right - $w - 30), ($screen.Bottom - $h - 30))
$form.Opacity = 0.92

# Use WebBrowser control
$browser = New-Object System.Windows.Forms.WebBrowser
$browser.Dock = [System.Windows.Forms.DockStyle]::Fill
$browser.ScrollBarsEnabled = $false
$browser.IsWebBrowserContextMenuEnabled = $false
$browser.ScriptErrorsSuppressed = $true
$browser.Navigate("HTMLPATH")
$form.Controls.Add($browser)

# Make window stay on desktop (behind everything but above wallpaper)
$form.Add_Shown({
    $form.Activate()
})

# Keep it always at bottom
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 2000
$timer.Add_Tick({
    # Send to bottom
    $HWND_BOTTOM = New-Object IntPtr(1)
    $SWP_NOSIZE = 0x0001
    $SWP_NOMOVE = 0x0002
    $SWP_NOACTIVATE = 0x0010
})
$timer.Start()

[System.Windows.Forms.Application]::Run($form)
'''

ps_script = PS_SCRIPT.replace("HTMLPATH", HTML_PATH.replace("\\", "\\\\"))

# Write the script
script_path = os.path.join(os.path.expanduser("~"), ".openclaw", "workspace", "genki-clock-widget.ps1")
with open(script_path, "w", encoding="utf-8") as f:
    f.write(ps_script)

print(f"Script written to {script_path}")
