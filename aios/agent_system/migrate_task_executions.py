#!/usr/bin/env python3
"""
migrate_task_executions.py - 杩佺Щ鏃ф牸寮?task_executions_v2.jsonl 鍒版爣鍑嗘牸寮?
鏃ф牸寮忥細
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

鏂版牸寮忥紙鏍囧噯鍖栵級锛?{
  "task_id": "task-xxx",
  "agent_id": "coder",
  "status": "completed",
  "start_time": "2026-03-07T07:00:00Z",
  "end_time": "2026-03-07T07:00:01Z",
  "duration_ms": 1234,
  "retry_count": 0,
  "side_effects": {"files_written": [], "tasks_created": [], "api_calls": 0},
  "result": {"output": "...", "task_type": "code"}  # status=completed 鏃?}

鐢ㄦ硶锛?  python migrate_task_executions.py                # 杩佺Щ骞跺浠?  python migrate_task_executions.py --dry-run      # 棰勮涓嶅啓鍏?  python migrate_task_executions.py --no-backup    # 涓嶅浠芥棫鏂囦欢
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
OLD_FILE = BASE_DIR / "task_executions_v2.jsonl"
BACKUP_FILE = BASE_DIR / "task_executions_v2.jsonl.backup"


def migrate_record(old: dict) -> dict:
    """杞崲鍗曟潯璁板綍"""
    result = old.get("result", {})
    success = result.get("success", False)
    agent_id = result.get("agent", "unknown")
    duration_s = result.get("duration", 0)
    output = result.get("output", "")
    
    # 鏃堕棿鎴宠浆 ISO 8601
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
        "retry_count": 0,  # 鏃ф牸寮忔病鏈夛紝榛樿 0
        "side_effects": {"files_written": [], "tasks_created": [], "api_calls": 0},
    }
    
    # 鏉′欢瀛楁
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
        print(f"[SKIP] {OLD_FILE} 涓嶅瓨鍦?)
        return
    
    # 璇诲彇鏃ц褰?    with open(OLD_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    
    if not lines:
        print(f"[SKIP] {OLD_FILE} 涓虹┖")
        return
    
    print(f"[INFO] 璇诲彇 {len(lines)} 鏉¤褰?)
    
    # 杞崲
    migrated = []
    errors = 0
    for i, line in enumerate(lines, 1):
        try:
            old = json.loads(line)
            new = migrate_record(old)
            migrated.append(new)
        except Exception as e:
            print(f"[ERROR] 绗?{i} 琛岃В鏋愬け璐? {e}")
            errors += 1
    
    print(f"[INFO] 鎴愬姛杞崲 {len(migrated)} 鏉★紝澶辫触 {errors} 鏉?)
    
    if dry_run:
        print("\n[DRY-RUN] 棰勮鍓?3 鏉★細")
        for rec in migrated[:3]:
            print(json.dumps(rec, ensure_ascii=False, indent=2))
        print("\n[DRY-RUN] 涓嶅啓鍏ユ枃浠?)
        return
    
    # 澶囦唤
    if not no_backup and OLD_FILE.exists():
        OLD_FILE.rename(BACKUP_FILE)
        print(f"[BACKUP] 鏃ф枃浠跺浠藉埌 {BACKUP_FILE}")
    
    # 鍐欏叆鏂版牸寮?    with open(OLD_FILE, "w", encoding="utf-8") as f:
        for rec in migrated:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    
    print(f"[OK] 杩佺Щ瀹屾垚锛屽啓鍏?{len(migrated)} 鏉¤褰曞埌 {OLD_FILE}")
    print(f"[INFO] 瀛楁鏍囧噯鍖栵細task_id, agent_id, status, start_time, end_time, duration_ms, retry_count, side_effects")
    print(f"[INFO] 鏉′欢瀛楁锛歟rror锛坒ailed鏃讹級, result锛坈ompleted鏃讹級")


if __name__ == "__main__":
    main()

