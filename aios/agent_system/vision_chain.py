#!/usr/bin/env python3
"""
太极OS 最小视觉链 v0.1
- 截屏（全屏 / 指定区域）
- OCR 文字提取（Tesseract）
- 基础截图解析（窗口标题、文字内容）

依赖：mss, Pillow, pytesseract, pyautogui
Tesseract 路径：C:/Program Files/Tesseract-OCR/tesseract.exe
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import mss
import pytesseract
from PIL import Image, ImageFilter

# Tesseract 配置
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# 输出目录
SCREENSHOT_DIR = Path(__file__).parent / "data" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def capture_screen(region=None, monitor=1):
    """截屏
    
    Args:
        region: (left, top, width, height) 或 None 全屏
        monitor: 显示器编号，默认 1（主屏）
    
    Returns:
        PIL.Image
    """
    with mss.mss() as sct:
        if region:
            left, top, width, height = region
            area = {"left": left, "top": top, "width": width, "height": height}
        else:
            area = sct.monitors[monitor]
        
        shot = sct.grab(area)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def ocr_image(img, lang="eng", preprocess=True):
    """OCR 提取文字
    
    Args:
        img: PIL.Image
        lang: 语言，eng / chi_sim / eng+chi_sim
        preprocess: 是否预处理（灰度+锐化）
    
    Returns:
        str: 提取的文字
    """
    if preprocess:
        img = img.convert("L")  # 灰度
        img = img.filter(ImageFilter.SHARPEN)  # 锐化
    
    text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()


def ocr_with_boxes(img, lang="eng", preprocess=True):
    """OCR 提取文字 + 位置信息
    
    Returns:
        list[dict]: [{text, left, top, width, height, conf}, ...]
    """
    if preprocess:
        img = img.convert("L")
        img = img.filter(ImageFilter.SHARPEN)
    
    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
    
    results = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])
        if text and conf > 30:  # 过滤低置信度
            results.append({
                "text": text,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
                "conf": conf
            })
    
    return results


def screenshot_and_ocr(region=None, lang="eng", save=True):
    """截屏 + OCR 一步到位
    
    Args:
        region: 截屏区域 (left, top, width, height) 或 None
        lang: OCR 语言
        save: 是否保存截图
    
    Returns:
        dict: {text, boxes, screenshot_path, timestamp, size}
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 截屏
    img = capture_screen(region=region)
    
    # 保存
    screenshot_path = None
    if save:
        screenshot_path = str(SCREENSHOT_DIR / f"screen_{ts}.png")
        img.save(screenshot_path)
    
    # OCR
    text = ocr_image(img, lang=lang)
    boxes = ocr_with_boxes(img, lang=lang)
    
    return {
        "text": text,
        "boxes": boxes,
        "screenshot_path": screenshot_path,
        "timestamp": ts,
        "size": {"width": img.width, "height": img.height}
    }


def find_text_on_screen(target, lang="eng", threshold=60):
    """在屏幕上查找指定文字的位置
    
    Args:
        target: 要查找的文字
        lang: OCR 语言
        threshold: 最低置信度
    
    Returns:
        list[dict]: 匹配的位置列表 [{text, center_x, center_y, conf}, ...]
    """
    img = capture_screen()
    boxes = ocr_with_boxes(img, lang=lang)
    
    matches = []
    target_lower = target.lower()
    for box in boxes:
        if target_lower in box["text"].lower() and box["conf"] >= threshold:
            cx = box["left"] + box["width"] // 2
            cy = box["top"] + box["height"] // 2
            matches.append({
                "text": box["text"],
                "center_x": cx,
                "center_y": cy,
                "conf": box["conf"]
            })
    
    return matches


