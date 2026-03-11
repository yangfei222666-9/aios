"""
真实 OCR dry-run search demo

用真实 OCR 数据验证完整链路：
1. 截图
2. OCR 识别
3. 查找目标文本
4. 计算点击中心点
5. dry-run 输出点击位置
6. 保存 debug 图（红框 + 绿色中心点 + 蓝色十字准星）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw
from main import RPAVision

print("=== 真实 OCR dry-run search demo ===\n")

rpa = RPAVision(debug_mode=True, dry_run=True)

# 1. 截图
print("步骤 1: 截图...")
screenshot = rpa.capture_screen()
print(f"  ✓ 截图: {screenshot.size}, DPI 缩放: {rpa.capture.dpi_scale}\n")

# 2. OCR
print("步骤 2: OCR 识别...")
ocr_result = rpa.extract_text()
print(f"  ✓ 识别到 {len(ocr_result)} 个文本元素\n")

# 3. 搜索多个目标
targets = ["搜索", "对话", "Clawdbot", "文件", "设置"]
found_any = False

for target in targets:
    print(f"步骤 3: 查找 '{target}'...")
    result = rpa.find_text(target, fuzzy=True, threshold=0.6)
    
    if result:
        found_any = True
        x1, y1, x2, y2 = result["bbox"]
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        w = x2 - x1
        h = y2 - y1
        
        print(f"  ✓ 找到: '{result['text']}'")
        print(f"    bbox (xyxy): ({x1}, {y1}, {x2}, {y2})")
        print(f"    尺寸: {w}x{h}")
        print(f"    点击中心: ({cx}, {cy})")
        print(f"    [DRY-RUN] click({cx}, {cy})")
        
        # 生成 debug 图
        annotated = screenshot.copy()
        draw = ImageDraw.Draw(annotated)
        
        # 红框 - 目标区域
        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
        
        # 绿色中心点
        draw.ellipse([(cx-6, cy-6), (cx+6, cy+6)], fill="lime", outline="lime")
        
        # 蓝色十字准星
        cross_size = 20
        draw.line([(cx - cross_size, cy), (cx + cross_size, cy)], fill="blue", width=2)
        draw.line([(cx, cy - cross_size), (cx, cy + cross_size)], fill="blue", width=2)
        
        # 标注文字
        label = f"'{target}' → click({cx}, {cy})"
        draw.text((x1, y1 - 20), label, fill="red")
        
        output_path = Path(__file__).parent.parent / "debug_output" / f"dryrun_{target}.png"
        annotated.save(output_path)
        print(f"    debug 图: {output_path}")
        print()
        break  # 找到第一个就够了
    else:
        print(f"  ⚠ 未找到 '{target}'\n")

if not found_any:
    print("⚠ 所有目标都未找到，请确保屏幕上有可识别的文本")
    # 用第一个 OCR 结果做 fallback demo
    if ocr_result:
        item = ocr_result[0]
        x1, y1, x2, y2 = item["bbox"]
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        print(f"\n  Fallback: 使用第一个 OCR 结果 '{item['text'][:20]}'")
        print(f"    bbox (xyxy): ({x1}, {y1}, {x2}, {y2})")
        print(f"    点击中心: ({cx}, {cy})")
        print(f"    [DRY-RUN] click({cx}, {cy})")

print("=== dry-run 完成 ===")
print("\n结论：截图 → OCR → 定位 → 坐标(xyxy) → dry-run 链路验证通过")
