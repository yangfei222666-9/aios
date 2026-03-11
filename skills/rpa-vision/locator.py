"""定位器 - 查找文本、按钮、输入框等元素"""

from typing import Optional, Dict, Any, Tuple, List
from difflib import SequenceMatcher

from capture import Capture
from ocr.base import OCREngine
from vision_parser import VisionParser


class Locator:
    """定位器"""
    
    def __init__(self, capture: Capture, ocr: OCREngine, parser: VisionParser):
        self.capture = capture
        self.ocr = ocr
        self.parser = parser
        self._cached_ocr_result = None
    
    def find_text(
        self,
        target: str,
        fuzzy: bool = False,
        threshold: float = 0.8,
        refresh: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        查找文本
        
        Args:
            target: 目标文本
            fuzzy: 是否模糊匹配
            threshold: 模糊匹配阈值（0-1）
            refresh: 是否刷新截图
        
        Returns:
            {"text": "...", "bbox": (x1, y1, x2, y2), "confidence": 0.95} 或 None
        """
        # 获取 OCR 结果
        if refresh or self._cached_ocr_result is None:
            screenshot = self.capture.capture()
            self._cached_ocr_result = self.ocr.extract(screenshot)
        
        # 查找匹配
        best_match = None
        best_score = 0.0
        
        for item in self._cached_ocr_result:
            text = item["text"]
            
            if fuzzy:
                # 模糊匹配
                score = SequenceMatcher(None, target.lower(), text.lower()).ratio()
                if score >= threshold and score > best_score:
                    best_score = score
                    best_match = item
            else:
                # 精确匹配
                if target in text:
                    return item
        
        return best_match
    
    def find_nearest_input(self, label_bbox: Tuple[int, int, int, int]) -> Optional[Tuple[int, int]]:
        """
        查找最近的输入框
        
        Args:
            label_bbox: 标签边界框 (x1, y1, x2, y2)
        
        Returns:
            输入框中心坐标 (x, y)，或 None
        """
        if self._cached_ocr_result is None:
            screenshot = self.capture.capture()
            self._cached_ocr_result = self.ocr.extract(screenshot)
        
        # 解析元素
        elements = self.parser.parse_elements(self._cached_ocr_result)
        
        # 查找输入框
        return self.parser.find_input_near_label(label_bbox, elements)
    
    def clear_cache(self):
        """清除缓存"""
        self._cached_ocr_result = None
