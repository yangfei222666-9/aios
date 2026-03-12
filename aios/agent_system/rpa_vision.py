# RPA + 视觉理解系统
# 集成免费 OCR（Tesseract / PaddleOCR）
#
# STATUS: PROTOTYPE ONLY - NOT INTEGRATED
# 观察期内封存，不接入主链，不继续扩张
# 观察期后需通过安全审查才能集成
#
# RISK LEVEL: HIGH
# - 可能点错、输错、操作错对象
# - 必须先 dry-run、留审计日志、明确人工确认点
# - 禁止高风险窗口/区域操作

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 第三方库
try:
    import pyautogui
    import pytesseract
    from PIL import Image, ImageGrab
    import cv2
    import numpy as np
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("[INFO] Install: pip install pyautogui pytesseract pillow opencv-python")
    sys.exit(1)

# 配置 Tesseract 路径（Windows）
if sys.platform == 'win32':
    # 常见安装路径
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\A\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

# 安全设置
pyautogui.FAILSAFE = True  # 鼠标移到屏幕角落可中止
pyautogui.PAUSE = 0.5  # 每次操作后暂停 0.5 秒


class VisualOCR:
    """视觉理解 - OCR 引擎"""
    
    def __init__(self, engine='tesseract'):
        """
        初始化 OCR 引擎
        
        Args:
            engine: 'tesseract' 或 'paddleocr'
        """
        self.engine = engine
        self.paddle_ocr = None
        
        if engine == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            except ImportError:
                print("[WARN] PaddleOCR not installed, falling back to Tesseract")
                print("[INFO] Install: pip install paddleocr")
                self.engine = 'tesseract'
    
    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        截图
        
        Args:
            region: (x, y, width, height) 或 None（全屏）
        
        Returns:
            PIL Image
        """
        if region:
            return ImageGrab.grab(bbox=region)
        return ImageGrab.grab()
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        图像预处理（提高 OCR 准确率）
        
        Args:
            image: PIL Image
        
        Returns:
            处理后的 PIL Image
        """
        # 转为 OpenCV 格式
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 灰度化
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 降噪
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
        
        # 转回 PIL
        return Image.fromarray(denoised)
    
    def extract_text(self, image: Image.Image, lang='chi_sim+eng') -> str:
        """
        提取文本
        
        Args:
            image: PIL Image
            lang: 语言（tesseract: 'chi_sim+eng', paddleocr: 'ch'）
        
        Returns:
            提取的文本
        """
        # 预处理
        processed = self.preprocess_image(image)
        
        if self.engine == 'paddleocr' and self.paddle_ocr:
            result = self.paddle_ocr.ocr(np.array(processed), cls=True)
            if result and result[0]:
                return '\n'.join([line[1][0] for line in result[0]])
            return ""
        else:
            # Tesseract
            return pytesseract.image_to_string(processed, lang=lang)
    
    def find_text_location(self, image: Image.Image, target_text: str, lang='chi_sim+eng') -> Optional[Tuple[int, int]]:
        """
        查找文本位置
        
        Args:
            image: PIL Image
            target_text: 目标文本
            lang: 语言
        
        Returns:
            (x, y) 中心坐标，未找到返回 None
        """
        processed = self.preprocess_image(image)
        
        if self.engine == 'paddleocr' and self.paddle_ocr:
            result = self.paddle_ocr.ocr(np.array(processed), cls=True)
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    if target_text in text:
                        # 计算中心点
                        box = line[0]
                        x = int((box[0][0] + box[2][0]) / 2)
                        y = int((box[0][1] + box[2][1]) / 2)
                        return (x, y)
        else:
            # Tesseract
            data = pytesseract.image_to_data(processed, lang=lang, output_type=pytesseract.Output.DICT)
            for i, text in enumerate(data['text']):
                if target_text in text:
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    return (x, y)
        
        return None


