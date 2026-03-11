"""安全模块 - 前台窗口校验、Fail-safe 等"""

import ctypes
import pyautogui


class Safety:
    """安全模块"""
    
    def __init__(self):
        self.failsafe_enabled = False
    
    def enable_failsafe(self):
        """启用 Fail-safe（鼠标移到左上角中断）"""
        pyautogui.FAILSAFE = True
        self.failsafe_enabled = True
    
    def disable_failsafe(self):
        """禁用 Fail-safe"""
        pyautogui.FAILSAFE = False
        self.failsafe_enabled = False
    
    def check_foreground(self) -> bool:
        """
        检查前台窗口
        
        Returns:
            True 表示有前台窗口
        """
        try:
            # Windows API
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            return hwnd != 0
        except:
            return True  # 非 Windows 系统默认通过
    
    def get_foreground_window_title(self) -> str:
        """
        获取前台窗口标题
        
        Returns:
            窗口标题
        """
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            
            return buffer.value
        except:
            return ""
