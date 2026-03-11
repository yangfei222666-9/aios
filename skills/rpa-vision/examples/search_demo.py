"""
Demo 1: 网页搜索

演示如何使用 RPA Vision 自动化网页搜索：
1. 打开浏览器（假设已打开）
2. 定位搜索框
3. 输入关键词
4. 回车
5. 等待结果页
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import RPAVision


def main():
    print("=== Demo 1: 网页搜索 ===\n")
    
    # 初始化 RPA Vision
    rpa = RPAVision(debug_mode=True, dry_run=False)
    
    print("步骤 1: 请打开浏览器并访问搜索引擎（如 Google/Bing）")
    input("准备好后按 Enter 继续...")
    
    try:
        # 步骤 2: 定位搜索框
        print("\n步骤 2: 定位搜索框...")
        rpa.capture_screen()
        rpa.extract_text()
        
        # 尝试查找搜索框（通过查找"搜索"或"Search"文本）
        search_box = rpa.find_text("搜索", fuzzy=True)
        if not search_box:
            search_box = rpa.find_text("Search", fuzzy=True)
        
        if search_box:
            print(f"✓ 找到搜索框: {search_box['text']}")
            
            # 步骤 3: 点击搜索框
            print("\n步骤 3: 点击搜索框...")
            x1, y1, x2, y2 = search_box["bbox"]
            rpa.click((x1 + x2) // 2, (y1 + y2) // 2)
            
            # 步骤 4: 输入关键词
            print("\n步骤 4: 输入关键词...")
            keyword = "OpenClaw AI Assistant"
            rpa.type_text(keyword)
            print(f"✓ 已输入: {keyword}")
            
            # 步骤 5: 回车
            print("\n步骤 5: 按 Enter 搜索...")
            rpa.press_key("enter")
            
            # 步骤 6: 等待结果页
            print("\n步骤 6: 等待搜索结果...")
            if rpa.wait_for_text("结果", timeout=10, fuzzy=True):
                print("✓ 搜索完成！")
            else:
                print("⚠ 未检测到结果页（可能已加载但未识别到'结果'文本）")
        
        else:
            print("✗ 未找到搜索框")
            print("提示: 请确保浏览器窗口在前台，且搜索框可见")
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")
    
    finally:
        print(f"\n调试输出已保存到: {rpa.debug.output_dir}")
        print("可以查看截图、OCR 结果和动作日志")


if __name__ == "__main__":
    main()