class RPAController:
    """RPA 控制器"""
    
    def __init__(self, ocr_engine='tesseract'):
        """
        初始化 RPA 控制器
        
        Args:
            ocr_engine: OCR 引擎（'tesseract' 或 'paddleocr'）
        """
        self.ocr = VisualOCR(engine=ocr_engine)
        self.screen_width, self.screen_height = pyautogui.size()
        self.log_file = Path("rpa_log.jsonl")
    
    def log_action(self, action: str, details: Dict):
        """记录操作日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def move_to(self, x: int, y: int, duration: float = 0.5):
        """移动鼠标"""
        pyautogui.moveTo(x, y, duration=duration)
        self.log_action('move_to', {'x': x, 'y': y})
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, button='left', clicks=1):
        """点击"""
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button, clicks=clicks)
            self.log_action('click', {'x': x, 'y': y, 'button': button, 'clicks': clicks})
        else:
            pyautogui.click(button=button, clicks=clicks)
            self.log_action('click', {'button': button, 'clicks': clicks})
    
    def type_text(self, text: str, interval: float = 0.1):
        """输入文本"""
        pyautogui.write(text, interval=interval)
        self.log_action('type_text', {'text': text})
    
    def press_key(self, key: str):
        """按键"""
        pyautogui.press(key)
        self.log_action('press_key', {'key': key})
    
    def hotkey(self, *keys):
        """组合键"""
        pyautogui.hotkey(*keys)
        self.log_action('hotkey', {'keys': list(keys)})
    
    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None, save_path: Optional[str] = None) -> Image.Image:
        """截图"""
        img = self.ocr.screenshot(region)
        if save_path:
            img.save(save_path)
            self.log_action('screenshot', {'region': region, 'saved': save_path})
        return img
    
    def read_screen(self, region: Optional[Tuple[int, int, int, int]] = None, lang='chi_sim+eng') -> str:
        """读取屏幕文本"""
        img = self.screenshot(region)
        text = self.ocr.extract_text(img, lang)
        self.log_action('read_screen', {'region': region, 'text_length': len(text)})
        return text
    
    def find_and_click(self, target_text: str, region: Optional[Tuple[int, int, int, int]] = None, lang='chi_sim+eng') -> bool:
        """查找文本并点击"""
        img = self.screenshot(region)
        location = self.ocr.find_text_location(img, target_text, lang)
        
        if location:
            # 如果指定了区域，需要加上偏移
            if region:
                x = region[0] + location[0]
                y = region[1] + location[1]
            else:
                x, y = location
            
            self.click(x, y)
            self.log_action('find_and_click', {'target_text': target_text, 'found': True, 'x': x, 'y': y})
            return True
        else:
            self.log_action('find_and_click', {'target_text': target_text, 'found': False})
            return False
    
    def wait_for_text(self, target_text: str, timeout: int = 10, interval: float = 1.0, region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """等待文本出现"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            text = self.read_screen(region)
            if target_text in text:
                self.log_action('wait_for_text', {'target_text': target_text, 'found': True, 'elapsed': time.time() - start_time})
                return True
            time.sleep(interval)
        
        self.log_action('wait_for_text', {'target_text': target_text, 'found': False, 'timeout': timeout})
        return False
    
    def execute_workflow(self, workflow: List[Dict]) -> bool:
        """
        执行工作流
        
        Args:
            workflow: 工作流步骤列表
                [
                    {'action': 'click', 'x': 100, 'y': 200},
                    {'action': 'type_text', 'text': 'Hello'},
                    {'action': 'find_and_click', 'target_text': '确定'},
                    {'action': 'wait_for_text', 'target_text': '成功', 'timeout': 5}
                ]
        
        Returns:
            是否成功
        """
        try:
            for i, step in enumerate(workflow):
                action = step.get('action')
                print(f"[STEP {i+1}/{len(workflow)}] {action}")
                
                if action == 'click':
                    self.click(step.get('x'), step.get('y'), step.get('button', 'left'), step.get('clicks', 1))
                
                elif action == 'move_to':
                    self.move_to(step['x'], step['y'], step.get('duration', 0.5))
                
                elif action == 'type_text':
                    self.type_text(step['text'], step.get('interval', 0.1))
                
                elif action == 'press_key':
                    self.press_key(step['key'])
                
                elif action == 'hotkey':
                    self.hotkey(*step['keys'])
                
                elif action == 'screenshot':
                    self.screenshot(step.get('region'), step.get('save_path'))
                
                elif action == 'read_screen':
                    text = self.read_screen(step.get('region'), step.get('lang', 'chi_sim+eng'))
                    print(f"[OCR] {text[:100]}...")
                
                elif action == 'find_and_click':
                    if not self.find_and_click(step['target_text'], step.get('region'), step.get('lang', 'chi_sim+eng')):
                        print(f"[ERROR] Text not found: {step['target_text']}")
                        return False
                
                elif action == 'wait_for_text':
                    if not self.wait_for_text(step['target_text'], step.get('timeout', 10), step.get('interval', 1.0), step.get('region')):
                        print(f"[ERROR] Timeout waiting for: {step['target_text']}")
                        return False
                
                elif action == 'wait':
                    time.sleep(step.get('seconds', 1))
                
                else:
                    print(f"[WARN] Unknown action: {action}")
                
                # 步骤间延迟
                if step.get('delay'):
                    time.sleep(step['delay'])
            
            print("[SUCCESS] Workflow completed")
            return True
        
        except Exception as e:
            print(f"[ERROR] Workflow failed: {e}")
            self.log_action('workflow_error', {'error': str(e)})
            return False


# 示例工作流
def example_workflow():
    """示例：打开记事本并输入文本"""
    rpa = RPAController(ocr_engine='tesseract')
    
    workflow = [
        # 1. 打开运行对话框
        {'action': 'hotkey', 'keys': ['win', 'r']},
        {'action': 'wait', 'seconds': 0.5},
        
        # 2. 输入 notepad
        {'action': 'type_text', 'text': 'notepad'},
        {'action': 'press_key', 'key': 'enter'},
        {'action': 'wait', 'seconds': 1},
        
        # 3. 输入文本
        {'action': 'type_text', 'text': 'Hello from RPA + OCR!\n这是一个测试。'},
        {'action': 'wait', 'seconds': 1},
        
        # 4. 截图
        {'action': 'screenshot', 'save_path': 'notepad_screenshot.png'},
        
        # 5. 读取屏幕文本
        {'action': 'read_screen', 'lang': 'chi_sim+eng'},
        
        # 6. 关闭记事本（不保存）
        {'action': 'hotkey', 'keys': ['alt', 'f4']},
        {'action': 'wait', 'seconds': 0.5},
        {'action': 'find_and_click', 'target_text': '不保存'},
    ]
    
    rpa.execute_workflow(workflow)


if __name__ == '__main__':
    print("RPA + 视觉理解系统")
    print("=" * 50)
    print("OCR 引擎: Tesseract (免费)")
    print("备选: PaddleOCR (更准确，需安装)")
    print("=" * 50)
    
    # 检查 Tesseract 是否安装
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract 版本: {version}")
    except Exception as e:
        print(f"✗ Tesseract 未安装或未配置")
        print(f"  下载: https://github.com/UB-Mannheim/tesseract/wiki")
        print(f"  错误: {e}")
        sys.exit(1)
    
    # 运行示例
    print("\n运行示例工作流...")
    example_workflow()
