"""
UIVisionAgent - 太极OS 视觉感知层
负责：截图 → 理解界面 → 输出操作
不负责：任务规划、状态管理、执行操作
"""

from typing import Dict, Any, Optional
from PIL import Image
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class Action:
    """操作对象"""
    type: str  # click | type | scroll | press | drag
    params: Dict[str, Any]
    
    def to_dict(self):
        return {"type": self.type, "params": self.params}


@dataclass
class PerceptionResult:
    """感知结果"""
    status: str  # ok | uncertain
    thought: str
    action: Action
    confidence: float
    
    def to_dict(self):
        return {
            "status": self.status,
            "thought": self.thought,
            "action": self.action.to_dict(),
            "confidence": self.confidence
        }


class VisionEngine:
    """视觉引擎接口（可替换实现）"""
    
    def infer(self, screenshot: Image, task_desc: str) -> str:
        """
        推理接口
        Args:
            screenshot: PIL.Image
            task_desc: 任务描述
        Returns:
            原始模型输出（字符串）
        """
        raise NotImplementedError


class UITARSEngine(VisionEngine):
    """UI-TARS 1.5-7B 引擎"""
    
    def __init__(self, model_path: str = "ByteDance-Seed/UI-TARS-1.5-7B"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
    
    def load(self):
        """延迟加载模型（避免启动时占用显存）"""
        if self.model is not None:
            return
        
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch
            
            self.model = AutoModel.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                trust_remote_code=True
            ).eval().cuda()
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            print(f"✅ UI-TARS 模型加载成功: {self.model_path}")
        except Exception as e:
            print(f"❌ UI-TARS 模型加载失败: {e}")
            raise
    
    def infer(self, screenshot: Image, task_desc: str) -> str:
        """调用 UI-TARS 推理"""
        self.load()
        
        # 构造 prompt（参考 UI-TARS 官方格式）
        prompt = f"Task: {task_desc}\nPlease analyze the screenshot and output the action."
        
        # 调用模型
        response, _ = self.model.chat(
            self.tokenizer,
            screenshot,
            prompt,
            generation_config={"max_new_tokens": 512, "do_sample": False},
            history=None,
            return_history=True
        )
        
        return response


