#!/usr/bin/env python3
"""
migrate_task_executions.py - 迁移旧格式 task_executions.jsonl 到标准格式

旧格式：
{
  "timestamp": 1234567890.123,
  "task_id": "task-xxx",
  "task_type": "code",
  "description": "...",
  "result": {
    "success": true,
    "agent": "coder",
    "duration": 1.234,
    "output": "..."
  }
}

新格式（标准化）：
{
  "task_id": "task-xxx",
  "agent_id": "coder",
  "status": "completed",
  "start_time": "2026-03-07T07:00:00Z",
  "end_time": "2026-03-07T07:00:01Z",
  "duration_ms": 1234,
  "retry_count": 0,
  "side_effects": {"files_written": [], "tasks_created": [], "api_calls": 0},
  "result": {"output": "...", "task_type": "code"}  # status=completed 时
}

用法：
  python migrate_task_executions.py                # 迁移并备份
  python migrate_task_executions.py --dry-run      # 预览不写入
  python migrate_task_executions.py --no-backup    # 不备份旧文件
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
OLD_FILE = BASE_DIR / "task_executions.jsonl"
BACKUP_FILE = BASE_DIR / "task_executions.jsonl.backup"


def migrate_record(old: dict) -> dict:
    """转换单条记录"""
    result = old.get("result", {})
    success = result.get("success", False)
    agent_id = result.get("agent", "unknown")
    duration_s = result.get("duration", 0)
    output = result.get("output", "")
    
    # 时间戳转 ISO 8601
    ts = old.get("timestamp", 0)
    if ts:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        iso_time = dt.isoformat()
    else:
        iso_time = datetime.now(timezone.utc).isoformat()
    
    new = {
        "task_id": old.get("task_id", "unknown"),
        "agent_id": agent_id,
        "status": "completed" if success else "failed",
        "start_time": iso_time,
        "end_time": iso_time,
        "duration_ms": round(duration_s * 1000),
        "retry_count": 0,  # 旧格式没有，默认 0
        "side_effects": {"files_written": [], "tasks_created": [], "api_calls": 0},
    }
    
    # 条件字段
    if success:
        new["result"] = {
            "output": output,
            "task_type": old.get("task_type", ""),
        }
    else:
        new["error"] = output or "task failed"
    
    return new


def main():
    dry_run = "--dry-run" in sys.argv
    no_backup = "--no-backup" in sys.argv
    
    if not OLD_FILE.exists():
        print(f"[SKIP] {OLD_FILE} 不存在")
        return
    
    # 读取旧记录
    with open(OLD_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    
    if not lines:
        print(f"[SKIP] {OLD_FILE} 为空")
        return
    
    print(f"[INFO] 读取 {len(lines)} 条记录")
    
    # 转换
    migrated = []
    errors = 0
    for i, line in enumerate(lines, 1):
        try:
            old = json.loads(line)
            new = migrate_record(old)
            migrated.append(new)
        except Exception as e:
            print(f"[ERROR] 第 {i} 行解析失败: {e}")
            errors += 1
    
    print(f"[INFO] 成功转换 {len(migrated)} 条，失败 {errors} 条")
    
    if dry_run:
        print("\n[DRY-RUN] 预览前 3 条：")
        for rec in migrated[:3]:
            print(json.dumps(rec, ensure_ascii=False, indent=2))
        print("\n[DRY-RUN] 不写入文件")
        return
    
    # 备份
    if not no_backup and OLD_FILE.exists():
        OLD_FILE.rename(BACKUP_FILE)
        print(f"[BACKUP] 旧文件备份到 {BACKUP_FILE}")
    
    # 写入新格式
    with open(OLD_FILE, "w", encoding="utf-8") as f:
        for rec in migrated:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    
    print(f"[OK] 迁移完成，写入 {len(migrated)} 条记录到 {OLD_FILE}")
    print(f"[INFO] 字段标准化：task_id, agent_id, status, start_time, end_time, duration_ms, retry_count, side_effects")
    print(f"[INFO] 条件字段：error（failed时）, result（completed时）")


if __name__ == "__main__":
    main()
