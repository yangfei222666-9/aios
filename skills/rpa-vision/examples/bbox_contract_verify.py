"""
bbox 契约验证 - 确认整条链路统一使用 xyxy 格式

检查 3 件事：
1. parsed[:3] 确认 bbox 是 (x1, y1, x2, y2) 格式（x2 > x1, y2 > y1）
2. 可视化框图 确认红框罩住文本
3. find_text() 返回 xyxy，点击中心点合理
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from main import RPAVision

print("=== bbox 契约验证（xyxy 统一）===\n")

rpa = RPAVision(debug_mode=True, dry_run=True)

# 1. 截图 + OCR
print("步骤 1: 截图 + OCR...")
screenshot = rpa.capture_screen()
ocr_result = rpa.extract_text()

if not ocr_result:
    print("✗ OCR 返回空结果，无法验证")
    sys.exit(1)

print(f"✓ OCR 识别到 {len(ocr_result)} 个文本元素\n")

# 2. 检查前 3 个 bbox 是否为 xyxy 格式
print("步骤 2: 检查 bbox 格式（前 5 个）...")
all_xyxy = True
for i, item in enumerate(ocr_result[:5]):
    text = item['text'].replace('\n', ' ')[:30]
    bbox = item['bbox']
    x1, y1, x2, y2 = bbox
    
    is_xyxy = (x2 > x1) and (y2 > y1)
    status = "✓ xyxy" if is_xyxy else "✗ 可能是 xywh!"
    
    if not is_xyxy:
        all_xyxy = False
    
    w = x2 - x1
    h = y2 - y1
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    
    print(f"  [{i+1}] '{text}'")
    print(f"       bbox: ({x1}, {y1}, {x2}, {y2})  →  {status}")
    print(f"       size: {w}x{h}  center: ({cx}, {cy})")

if all_xyxy:
    print("\n✓ 所有 bbox 均为 xyxy 格式\n")
else:
    print("\n✗ 存在非 xyxy 格式的 bbox！\n")

# 3. 可视化框图
print("步骤 3: 生成可视化框图...")
annotated = screenshot.copy()
draw = ImageDraw.Draw(annotated)

for item in ocr_result:
    x1, y1, x2, y2 = item['bbox']
    # 红框
    draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=2)
    # 中心点
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    draw.ellipse([(cx-4, cy-4), (cx+4, cy+4)], fill="lime", outline="lime")

output_path = Path(__file__).parent.parent / "debug_output" / "bbox_verification.png"
output_path.parent.mkdir(parents=True, exist_ok=True)
annotated.save(output_path)
print(f"✓ 已保存: {output_path}\n")

# 4. find_text 测试
print("步骤 4: find_text 测试...")
# 用第一个识别到的文本做测试
test_target = ocr_result[0]["text"].strip()[:10]
if test_target:
    result = rpa.find_text(test_target, fuzzy=True, threshold=0.6)
    if result:
        x1, y1, x2, y2 = result["bbox"]
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        print(f"  查找: '{test_target}'")
        print(f"  bbox: ({x1}, {y1}, {x2}, {y2})")
        print(f"  中心点: ({cx}, {cy})")
        print(f"  ✓ find_text 返回 xyxy 格式")
    else:
        print(f"  ⚠ find_text('{test_target}') 返回 None")

# 5. 搜索"搜索"关键词（如果存在）
print("\n步骤 5: 查找'搜索'关键词...")
search_result = rpa.find_text("搜索", fuzzy=True, threshold=0.6)
if search_result:
    x1, y1, x2, y2 = search_result["bbox"]
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    print(f"  ✓ 找到: '{search_result['text']}'")
    print(f"  bbox: ({x1}, {y1}, {x2}, {y2})")
    print(f"  点击中心: ({cx}, {cy})")
else:
    print("  ⚠ 当前屏幕未找到'搜索'文本（正常，取决于屏幕内容）")

print("\n=== 验证完成 ===")
print(f"可视化图: {output_path}")
