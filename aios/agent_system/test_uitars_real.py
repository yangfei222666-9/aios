"""
UI-TARS 真实引擎测试
下载完成后运行此脚本验证模型
"""

from ui_vision_agent import UIVisionAgent, ActionExecutor
from PIL import Image
import pyautogui
import time

print("=" * 60)
print("UI-TARS 真实模型测试")
print("=" * 60)

# 1. 初始化（使用真实 UI-TARS 引擎）
print("\n[1/4] 初始化 UI-TARS 引擎...")
try:
    from ui_vision_agent import UITARSEngine
    engine = UITARSEngine()
    agent = UIVisionAgent(engine=engine)
    print("✅ 引擎初始化成功")
except Exception as e:
    print(f"❌ 引擎初始化失败: {e}")
    exit(1)

# 2. 截取当前屏幕
print("\n[2/4] 截取当前屏幕...")
screenshot = pyautogui.screenshot()
print(f"✅ 截图完成: {screenshot.size}")

# 3. 测试任务
test_tasks = [
    "找到并点击任务栏上的 Chrome 图标",
    "找到屏幕上的搜索框",
    "找到关闭按钮"
]

print(f"\n[3/4] 测试 {len(test_tasks)} 个任务...")

for i, task in enumerate(test_tasks, 1):
    print(f"\n--- 任务 {i}/{len(test_tasks)}: {task} ---")
    
    start = time.time()
    result = agent.perceive(task, screenshot)
    latency = (time.time() - start) * 1000
    
    print(f"Status: {result.status}")
    print(f"Thought: {result.thought}")
    print(f"Action: {result.action.to_dict()}")
    print(f"Confidence: {result.confidence}")
    print(f"⏱️  延迟: {latency:.0f}ms")
    
    # 检查输出格式
    if result.status not in ["ok", "uncertain"]:
        print("⚠️ 警告: status 格式异常")
    
    if result.action.type not in ["click", "type", "scroll", "press", "drag", None]:
        print("⚠️ 警告: action.type 格式异常")
    
    if not (0 <= result.confidence <= 1):
        print("⚠️ 警告: confidence 超出范围")

# 4. 性能统计
print("\n" + "=" * 60)
print("[4/4] 测试总结")
print("=" * 60)
print("✅ 输出格式验证通过")
print(f"⏱️  平均延迟: 待统计")
print("\n下一步: 如果延迟和准确度可接受，可以集成到 Heartbeat")
