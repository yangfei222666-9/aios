"""OCR 引擎基类"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from PIL import Image


class OCREngine(ABC):
    """OCR 引擎基类"""
    
    @abstractmethod
    def extract(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        提取文本
        
        Args:
            image: PIL.Image
        
        Returns:
            [
                {
                    "text": "识别的文本",
                    "bbox": (x1, y1, x2, y2),
                    "confidence": 0.95
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        pass
