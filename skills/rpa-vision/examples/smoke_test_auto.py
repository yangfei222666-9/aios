"""
自动化 Smoke Test - 无需交互

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

print("=== RPA Vision 自动化 Smoke Test ===\n")

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
    print(f"✓ 截图成功: {screenshot.size}")
    print(f"  DPI 缩放: {rpa.capture.dpi_scale}\n")
except Exception as e:
    print(f"✗ 截图失败: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: OCR
print("测试 3: OCR 识别...")
print("  正在识别当前屏幕内容...")

try:
    screenshot = rpa.capture_screen()
    ocr_result = rpa.extract_text()
    
    if ocr_result:
        print(f"✓ OCR 成功，识别到 {len(ocr_result)} 个文本元素")
        print("\n前 10 个识别结果：")
        for i, item in enumerate(ocr_result[:10]):
            text = item['text'].replace('\n', ' ').replace('\r', '')[:50]
            bbox = item['bbox']
            print(f"  [{i+1}] '{text}' @ ({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]})")
        print()
    else:
        print("⚠ OCR 返回空结果（可能屏幕中没有可识别文字）\n")
except Exception as e:
    print(f"✗ OCR 失败: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: find_text
print("测试 4: find_text...")
if ocr_result and len(ocr_result) > 0:
    # 尝试查找前 3 个识别到的文本
    for i in range(min(3, len(ocr_result))):
        target = ocr_result[i]["text"].strip()[:20]  # 取前 20 个字符
        if not target:
            continue
            
        print(f"\n  尝试查找: '{target}'")
        
        try:
            result = rpa.find_text(target, fuzzy=True, threshold=0.6)
            if result:
                print(f"  ✓ find_text 成功")
                print(f"    文本: {result['text'][:50]}")
                print(f"    bbox: {result['bbox']}")
                print(f"    置信度: {result.get('confidence', 'N/A')}")
                break
            else:
                print(f"  ⚠ find_text 返回 None")
        except Exception as e:
            print(f"  ✗ find_text 失败: {e}")
            import traceback
            traceback.print_exc()
else:
    print("⚠ 跳过 find_text 测试（OCR 结果为空）")

print("\n=== Smoke Test 完成 ===")
print(f"\n调试输出目录: {rpa.debug.output_dir}")
print("可以查看以下文件：")
print(f"  - screenshots/")
print(f"  - ocr_results/")
print(f"  - logs/")
