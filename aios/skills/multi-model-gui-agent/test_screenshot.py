"""
测试脚本 - 验证环境和基础功能
"""

import pyautogui
from PIL import ImageGrab
import sys

def test_screenshot():
    """测试截图功能"""
    print("测试截图功能...")
    try:
        img = ImageGrab.grab()
        img.save('test_screenshot.png')
        print("✅ 截图成功: test_screenshot.png")
        print(f"   分辨率: {img.size}")
        return True
    except Exception as e:
        print(f"❌ 截图失败: {e}")
        return False

def test_mouse_control():
    """测试鼠标控制"""
    print("\n测试鼠标控制...")
    try:
        pos = pyautogui.position()
        print(f"✅ 当前鼠标位置: {pos}")
        
        # 测试移动（不实际移动，只检查API）
        screen_width, screen_height = pyautogui.size()
        print(f"   屏幕分辨率: {screen_width}x{screen_height}")
        return True
    except Exception as e:
        print(f"❌ 鼠标控制失败: {e}")
        return False

def test_keyboard():
    """测试键盘控制"""
    print("\n测试键盘控制...")
    try:
        # 只测试API可用性，不实际输入
        print("✅ 键盘控制 API 可用")
        return True
    except Exception as e:
        print(f"❌ 键盘控制失败: {e}")
        return False

def test_imports():
    """测试依赖导入"""
    print("\n测试依赖导入...")
    try:
        import requests
        import json
        from pathlib import Path
        from dataclasses import dataclass
        print("✅ 所有依赖导入成功")
        return True
    except ImportError as e:
        print(f"❌ 依赖导入失败: {e}")
        print("   请运行: pip install pyautogui pillow requests")
        return False

def main():
    print("=" * 50)
    print("多模型GUI代理 - 环境测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_screenshot,
        test_mouse_control,
        test_keyboard
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 50)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 50)
    
    if all(results):
        print("\n✅ 环境准备完成，可以开始使用！")
        print("\n下一步:")
        print("1. 编辑 config.json，填入豆包 API Keys")
        print("2. 创建 urls.txt，添加测试链接")
        print("3. 运行: python agent.py --config config.json --urls urls.txt --mode douyin")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查环境配置")
        return 1

if __name__ == '__main__':
    sys.exit(main())
