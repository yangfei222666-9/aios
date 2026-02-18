"""
autolearn/scripts/triage.py - 错误分类处理器
读取 inbox.md 中的 pending 条目，生成结构化 lesson 写入 lessons.json
"""
import json
import re
import os
from datetime import datetime

WORKSPACE = os.path.join(os.environ["USERPROFILE"], ".openclaw", "workspace")
INBOX = os.path.join(WORKSPACE, "autolearn", "inbox.md")
LESSONS_FILE = os.path.join(WORKSPACE, "memory", "lessons.json")
LESSONS_DIR = os.path.join(WORKSPACE, "autolearn", "lessons")

# Category keywords mapping
CATEGORY_MAP = {
    "powershell": ["powershell", "get-childitem", "dir ", "cmdlet", "parameter"],
    "path": ["路径", "path", "~", "$env:", "绝对路径", "展开"],
    "encoding": ["encoding", "bytesting", "unicode", "utf-8", "gbk", "乱码"],
    "permission": ["权限", "permission", "runas", "admin", "管理员", "拒绝"],
    "data": ["数据", "编造", "data", "模板", "凑数"],
    "ui": ["ui", "界面", "删错", "元素", "颜色"],
    "tool_limitation": ["工具限制", "bug", "web_search", "不支持"],
}

def detect_category(text):
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_MAP.items():
        scores[cat] = sum(1 for kw in keywords if kw.lower() in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"

def parse_inbox(filepath):
    """Parse inbox.md into structured entries."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    entries = []
    sections = re.split(r"^## ", content, flags=re.MULTILINE)[1:]  # skip header
    
    for section in sections:
        lines = section.strip().split("\n")
        title_line = lines[0]
        
        # Parse title: "2026-02-19 | PowerShell dir 参数错误"
        match = re.match(r"(\d{4}-\d{2}-\d{2})\s*\|\s*(.+)", title_line)
        if not match:
            continue
        
        date, title = match.group(1), match.group(2).strip()
        body = "\n".join(lines[1:])
        
        # Check status
        status_match = re.search(r"\*\*状态\*\*:\s*(\w+)", body)
        status = status_match.group(1) if status_match else "unknown"
        
        if status != "pending":
            continue
        
        # Extract fields
        fields = {}
        for field in ["场景", "原因", "正确做法", "严重度"]:
            m = re.search(rf"\*\*{field}\*\*:\s*(.+)", body)
            if m:
                fields[field] = m.group(1).strip()
        
        category = detect_category(body + " " + title)
        
        entries.append({
            "date": date,
            "title": title,
            "category": category,
            "scenario": fields.get("场景", ""),
            "cause": fields.get("原因", ""),
            "correct_action": fields.get("正确做法", ""),
            "severity": fields.get("严重度", "low"),
            "status": status,
        })
    
    return entries

def generate_lesson(entry):
    """Convert inbox entry to a lesson for lessons.json."""
    return {
        "date": entry["date"],
        "category": entry["category"],
        "mistake": entry["scenario"],
        "lesson": entry["correct_action"],
        "severity": entry["severity"],
        "source": "autolearn_triage",
        "verified": False,
    }

def generate_verify_command(entry):
    """Generate a verification test for the lesson."""
    cat = entry["category"]
    if cat == "powershell":
        return "Get-ChildItem \"$env:USERPROFILE\\Downloads\" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name"
    elif cat == "path":
        return f'Test-Path "$env:USERPROFILE\\.openclaw\\workspace\\autolearn\\inbox.md"'
    elif cat == "permission":
        return 'Start-Process powershell -Verb RunAs -ArgumentList \'-Command "whoami /priv"\''
    elif cat == "encoding":
        return "# Tool limitation - manual verification needed"
    return "# No auto-verify available"

def update_lessons_file(new_lessons):
    """Append new lessons to lessons.json."""
    data = {"lessons": [], "rules_derived": []}
    if os.path.exists(LESSONS_FILE):
        with open(LESSONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    
    existing_mistakes = {l.get("mistake", "") for l in data["lessons"]}
    added = 0
    for lesson in new_lessons:
        if lesson["mistake"] not in existing_mistakes:
            data["lessons"].append(lesson)
            added += 1
    
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return added

def mark_processed(filepath):
    """Mark all pending entries as processed in inbox.md."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("**状态**: pending", "**状态**: processed")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def save_lesson_detail(entry, lesson):
    """Save detailed lesson to autolearn/lessons/ directory."""
    filename = f"{entry['date']}_{entry['category']}_{entry['title'][:20].replace(' ', '_')}.md"
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filepath = os.path.join(LESSONS_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {entry['title']}\n\n")
        f.write(f"- **日期**: {entry['date']}\n")
        f.write(f"- **类别**: {entry['category']}\n")
        f.write(f"- **严重度**: {entry['severity']}\n\n")
        f.write(f"## 场景\n{entry['scenario']}\n\n")
        f.write(f"## 原因\n{entry['cause']}\n\n")
        f.write(f"## 正确做法\n{entry['correct_action']}\n\n")
        f.write(f"## 复测命令\n```powershell\n{generate_verify_command(entry)}\n```\n")
    
    return filepath

def main():
    print("=" * 50)
    print("  Autolearn Triage")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if not os.path.exists(INBOX):
        print("\n[!] inbox.md not found")
        return
    
    entries = parse_inbox(INBOX)
    if not entries:
        print("\n[OK] No pending entries in inbox")
        return
    
    print(f"\n[*] Found {len(entries)} pending entries\n")
    
    new_lessons = []
    for entry in entries:
        print(f"  [{entry['severity'].upper()}] {entry['title']}")
        print(f"    Category: {entry['category']}")
        
        lesson = generate_lesson(entry)
        new_lessons.append(lesson)
        
        detail_path = save_lesson_detail(entry, lesson)
        print(f"    Detail: {os.path.basename(detail_path)}")
    
    added = update_lessons_file(new_lessons)
    print(f"\n[+] Added {added} new lessons to lessons.json")
    
    mark_processed(INBOX)
    print("[+] Inbox entries marked as processed")
    
    print("\n" + "=" * 50)
    print(f"  Triage complete: {len(entries)} processed, {added} new lessons")
    print("=" * 50)

if __name__ == "__main__":
    main()
