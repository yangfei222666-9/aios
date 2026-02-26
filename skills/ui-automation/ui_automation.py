#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Automation - Python 包装器
"""
import subprocess
import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent

def click(x: int, y: int, button: str = "Left", window: str = None, double: bool = False):
    """点击鼠标"""
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(SKILL_DIR / "ui-click.ps1"),
           "-X", str(x), "-Y", str(y), "-Button", button]
    
    if window:
        cmd.extend(["-Window", window])
    if double:
        cmd.append("-DoubleClick")
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return result.returncode == 0

def type_text(text: str, press_enter: bool = False, delay_ms: int = 50):
    """输入文本"""
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(SKILL_DIR / "ui-type.ps1"),
           "-Text", text, "-DelayMs", str(delay_ms)]
    
    if press_enter:
        cmd.append("-PressEnter")
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return result.returncode == 0

def get_windows(filter_text: str = None):
    """获取窗口列表"""
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(SKILL_DIR / "ui-windows.ps1"),
           "-Json"]
    
    if filter_text:
        cmd.extend(["-Filter", filter_text])
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except:
            return []
    return []

if __name__ == "__main__":
    # 测试
    print("获取窗口列表...")
    windows = get_windows()
    for win in windows:
        print(f"  - {win['Title']} ({win['ProcessName']})")
