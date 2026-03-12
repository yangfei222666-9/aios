"""
MockEngine - 用于测试 UIVisionAgent 接口流程
不需要真实模型，直接返回模拟输出
"""

from ui_vision_agent import VisionEngine
from PIL import Image


class MockEngine(VisionEngine):
    """Mock 视觉引擎 - 用于测试"""
    
    def __init__(self):
        self.call_count = 0
    
    def infer(self, screenshot: Image, task_desc: str) -> str:
        """返回模拟的 UI-TARS 输出"""
        self.call_count += 1
        
        # 根据任务描述返回不同的 mock 输出
        if "登录" in task_desc or "login" in task_desc.lower():
            return """Thought: 我看到登录按钮在屏幕右上角，坐标约为 (850, 120)
Action: click(start_box='(850,120)')"""
        
        elif "输入" in task_desc or "type" in task_desc.lower():
            # 提取要输入的文本
            if "用户名" in task_desc:
                text = "test_user"
            elif "密码" in task_desc:
                text = "password123"
            else:
                text = "mock_text"
            return f"""Thought: 我看到输入框，准备输入文本
Action: type(text='{text}')"""
        
        elif "滚动" in task_desc or "scroll" in task_desc.lower():
            direction = "down" if "下" in task_desc or "down" in task_desc.lower() else "up"
            return f"""Thought: 准备向{direction}滚动页面
Action: scroll(direction='{direction}')"""
        
        elif "按" in task_desc or "press" in task_desc.lower():
            key = "enter"
            if "回车" in task_desc or "enter" in task_desc.lower():
                key = "enter"
            elif "esc" in task_desc.lower():
                key = "esc"
            return f"""Thought: 准备按下 {key} 键
Action: press(key='{key}')"""
        
        else:
            # 未识别的任务
            return """Thought: 无法理解任务描述
Action: none()"""


if __name__ == "__main__":
    from ui_vision_agent import UIVisionAgent, ActionExecutor
    from PIL import Image
    import io
    
    print("=" * 60)
    print("UIVisionAgent 接口测试（Mock 模式）")
    print("=" * 60)
    
    # 创建 mock 截图（1x1 像素，只是占位）
    mock_screenshot = Image.new("RGB", (1920, 1080), color=(255, 255, 255))
    
    # 初始化 Agent（使用 MockEngine）
    agent = UIVisionAgent(engine=MockEngine())
    executor = ActionExecutor()
    
    # 测试用例
    test_cases = [
        "点击登录按钮",
        "输入用户名",
        "向下滚动页面",
        "按回车键",
        "这是一个无法识别的任务"
    ]
    
    for i, task in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {task}")
        print("-" * 60)
        
        # 感知
        result = agent.perceive(task, mock_screenshot)
        
        print(f"Status: {result.status}")
        print(f"Thought: {result.thought}")
        print(f"Action: {result.action.to_dict()}")
        print(f"Confidence: {result.confidence}")
        
        # 判断是否执行
        if result.status == "ok" and result.confidence >= 0.8:
            print("✅ 置信度足够，可以执行")
            # 注意：这里不真实执行，只是演示流程
            # exec_result = executor.execute(result.action)
            # print(f"执行结果: {exec_result}")
        else:
            print("⚠️ 置信度不足或状态不确定，不执行")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