def analyze_screen(lang="eng"):
    """分析当前屏幕内容，输出结构化摘要
    
    Returns:
        dict: {summary, line_count, top_texts, timestamp}
    """
    result = screenshot_and_ocr(lang=lang, save=False)
    
    lines = [l for l in result["text"].split("\n") if l.strip()]
    
    # 按置信度排序取 top 文字块
    top_boxes = sorted(result["boxes"], key=lambda b: b["conf"], reverse=True)[:10]
    
    return {
        "summary": "\n".join(lines[:20]),  # 前 20 行
        "line_count": len(lines),
        "top_texts": [b["text"] for b in top_boxes],
        "timestamp": result["timestamp"],
        "screen_size": result["size"]
    }


# === CLI ===

def main():
    import argparse
    parser = argparse.ArgumentParser(description="太极OS 视觉链 v0.1")
    sub = parser.add_subparsers(dest="cmd")
    
    # screenshot
    p_shot = sub.add_parser("screenshot", help="截屏并 OCR")
    p_shot.add_argument("--region", type=str, help="区域: left,top,width,height")
    p_shot.add_argument("--lang", default="eng", help="OCR 语言 (eng/chi_sim/eng+chi_sim)")
    p_shot.add_argument("--no-save", action="store_true", help="不保存截图")
    
    # find
    p_find = sub.add_parser("find", help="在屏幕上查找文字")
    p_find.add_argument("text", help="要查找的文字")
    p_find.add_argument("--lang", default="eng", help="OCR 语言")
    
    # analyze
    p_analyze = sub.add_parser("analyze", help="分析屏幕内容")
    p_analyze.add_argument("--lang", default="eng", help="OCR 语言")
    
    # check
    sub.add_parser("check", help="检查依赖是否就绪")
    
    args = parser.parse_args()
    
    if args.cmd == "check":
        print("=== 视觉链依赖检查 ===")
        # Tesseract
        try:
            ver = pytesseract.get_tesseract_version()
            print(f"[OK] Tesseract: v{ver}")
        except Exception as e:
            print(f"[FAIL] Tesseract: {e}")
        # Languages
        try:
            langs = pytesseract.get_languages()
            print(f"[OK] Languages: {', '.join(langs)}")
            if "chi_sim" not in langs:
                print("[WARN] chi_sim 未安装，中文 OCR 不可用")
                print("  下载: https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata")
                print(f"  放到: C:\\Program Files\\Tesseract-OCR\\tessdata\\")
        except Exception as e:
            print(f"[FAIL] Languages: {e}")
        # mss
        try:
            import mss as _mss
            print(f"[OK] mss: {_mss.__version__}")
        except Exception as e:
            print(f"[FAIL] mss: {e}")
        # Pillow
        try:
            from PIL import __version__ as pil_ver
            print(f"[OK] Pillow: {pil_ver}")
        except Exception as e:
            print(f"[FAIL] Pillow: {e}")
        print("=== 检查完成 ===")
    
    elif args.cmd == "screenshot":
        region = None
        if args.region:
            region = tuple(int(x) for x in args.region.split(","))
        result = screenshot_and_ocr(region=region, lang=args.lang, save=not args.no_save)
        print(json.dumps({
            "screenshot_path": result["screenshot_path"],
            "timestamp": result["timestamp"],
            "size": result["size"],
            "text_preview": result["text"][:500],
            "box_count": len(result["boxes"])
        }, ensure_ascii=False, indent=2))
    
    elif args.cmd == "find":
        matches = find_text_on_screen(args.text, lang=args.lang)
        if matches:
            print(f"找到 {len(matches)} 个匹配:")
            for m in matches:
                print(f"  [{m['conf']}%] \"{m['text']}\" @ ({m['center_x']}, {m['center_y']})")
        else:
            print(f"未找到 \"{args.text}\"")
    
    elif args.cmd == "analyze":
        result = analyze_screen(lang=args.lang)
        print(f"屏幕分析 ({result['screen_size']['width']}x{result['screen_size']['height']})")
        print(f"识别 {result['line_count']} 行文字")
        print(f"--- Top 文字块 ---")
        for t in result["top_texts"]:
            print(f"  {t}")
        print(f"--- 内容摘要 ---")
        print(result["summary"][:800])
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
