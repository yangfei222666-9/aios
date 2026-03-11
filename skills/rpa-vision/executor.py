"""执行器 - 执行鼠标、键盘操作"""

import time
from typing import Tuple
import pyautogui


class Executor:
    """执行器"""
    
    def __init__(self, dry_run: bool = False):
        """
        初始化
        
        Args:
            dry_run: 是否启用 Dry-run 模式（只记录不执行）
        """
        self.dry_run = dry_run
        
        # PyAutoGUI 配置
        pyautogui.PAUSE = 0.1  # 每次操作后暂停 0.1 秒
        pyautogui.FAILSAFE = True  # 鼠标移到左上角中断
    
    def click(self, x: int, y: int, button: str = "left"):
        """
        点击
        
        Args:
            x: X 坐标
            y: Y 坐标
            button: 按钮类型（left/right/middle）
        """
        if self.dry_run:
            print(f"[DRY-RUN] click({x}, {y}, button={button})")
            return
        
        pyautogui.click(x, y, button=button)
    
    def type_text(self, text: str, interval: float = 0.05):
        """
        输入文本
        
        Args:
            text: 文本内容
            interval: 按键间隔（秒）
        """
        if self.dry_run:
            print(f"[DRY-RUN] type_text('{text}', interval={interval})")
            return
        
        pyautogui.write(text, interval=interval)
    
    def press_key(self, key: str):
        """
        按键
        
        Args:
            key: 按键名称（enter/esc/tab/...）
        """
        if self.dry_run:
            print(f"[DRY-RUN] press_key('{key}')")
            return
        
        pyautogui.press(key)
    
    def hotkey(self, *keys: str):
        """
        快捷键
        
        Args:
            keys: 按键序列（如 "ctrl", "c"）
        """
        if self.dry_run:
            print(f"[DRY-RUN] hotkey({', '.join(keys)})")
            return
        
        pyautogui.hotkey(*keys)
    
    def drag(self, start: Tuple[int, int], end: Tuple[int, int], duration: float = 0.5):
        """
        拖拽
        
        Args:
            start: 起点 (x, y)
            end: 终点 (x, y)
            duration: 持续时间（秒）
        """
        if self.dry_run:
            print(f"[DRY-RUN] drag({start}, {end}, duration={duration})")
            return
        
        pyautogui.moveTo(start[0], start[1])
        pyautogui.dragTo(end[0], end[1], duration=duration)
