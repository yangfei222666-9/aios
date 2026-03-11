"""
RPA Vision - 视觉理解 + 自动化执行

核心能力：
1. 截图（全屏/窗口/区域）
2. OCR 文本提取
3. 查找文本
4. 点击文本
5. 输入文本
6. 快捷键
7. 等待条件
8. 调试输出

OCR 引擎优先级：
1. Windows OCR API（默认）
2. PaddleOCR（fallback）
3. Tesseract（兜底）
"""

import os
import time
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

import pyautogui
from mss import mss
from PIL import Image

from capture import Capture
from ocr.base import OCREngine
from ocr.windows_ocr import WindowsOCR
from vision_parser import VisionParser
from locator import Locator
from executor import Executor
from safety import Safety
from debug import Debug


class RPAVision:
    """RPA Vision 主入口"""
    
    def __init__(
        self,
        ocr_engine: Optional[OCREngine] = None,
        debug_mode: bool = False,
        debug_dir: Optional[str] = None,
        dry_run: bool = False
    ):
        """
        初始化 RPA Vision
        
        Args:
            ocr_engine: OCR 引擎（默认使用 Windows OCR）
            debug_mode: 是否启用调试模式
            debug_dir: 调试输出目录
            dry_run: 是否启用 Dry-run 模式（只识别不执行）
        """
        # 核心模块
        self.capture = Capture()
        self.ocr = ocr_engine or WindowsOCR()
        self.parser = VisionParser()
        self.locator = Locator(self.capture, self.ocr, self.parser)
        self.executor = Executor(dry_run=dry_run)
        self.safety = Safety()
        
        # 调试模块
        self.debug_mode = debug_mode
        self.debug = Debug(debug_dir) if debug_mode else None
        
        # 状态
        self.last_screenshot = None
        self.last_ocr_result = None
        
        # 安全检查
        self.safety.enable_failsafe()
    
    # ==================== 识别类 ====================
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        截图
        
        Args:
            region: 区域 (x, y, width, height)，None 表示全屏
        
        Returns:
            PIL.Image
        """
        screenshot = self.capture.capture(region)
        self.last_screenshot = screenshot
        
        if self.debug_mode:
            self.debug.save_screenshot(screenshot, "capture")
        
        return screenshot
    
    def extract_text(self, image: Optional[Image.Image] = None) -> List[Dict[str, Any]]:
        """
        OCR 提取文本
        
        Args:
            image: PIL.Image，None 表示使用最后一次截图
        
        Returns:
            [{"text": "...", "bbox": (x1, y1, x2, y2), "confidence": 0.95}, ...]
        """
        if image is None:
            if self.last_screenshot is None:
                image = self.capture_screen()
            else:
                image = self.last_screenshot
        
        result = self.ocr.extract(image)
        self.last_ocr_result = result
        
        if self.debug_mode:
            self.debug.save_ocr_result(result, "ocr")
        
        return result
    
    def find_text(
        self,
        target: str,
        fuzzy: bool = False,
        threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        查找文本
        
        Args:
            target: 目标文本
            fuzzy: 是否模糊匹配
            threshold: 模糊匹配阈值（0-1）
        
        Returns:
            {"text": "...", "bbox": (x1, y1, x2, y2), "confidence": 0.95} 或 None
        """
        return self.locator.find_text(target, fuzzy=fuzzy, threshold=threshold)
    
    def find_nearest_input(self, label_bbox: Tuple[int, int, int, int]) -> Optional[Tuple[int, int]]:
        """
        查找最近的输入框
        
        Args:
            label_bbox: 标签的 bbox (x1, y1, x2, y2)
        
        Returns:
            (x, y) 输入框中心坐标，或 None
        """
        return self.locator.find_nearest_input(label_bbox)
    
    def find_button(self, name: str) -> Optional[Tuple[int, int]]:
        """
        查找按钮
        
        Args:
            name: 按钮文本
        
        Returns:
            (x, y) 按钮中心坐标，或 None
        """
        result = self.find_text(name, fuzzy=True)
        if result:
            x1, y1, x2, y2 = result["bbox"]
            return ((x1 + x2) // 2, (y1 + y2) // 2)
        return None
    
    # ==================== 执行类 ====================
    
    def click(self, x: int, y: int, button: str = "left"):
        """
        点击坐标
        
        Args:
            x: X 坐标
            y: Y 坐标
            button: 按钮类型（left/right/middle）
        """
        # 前台窗口校验
        if not self.safety.check_foreground():
            raise RuntimeError("目标窗口不在前台")
        
        # 执行点击
        self.executor.click(x, y, button)
        
        # 调试记录
        if self.debug_mode:
            self.debug.log_action("click", {"x": x, "y": y, "button": button})
            if self.last_screenshot:
                self.debug.save_annotated_screenshot(
                    self.last_screenshot,
                    [(x, y)],
                    "click"
                )
    
    def click_text(
        self,
        target: str,
        offset: Tuple[int, int] = (0, 0),
        fuzzy: bool = True
    ):
        """
        点击文本
        
        Args:
            target: 目标文本
            offset: 偏移量 (dx, dy)
            fuzzy: 是否模糊匹配
        """
        # 查找文本
        result = self.find_text(target, fuzzy=fuzzy)
        if not result:
            raise ValueError(f"未找到文本: {target}")
        
        # 计算点击位置
        x1, y1, x2, y2 = result["bbox"]
        click_x = (x1 + x2) // 2 + offset[0]
        click_y = (y1 + y2) // 2 + offset[1]
        
        # 点击
        self.click(click_x, click_y)
    
    def type_text(self, text: str, interval: float = 0.05):
        """
        输入文本
        
        Args:
            text: 文本内容
            interval: 按键间隔（秒）
        """
        self.executor.type_text(text, interval)
        
        if self.debug_mode:
            self.debug.log_action("type_text", {"text": text, "interval": interval})
    
    def press_key(self, key: str):
        """
        按键
        
        Args:
            key: 按键名称（enter/esc/tab/...）
        """
        self.executor.press_key(key)
        
        if self.debug_mode:
            self.debug.log_action("press_key", {"key": key})
    
    def hotkey(self, *keys: str):
        """
        快捷键
        
        Args:
            keys: 按键序列（如 "ctrl", "c"）
        """
        self.executor.hotkey(*keys)
        
        if self.debug_mode:
            self.debug.log_action("hotkey", {"keys": keys})
    
    def drag(self, start: Tuple[int, int], end: Tuple[int, int], duration: float = 0.5):
        """
        拖拽
        
        Args:
            start: 起点 (x, y)
            end: 终点 (x, y)
            duration: 持续时间（秒）
        """
        self.executor.drag(start, end, duration)
        
        if self.debug_mode:
            self.debug.log_action("drag", {"start": start, "end": end, "duration": duration})
    
    # ==================== 流程类 ====================
    
    def wait_for_text(
        self,
        target: str,
        timeout: float = 10,
        interval: float = 0.5,
        fuzzy: bool = True
    ) -> bool:
        """
        等待文本出现
        
        Args:
            target: 目标文本
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
            fuzzy: 是否模糊匹配
        
        Returns:
            是否找到
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self.capture_screen()
            self.extract_text()
            
            result = self.find_text(target, fuzzy=fuzzy)
            if result:
                return True
            
            time.sleep(interval)
        
        return False
    
    def wait_until_disappear(
        self,
        target: str,
        timeout: float = 10,
        interval: float = 0.5,
        fuzzy: bool = True
    ) -> bool:
        """
        等待文本消失
        
        Args:
            target: 目标文本
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
            fuzzy: 是否模糊匹配
        
        Returns:
            是否消失
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self.capture_screen()
            self.extract_text()
            
            result = self.find_text(target, fuzzy=fuzzy)
            if not result:
                return True
            
            time.sleep(interval)
        
        return False
    
    # ==================== 调试类 ====================
    
    def enable_debug(self, output_dir: Optional[str] = None):
        """启用调试模式"""
        self.debug_mode = True
        self.debug = Debug(output_dir)
    
    def dry_run(self, enabled: bool = True):
        """启用/禁用 Dry-run 模式"""
        self.executor.dry_run = enabled
    
    def get_last_screenshot(self) -> Optional[Image.Image]:
        """获取最后一次截图"""
        return self.last_screenshot
    
    def get_last_ocr_result(self) -> Optional[List[Dict[str, Any]]]:
        """获取最后一次 OCR 结果"""
        return self.last_ocr_result
