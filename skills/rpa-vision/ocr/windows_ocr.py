"""Windows OCR API 引擎"""

import asyncio
import io
from typing import List, Dict, Any
from PIL import Image

try:
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.globalization import Language
    from winsdk.windows.graphics.imaging import BitmapDecoder, SoftwareBitmap
    from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
    WINDOWS_OCR_AVAILABLE = True
except ImportError:
    WINDOWS_OCR_AVAILABLE = False

from ocr.base import OCREngine


def rect_to_xyxy(rect):
    """
    将 Windows OCR 的 (x, y, width, height) 转为内部统一格式 (x1, y1, x2, y2)
    
    Args:
        rect: OcrWord.BoundingRect
    
    Returns:
        (x1, y1, x2, y2)
    """
    x1 = int(rect.x)
    y1 = int(rect.y)
    x2 = int(rect.x + rect.width)
    y2 = int(rect.y + rect.height)
    return (x1, y1, x2, y2)


def union_boxes(boxes):
    """
    合并多个 bbox 为一个包围框
    
    Args:
        boxes: [(x1, y1, x2, y2), ...]
    
    Returns:
        (x1, y1, x2, y2) or None
    """
    if not boxes:
        return None
    
    x1 = min(b[0] for b in boxes)
    y1 = min(b[1] for b in boxes)
    x2 = max(b[2] for b in boxes)
    y2 = max(b[3] for b in boxes)
    return (x1, y1, x2, y2)


class WindowsOCR(OCREngine):
    """Windows OCR API 引擎"""
    
    def __init__(self, language: str = "zh-CN"):
        """
        初始化
        
        Args:
            language: 语言代码（zh-CN/en-US/...）
        """
        self.language = language
        self._engine = None
        self._available_languages = []
        
        if WINDOWS_OCR_AVAILABLE:
            try:
                # 获取可用语言列表
                self._available_languages = [lang.language_tag for lang in OcrEngine.available_recognizer_languages]
                
                # 尝试创建指定语言的引擎
                if language in self._available_languages:
                    lang = Language(language)
                    self._engine = OcrEngine.try_create_from_language(lang)
                else:
                    # Fallback to user profile languages
                    self._engine = OcrEngine.try_create_from_user_profile_languages()
            except Exception as e:
                # Fallback to default
                try:
                    self._engine = OcrEngine.try_create_from_user_profile_languages()
                except:
                    pass
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return WINDOWS_OCR_AVAILABLE and self._engine is not None
    
    def get_available_languages(self) -> List[str]:
        """获取可用语言列表"""
        return self._available_languages
    
    def extract(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        提取文本
        
        Args:
            image: PIL.Image
        
        Returns:
            [{"text": "...", "bbox": (x1, y1, x2, y2), "words": [...], "confidence": 1.0}, ...]
        """
        if not self.is_available():
            raise RuntimeError("Windows OCR 不可用")
        
        # 运行异步 OCR
        return asyncio.run(self._extract_async(image))
    
    async def _extract_async(self, image: Image.Image) -> List[Dict[str, Any]]:
        """异步提取文本"""
        # 转换 PIL.Image 为 SoftwareBitmap
        stream = InMemoryRandomAccessStream()
        
        # 保存图像到内存流
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        # 写入流
        writer = DataWriter(stream)
        writer.write_bytes(buffer.read())
        await writer.store_async()
        await writer.flush_async()
        stream.seek(0)
        
        # 解码
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        
        # OCR 识别
        result = await self._engine.recognize_async(bitmap)
        
        # 解析结果
        parsed = []
        for line in result.lines:
            words = []
            word_boxes = []
            
            # 从 line.words 提取每个 word 的 bbox
            for word in line.words:
                box = rect_to_xyxy(word.bounding_rect)
                words.append({
                    "text": word.text,
                    "bbox": box,
                })
                word_boxes.append(box)
            
            # Union 所有 word bbox 得到 line bbox
            line_bbox = union_boxes(word_boxes)
            if line_bbox is None:
                # 如果没有 words，跳过这一行
                continue
            
            parsed.append({
                "text": line.text,
                "bbox": line_bbox,
                "words": words,
                "confidence": 1.0  # Windows OCR 不提供置信度
            })
        
        return parsed