class UIVisionAgent:
    """GUI 视觉代理 - 太极OS 视觉感知层"""
    
    def __init__(self, engine: Optional[VisionEngine] = None):
        """
        Args:
            engine: 视觉引擎（默认 UI-TARS）
        """
        self.engine = engine or UITARSEngine()
    
    def perceive(self, task_desc: str, screenshot: Image) -> PerceptionResult:
        """
        感知界面，输出可执行操作
        
        Args:
            task_desc: 任务描述（如"点击登录按钮"）
            screenshot: PIL.Image 对象
        
        Returns:
            PerceptionResult
        """
        try:
            # 1. 调用视觉引擎
            raw_response = self.engine.infer(screenshot, task_desc)
            
            # 2. 解析输出
            parsed = self._parse_response(raw_response)
            
            # 3. 构造结果
            return PerceptionResult(
                status="ok" if parsed["valid"] else "uncertain",
                thought=parsed["thought"],
                action=Action(type=parsed["action_type"], params=parsed["action_params"]),
                confidence=self._calc_confidence(parsed)
            )
        
        except Exception as e:
            # 异常情况返回 uncertain
            return PerceptionResult(
                status="uncertain",
                thought=f"推理失败: {str(e)}",
                action=Action(type="none", params={}),
                confidence=0.0
            )
    
    def _parse_response(self, raw: str) -> Dict[str, Any]:
        """
        解析 UI-TARS 输出
        
        格式示例：
        Thought: 我看到登录按钮在右上角
        Action: click(start_box='(850,120)')
        """
        lines = raw.strip().split("\n")
        thought = ""
        action_str = ""
        
        for line in lines:
            if line.startswith("Thought:"):
                thought = line.replace("Thought:", "").strip()
            elif line.startswith("Action:"):
                action_str = line.replace("Action:", "").strip()
        
        # 解析 action
        action_type, action_params = self._parse_action(action_str)
        
        return {
            "valid": bool(action_type and action_params),
            "thought": thought or "无推理过程",
            "action_type": action_type,
            "action_params": action_params
        }
    
    def _parse_action(self, action_str: str) -> tuple:
        """
        解析 action 字符串
        
        示例：
        - click(start_box='(850,120)') → ("click", {"x": 850, "y": 120})
        - type(text='username') → ("type", {"text": "username"})
        - scroll(direction='down') → ("scroll", {"direction": "down", "amount": 3})
        """
        import re
        
        # click
        match = re.search(r"click\(start_box='?\((\d+),(\d+)\)'?\)", action_str)
        if match:
            return "click", {"x": int(match.group(1)), "y": int(match.group(2))}
        
        # type
        match = re.search(r"type\(text='([^']+)'\)", action_str)
        if match:
            return "type", {"text": match.group(1)}
        
        # scroll
        match = re.search(r"scroll\(direction='(up|down)'\)", action_str)
        if match:
            return "scroll", {"direction": match.group(1), "amount": 3}
        
        # press
        match = re.search(r"press\(key='([^']+)'\)", action_str)
        if match:
            return "press", {"key": match.group(1)}
        
        # 未识别
        return None, {}
    
    def _calc_confidence(self, parsed: Dict) -> float:
        """
        计算置信度
        
        规则：
        - 解析成功 + 坐标合理 → 0.9
        - 解析成功但坐标异常 → 0.5
        - 解析失败 → 0.0
        """
        if not parsed["valid"]:
            return 0.0
        
        # 检查坐标合理性（假设屏幕最大 4K）
        if parsed["action_type"] == "click":
            x, y = parsed["action_params"].get("x", 0), parsed["action_params"].get("y", 0)
            if 0 <= x <= 3840 and 0 <= y <= 2160:
                return 0.9
            else:
                return 0.5
        
        # 其他操作类型默认 0.9
        return 0.9


# ============================================================
# 执行器（可选，调用方可以自己执行）
# ============================================================

class ActionExecutor:
    """操作执行器（基于 pyautogui）"""
    
    def __init__(self):
        try:
            import pyautogui
            self.pyautogui = pyautogui
            # 安全设置
            self.pyautogui.FAILSAFE = True  # 鼠标移到左上角可中断
            self.pyautogui.PAUSE = 0.5  # 每次操作间隔 0.5s
        except ImportError:
            print("⚠️ pyautogui 未安装，执行器不可用")
            self.pyautogui = None
    
    def execute(self, action: Action) -> Dict[str, Any]:
        """
        执行操作
        
        Returns:
            {"success": bool, "error": str}
        """
        if self.pyautogui is None:
            return {"success": False, "error": "pyautogui 未安装"}
        
        try:
            if action.type == "click":
                x, y = action.params["x"], action.params["y"]
                self.pyautogui.click(x, y)
            
            elif action.type == "type":
                text = action.params["text"]
                self.pyautogui.write(text, interval=0.05)
            
            elif action.type == "scroll":
                direction = action.params["direction"]
                amount = action.params.get("amount", 3)
                clicks = amount if direction == "down" else -amount
                self.pyautogui.scroll(clicks * 100)
            
            elif action.type == "press":
                key = action.params["key"]
                self.pyautogui.press(key)
            
            else:
                return {"success": False, "error": f"未知操作类型: {action.type}"}
            
            return {"success": True, "error": None}
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    # 初始化
    agent = UIVisionAgent()
    executor = ActionExecutor()
    
    # 加载截图
    screenshot = Image.open("screenshot.png")
    
    # 感知
    result = agent.perceive("点击登录按钮", screenshot)
    
    print(f"Status: {result.status}")
    print(f"Thought: {result.thought}")
    print(f"Action: {result.action.to_dict()}")
    print(f"Confidence: {result.confidence}")
    
    # 执行（可选）
    if result.status == "ok" and result.confidence >= 0.8:
        exec_result = executor.execute(result.action)
        print(f"Execution: {exec_result}")
