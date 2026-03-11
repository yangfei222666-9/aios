"""截图模块"""

import ctypes
from typing import Optional, Tuple
from mss import mss
from PIL import Image


class Capture:
    """截图器"""
    
    def __init__(self):
        self.sct = mss()
        self.dpi_scale = self._get_dpi_scale()
    
    def _get_dpi_scale(self) -> float:
        """获取 DPI 缩放比例"""
        try:
            # Windows DPI 感知
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            
            # 获取缩放比例
            hdc = user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            user32.ReleaseDC(0, hdc)
            
            return dpi / 96.0  # 96 DPI = 100%
        except:
            return 1.0
    
    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        截图
        
        Args:
            region: (x, y, width, height)，None 表示全屏
        
        Returns:
            PIL.Image
        """
        if region is None:
            # 全屏截图
            monitor = self.sct.monitors[1]  # 主显示器
            screenshot = self.sct.grab(monitor)
        else:
            # 区域截图
            x, y, w, h = region
            
            # DPI 缩放调整
            if self.dpi_scale != 1.0:
                x = int(x * self.dpi_scale)
                y = int(y * self.dpi_scale)
                w = int(w * self.dpi_scale)
                h = int(h * self.dpi_scale)
            
            monitor = {"top": y, "left": x, "width": w, "height": h}
            screenshot = self.sct.grab(monitor)
        
        # 转换为 PIL.Image
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        monitor = self.sct.monitors[1]
        return (monitor["width"], monitor["height"])
