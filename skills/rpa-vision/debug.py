"""调试模块 - 保存截图、OCR 结果、动作日志"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw


class Debug:
    """调试模块"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化
        
        Args:
            output_dir: 输出目录，None 表示使用默认目录
        """
        if output_dir is None:
            output_dir = "./debug_output"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self.output_dir / "screenshots").mkdir(exist_ok=True)
        (self.output_dir / "ocr_results").mkdir(exist_ok=True)
        (self.output_dir / "annotated").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        # 日志文件
        self.log_file = self.output_dir / "logs" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    def save_screenshot(self, image: Image.Image, prefix: str = "screenshot"):
        """
        保存截图
        
        Args:
            image: PIL.Image
            prefix: 文件名前缀
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.png"
        filepath = self.output_dir / "screenshots" / filename
        image.save(filepath)
    
    def save_ocr_result(self, result: List[Dict[str, Any]], prefix: str = "ocr"):
        """
        保存 OCR 结果
        
        Args:
            result: OCR 结果
            prefix: 文件名前缀
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.json"
        filepath = self.output_dir / "ocr_results" / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def save_annotated_screenshot(
        self,
        image: Image.Image,
        points: List[Tuple[int, int]],
        prefix: str = "annotated"
    ):
        """
        保存标注截图
        
        Args:
            image: PIL.Image
            points: 标注点列表 [(x, y), ...]
            prefix: 文件名前缀
        """
        # 复制图像
        annotated = image.copy()
        draw = ImageDraw.Draw(annotated)
        
        # 绘制标注点
        for x, y in points:
            # 绘制十字
            size = 10
            draw.line([(x - size, y), (x + size, y)], fill="red", width=2)
            draw.line([(x, y - size), (x, y + size)], fill="red", width=2)
            
            # 绘制圆圈
            draw.ellipse([(x - 5, y - 5), (x + 5, y + 5)], outline="red", width=2)
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.png"
        filepath = self.output_dir / "annotated" / filename
        annotated.save(filepath)
    
    def log_action(self, action: str, params: Dict[str, Any]):
        """
        记录动作日志
        
        Args:
            action: 动作类型
            params: 参数
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "params": params
        }
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
