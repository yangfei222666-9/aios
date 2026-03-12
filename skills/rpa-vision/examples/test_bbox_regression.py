"""
bbox xyxy 契约回归测试

4 个回归：
1. bbox 契约检查 - 所有输出 bbox 满足 len==4, x2>x1, y2>y1
2. 中心点正确 - 已知框验证 center
3. 真实 OCR + dry-run - find_text + bbox_center + dry_run click
4. 可视化检查 - bbox 红框 + 中心点十字
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from bbox_utils import bbox_width, bbox_height, bbox_center, validate_bbox_xyxy
from PIL import Image, ImageDraw

print("=== bbox xyxy 契约回归测试 ===\n")

passed = 0
failed = 0

# ==================== 回归 1：bbox 契约检查 ====================
print("回归 1：bbox 契约检查")
print("-" * 40)

test_bboxes = [
    (380, 20, 412, 44),   # 正常
    (100, 200, 300, 250),  # 正常
    (0, 0, 1920, 1080),    # 全屏
]

bad_bboxes = [
    (412, 20, 380, 44),   # x2 < x1
    (100, 250, 300, 200),  # y2 < y1
    (100, 100, 100, 200),  # x2 == x1
]

for bbox in test_bboxes:
    try:
        validate_bbox_xyxy(bbox)
        print(f"  ✓ {bbox} → valid xyxy")
        passed += 1
    except ValueError as e:
        print(f"  ✗ {bbox} → 应该 valid 但报错: {e}")
        failed += 1

for bbox in bad_bboxes:
    try:
        validate_bbox_xyxy(bbox)
        print(f"  ✗ {bbox} → 应该报错但通过了")
        failed += 1
    except ValueError:
        print(f"  ✓ {bbox} → 正确拒绝")
        passed += 1

print()

# ==================== 回归 2：中心点正确 ====================
print("回归 2：中心点正确")
print("-" * 40)

bbox = (380, 20, 412, 44)
expected_center = (396, 32)
actual_center = bbox_center(bbox)

if actual_center == expected_center:
    print(f"  ✓ bbox_center({bbox}) == {actual_center}")
    passed += 1
else:
    print(f"  ✗ bbox_center({bbox}) == {actual_center}, expected {expected_center}")
    failed += 1

# 额外验证 width/height
expected_w = 32
expected_h = 24
actual_w = bbox_width(bbox)
actual_h = bbox_height(bbox)

if actual_w == expected_w:
    print(f"  ✓ bbox_width({bbox}) == {actual_w}")
    passed += 1
else:
    print(f"  ✗ bbox_width({bbox}) == {actual_w}, expected {expected_w}")
    failed += 1

if actual_h == expected_h:
    print(f"  ✓ bbox_height({bbox}) == {actual_h}")
    passed += 1
else:
    print(f"  ✗ bbox_height({bbox}) == {actual_h}, expected {expected_h}")
    failed += 1

print()

# ==================== 回归 3：真实 OCR + dry-run ====================
print("回归 3：真实 OCR + dry-run")
print("-" * 40)

try:
    from main import RPAVision
    
    rpa = RPAVision(debug_mode=True, dry_run=True)
    screenshot = rpa.capture_screen()
    ocr_result = rpa.extract_text()
    
    if not ocr_result:
        print("  ⚠ OCR 返回空结果，跳过真实验证")
    else:
        # 检查所有 OCR 结果的 bbox 契约
        all_valid = True
        for item in ocr_result:
            try:
                validate_bbox_xyxy(item["bbox"])
            except ValueError as e:
                print(f"  ✗ OCR 输出违反 xyxy 契约: {item['text'][:20]} → {e}")
                all_valid = False
                failed += 1
        
        if all_valid:
            print(f"  ✓ 所有 {len(ocr_result)} 个 OCR 结果均符合 xyxy 契约")
            passed += 1
        
        # 尝试 find_text
        # 用 OCR 结果中的第一个非空文本
        test_text = None
        for item in ocr_result:
            t = item["text"].strip()
            if len(t) >= 2:
                test_text = t[:10]
                break
        
        if test_text:
            result = rpa.find_text(test_text, fuzzy=True, threshold=0.6)
            if result:
                x1, y1, x2, y2 = result["bbox"]
                cx, cy = bbox_center(result["bbox"])
                validate_bbox_xyxy(result["bbox"])
                
                print(f"  ✓ find_text('{test_text}') → bbox=({x1},{y1},{x2},{y2})")
                print(f"    [DRY-RUN] click({cx}, {cy})")
                passed += 1
            else:
                print(f"  ⚠ find_text('{test_text}') 返回 None")

except Exception as e:
    print(f"  ✗ 真实 OCR 测试失败: {e}")
    failed += 1

print()

# ==================== 回归 4：可视化检查 ====================
print("回归 4：可视化检查")
print("-" * 40)

try:
    if ocr_result and screenshot:
        annotated = screenshot.copy()
        draw = ImageDraw.Draw(annotated)
        
        for item in ocr_result[:10]:  # 只画前 10 个
            x1, y1, x2, y2 = item["bbox"]
            cx, cy = bbox_center(item["bbox"])
            
            # bbox 红框
            draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=2)
            
            # 中心点绿点
            draw.ellipse([(cx-5, cy-5), (cx+5, cy+5)], fill="lime")
            
            # 十字准星
            draw.line([(cx-15, cy), (cx+15, cy)], fill="blue", width=2)
            draw.line([(cx, cy-15), (cx, cy+15)], fill="blue", width=2)
        
        output_path = Path(__file__).parent.parent / "debug_output" / "regression_bbox_xyxy.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        annotated.save(output_path)
        print(f"  ✓ 可视化图已保存: {output_path}")
        passed += 1
    else:
        print("  ⚠ 无截图/OCR 数据，跳过可视化")

except Exception as e:
    print(f"  ✗ 可视化失败: {e}")
    failed += 1

# ==================== 汇总 ====================
print()
print("=" * 40)
print(f"结果: {passed} passed, {failed} failed")

if failed == 0:
    print("✓ 所有回归测试通过 — xyxy 契约统一完成")
else:
    print("✗ 存在失败项，需要检查")

sys.exit(0 if failed == 0 else 1)
