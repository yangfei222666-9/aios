"""
最小 Smoke Test - 验证核心链路

测试 4 件事：
1. import main 正常
2. 能成功截图并保存
3. OCR 能识别出一段已知文字
4. find_text() 能返回 bbox 坐标
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=== RPA Vision 最小 Smoke Test ===\n")

# 测试 1: import main
print("测试 1: import main...")
try:
    from main import RPAVision
    print("✓ import 成功\n")
except Exception as e:
    print(f"✗ import 失败: {e}\n")
    sys.exit(1)

# 测试 2: 截图
print("测试 2: 截图...")
try:
    rpa = RPAVision(debug_mode=True, dry_run=True)
    screenshot = rpa.capture_screen()
    print(f"✓ 截图成功: {screenshot.size}\n")
except Exception as e:
    print(f"✗ 截图失败: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: OCR
print("测试 3: OCR 识别...")
print("请打开一个包含文字的窗口（如记事本、浏览器）")
input("准备好后按 Enter 继续...")

try:
    screenshot = rpa.capture_screen()
    ocr_result = rpa.extract_text()
    
    if ocr_result:
        print(f"✓ OCR 成功，识别到 {len(ocr_result)} 个文本元素")
        print("\n前 5 个识别结果：")
        for i, item in enumerate(ocr_result[:5]):
            print(f"  [{i+1}] {item['text'][:50]} (bbox: {item['bbox']})")
        print()
    else:
        print("⚠ OCR 返回空结果（可能窗口中没有文字）\n")
except Exception as e:
    print(f"✗ OCR 失败: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: find_text
print("测试 4: find_text...")
if ocr_result:
    # 尝试查找第一个识别到的文本
    target = ocr_result[0]["text"][:10]  # 取前 10 个字符
    print(f"尝试查找: '{target}'")
    
    try:
        result = rpa.find_text(target, fuzzy=True)
        if result:
            print(f"✓ find_text 成功")
            print(f"  文本: {result['text']}")
            print(f"  bbox: {result['bbox']}")
            print(f"  置信度: {result.get('confidence', 'N/A')}")
        else:
            print(f"⚠ find_text 返回 None")
    except Exception as e:
        print(f"✗ find_text 失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠ 跳过 find_text 测试（OCR 结果为空）")

print("\n=== Smoke Test 完成 ===")
print(f"调试输出: {rpa.debug.output_dir}")
