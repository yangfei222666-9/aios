"""
清理假数据 - 一次性脚本

功能：
1. 识别 lessons.json 中的假数据（simulated / 测试描述）
2. 归档到 lessons.test.archive.json
3. 只保留真实失败记录
"""

import json
import shutil
import os
from datetime import datetime

LESSONS_PATH = "lessons.json"
ARCHIVE_PATH = "lessons.test.archive.json"

# 假数据特征（精确匹配，避免误杀真实任务）
FAKE_MARKERS = [
    "Generate complex report",
    "Install pandas",
    "Calculate average",
    "Process large file",
    "Simulated failure",
    "Demo task"
]


def cleanup():
    if not os.path.exists(LESSONS_PATH):
        print(f"[WARN] {LESSONS_PATH} not found, nothing to clean")
        return
    
    with open(LESSONS_PATH, "r", encoding="utf-8") as f:
        lessons = json.load(f)
    
    real, fake = [], []
    
    for lesson in lessons:
        desc = lesson.get("task_description", "") or lesson.get("description", "")
        error = lesson.get("error_message", "")
        
        is_fake = (
            lesson.get("source") == "simulated" or
            any(m.lower() in desc.lower() for m in FAKE_MARKERS) or
            any(m.lower() in error.lower() for m in FAKE_MARKERS)
            # 注意：不用 lesson_id 前缀判断，sha256 hash 可能合法以 00 开头
        )
        
        (fake if is_fake else real).append(lesson)
    
    # 归档假数据
    if fake:
        shutil.copy2(LESSONS_PATH, ARCHIVE_PATH)
        print(f"[OK] Archived {len(fake)} fake lessons → {ARCHIVE_PATH}")
    
    # 只保留真实数据
    with open(LESSONS_PATH, "w", encoding="utf-8") as f:
        json.dump(real, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Production {LESSONS_PATH}: {len(real)} real records")
    print(f"[INFO] Removed: {len(fake)} fake records")
    
    # 统计
    print("\n" + "=" * 60)
    print("Cleanup Summary:")
    print(f"  Real failures: {len(real)}")
    print(f"  Fake data (archived): {len(fake)}")
    print("=" * 60)


if __name__ == "__main__":
    print("Cleanup Fake Lessons - One-time Script")
    print("=" * 60)
    cleanup()
