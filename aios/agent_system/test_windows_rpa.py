#!/usr/bin/env python3
# test_windows_rpa.py - Windows 表层 RPA 验证

import ctypes
import time
from ctypes import wintypes

# Windows API 定义
user32 = ctypes.windll.user32

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_position():
    """获取鼠标当前位置（表层映射）"""
    try:
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        print(f"[MOUSE] Position: ({pt.x}, {pt.y})")
        return (pt.x, pt.y)
    except Exception as e:
        print(f"[ERROR] Get mouse position failed: {e}")
        return None

def get_active_window():
    """获取当前活动窗口（表层映射）"""
    try:
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        print(f"[WINDOW] Active: {buff.value}")
        return buff.value
    except Exception as e:
        print(f"[ERROR] Get active window failed: {e}")
        return None

def get_screen_size():
    """获取屏幕分辨率（表层映射）"""
    try:
        width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        print(f"[SCREEN] Resolution: {width}x{height}")
        return (width, height)
    except Exception as e:
        print(f"[ERROR] Get screen info failed: {e}")
        return None

def track_mouse_movement(duration=5):
    """追踪鼠标移动轨迹（表层映射）"""
    print(f"\n[TRACK] Start tracking mouse for {duration} seconds...")
    print("Please move your mouse...")
    
    positions = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        pos = get_mouse_position()
        if pos:
            positions.append((time.time() - start_time, pos))
        time.sleep(0.5)
    
    print(f"\n[TRACK] Completed, {len(positions)} points recorded")
    for t, pos in positions:
        print(f"  {t:.1f}s: {pos}")
    
    return positions

if __name__ == "__main__":
    print("=" * 60)
    print("Windows 表层 RPA 验证")
    print("=" * 60)
    
    # 1. 获取鼠标位置
    print("\n[1] 鼠标位置检测")
    get_mouse_position()
    
    # 2. 获取活动窗口
    print("\n[2] 活动窗口检测")
    get_active_window()
    
    # 3. 获取屏幕信息
    print("\n[3] 屏幕信息检测")
    get_screen_size()
    
    # 4. 追踪鼠标轨迹
    print("\n[4] 鼠标轨迹追踪")
    track_mouse_movement(duration=5)
    
    print("\n" + "=" * 60)
    print("[OK] Verification completed")
    print("=" * 60)
