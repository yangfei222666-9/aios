"""
fix_lessons_error_type.py
自动分类 lessons.json.migrated 中 error_type=unknown 的条目
"""
import json
import re
from pathlib import Path

def classify_error(error_message: str, task_type: str) -> str:
    """根据 error_message 自动分类错误类型"""
    msg = error_message.lower()
    
    # API/网络错误
    if any(x in msg for x in ['502', '503', '504', 'bad gateway', 'cloudflare', 'api error']):
        return 'api_error'
    if any(x in msg for x in ['timeout', 'timed out', 'connection']):
        return 'timeout'
    if any(x in msg for x in ['401', '403', 'unauthorized', 'forbidden']):
        return 'auth_error'
    if any(x in msg for x in ['404', 'not found']):
        return 'not_found'
    
    # 依赖/环境错误
    if any(x in msg for x in ['import', 'module', 'package', 'install', 'dependency']):
        return 'dependency_error'
    if any(x in msg for x in ['permission', 'access denied', 'eacces']):
        return 'permission_error'
    
    # 模拟失败（测试数据）
    if 'simulated failure' in msg:
        return 'simulated_failure'
    
    # 逻辑/代码错误
    if any(x in msg for x in ['typeerror', 'valueerror', 'attributeerror', 'keyerror', 'indexerror']):
        return 'logic_error'
    if any(x in msg for x in ['syntax', 'parse error']):
        return 'syntax_error'
    
    # 资源不足
    if any(x in msg for x in ['memory', 'disk', 'resource', 'quota']):
        return 'resource_exhausted'
    
    return 'unknown'

# 读取 lessons.json.migrated
lessons_file = Path("lessons.json.migrated")
with open(lessons_file, 'r', encoding='utf-8') as f:
    lessons = json.load(f)

# 分类并修复
fixed = 0
for lesson in lessons:
    if lesson.get('error_type') == 'unknown':
        new_type = classify_error(
            lesson.get('error_message', ''),
            lesson.get('task_type', '')
        )
        if new_type != 'unknown':
            print(f"  {lesson['lesson_id'][:12]}: unknown -> {new_type}")
            lesson['error_type'] = new_type
            fixed += 1
        else:
            print(f"  {lesson['lesson_id'][:12]}: still unknown (msg: {lesson.get('error_message','')[:60]})")

# 写回文件
with open(lessons_file, 'w', encoding='utf-8') as f:
    json.dump(lessons, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Fixed {fixed}/{len(lessons)} lessons")

# 同时更新 lessons.json（如果存在）
lessons_json = Path("lessons.json")
if not lessons_json.exists():
    # 只保留非 simulated_failure 的真实失败
    real_lessons = [l for l in lessons if l.get('error_type') != 'simulated_failure']
    with open(lessons_json, 'w', encoding='utf-8') as f:
        json.dump(real_lessons, f, indent=2, ensure_ascii=False)
    print(f"[OK] Created lessons.json with {len(real_lessons)} real failures")
else:
    with open(lessons_json, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    print(f"[INFO] lessons.json already exists with {len(existing)} entries")
