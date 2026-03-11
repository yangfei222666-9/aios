"""视觉解析器 - 解析 OCR 结果，推断元素类型和位置"""

from typing import List, Dict, Any, Optional, Tuple


class VisionParser:
    """视觉解析器"""
    
    def parse_elements(self, ocr_result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析元素
        
        Args:
            ocr_result: OCR 结果
        
        Returns:
            [
                {
                    "text": "...",
                    "bbox": (x1, y1, x2, y2),
                    "type": "label|button|input|...",
                    "confidence": 0.95
                },
                ...
            ]
        """
        elements = []
        
        for item in ocr_result:
            element = item.copy()
            element["type"] = self._infer_type(item["text"], item["bbox"])
            elements.append(element)
        
        return elements
    
    def _infer_type(self, text: str, bbox: Tuple[int, int, int, int]) -> str:
        """
        推断元素类型
        
        Args:
            text: 文本内容
            bbox: 边界框 (x1, y1, x2, y2)
        
        Returns:
            元素类型（label/button/input/...）
        """
        text_lower = text.lower().strip()
        x1, y1, x2, y2 = bbox
        
        # 按钮特征
        button_keywords = [
            "确定", "取消", "提交", "登录", "注册", "搜索", "发送",
            "ok", "cancel", "submit", "login", "register", "search", "send"
        ]
        if any(kw in text_lower for kw in button_keywords):
            return "button"
        
        # 标签特征（通常以冒号结尾）
        if text.endswith(":") or text.endswith("："):
            return "label"
        
        # 输入框特征（通常是空白或占位符）
        if not text or text in ["请输入", "输入", "input", "enter"]:
            return "input"
        
        # 默认为文本
        return "text"
    
    def find_input_near_label(
        self,
        label_bbox: Tuple[int, int, int, int],
        elements: List[Dict[str, Any]],
        max_distance: int = 200
    ) -> Optional[Tuple[int, int]]:
        """
        查找标签附近的输入框
        
        Args:
            label_bbox: 标签边界框 (x1, y1, x2, y2)
            elements: 元素列表
            max_distance: 最大距离（像素）
        
        Returns:
            输入框中心坐标 (x, y)，或 None
        """
        lx1, ly1, lx2, ly2 = label_bbox
        label_center = ((lx1 + lx2) // 2, (ly1 + ly2) // 2)
        
        # 查找最近的输入框
        min_distance = float("inf")
        nearest_input = None
        
        for elem in elements:
            if elem["type"] == "input":
                ex1, ey1, ex2, ey2 = elem["bbox"]
                elem_center = ((ex1 + ex2) // 2, (ey1 + ey2) // 2)
                
                # 计算距离
                distance = ((elem_center[0] - label_center[0]) ** 2 +
                           (elem_center[1] - label_center[1]) ** 2) ** 0.5
                
                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    nearest_input = elem_center
        
        return nearest_input
