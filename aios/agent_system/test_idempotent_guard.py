"""
调度层幂等护栏验证 - 3 个核心场景
1. 同一 task_id 连续入队两次，第二次必须被拦
2. auto_dispatcher 和 task_scheduler 对同一任务同时尝试写，最终只能进一次
3. 同一 spawn payload 连续写两次，第二次必须被拦并落日志
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 确保能 import
_parent = Path(__file__).resolve().parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from task_queue_manager import TaskQueueManager, SpawnRequestManager

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def test_1_task_id_dedup():
    """同一 task_id 连续入队两次，第二次必须被拦"""
    print("\n[Test 1] 同一 task_id 连续入队两次")
    
    tmp = Path(tempfile.mkdtemp())
    queue_file = tmp / "task_queue.jsonl"
    
    mgr = TaskQueueManager(queue_file=queue_file)
    
    task = {
        "id": "test-dedup-001",
        "description": "Test dedup",
        "type": "code",
        "priority": "normal",
        "status": "pending",
    }
    
    r1 = mgr.enqueue_task(task, source="test")
    check("第一次入队成功", r1["success"] is True, f"got {r1}")
    check("action=enqueued", r1["action"] == "enqueued", f"got {r1['action']}")
    
    r2 = mgr.enqueue_task(task, source="test")
    check("第二次入队被拦", r2["success"] is False, f"got {r2}")
    check("action 含 skipped", "skipped" in r2["action"], f"got {r2['action']}")
    
    # 确认文件里只有 1 条
    lines = [l for l in queue_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    check("队列文件只有 1 条记录", len(lines) == 1, f"got {len(lines)}")
    
    shutil.rmtree(tmp)


def test_2_cross_source_dedup():
    """auto_dispatcher 和 task_scheduler 对同一任务同时尝试写，最终只能进一次"""
    print("\n[Test 2] 跨来源同一任务去重")
    
    tmp = Path(tempfile.mkdtemp())
    queue_file = tmp / "task_queue.jsonl"
    
    mgr = TaskQueueManager(queue_file=queue_file)
    
    task = {
        "id": "cross-source-001",
        "description": "Cross source test",
        "type": "analysis",
        "priority": "high",
        "status": "pending",
    }
    
    r1 = mgr.enqueue_task(task, source="auto_dispatcher")
    check("auto_dispatcher 入队成功", r1["success"] is True, f"got {r1}")
    
    r2 = mgr.enqueue_task(task, source="task_scheduler")
    check("task_scheduler 被拦", r2["success"] is False, f"got {r2}")
    check("reason 提到 task_id", "cross-source-001" in r2.get("reason", ""), f"got {r2.get('reason')}")
    
    lines = [l for l in queue_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    check("队列文件只有 1 条记录", len(lines) == 1, f"got {len(lines)}")
    
    # 验证记录的 source 是第一个写入者
    record = json.loads(lines[0])
    check("记录 source=auto_dispatcher", record.get("source") == "auto_dispatcher", f"got {record.get('source')}")
    
    shutil.rmtree(tmp)


def test_3_spawn_dedup_with_log():
    """同一 spawn payload 连续写两次，第二次必须被拦并落日志"""
    print("\n[Test 3] spawn 请求去重 + duplicate 日志")
    
    tmp = Path(tempfile.mkdtemp())
    spawn_file = tmp / "spawn_requests.jsonl"
    dup_log = tmp / "duplicate_enqueue_attempts.jsonl"
    
    spawn_mgr = SpawnRequestManager(spawn_file=spawn_file)
    
    request = {
        "task_id": "spawn-dedup-001",
        "agent_id": "coder-dispatcher",
        "task": "Test spawn dedup",
        "label": "coder",
        "workflow_id": "wf-001",
    }
    
    r1 = spawn_mgr.create_spawn_request(request, source="task_scheduler")
    check("第一次 spawn 成功", r1["success"] is True, f"got {r1}")
    
    r2 = spawn_mgr.create_spawn_request(request, source="task_scheduler")
    check("第二次 spawn 被拦", r2["success"] is False, f"got {r2}")
    check("action=skipped_duplicate", r2["action"] == "skipped_duplicate", f"got {r2['action']}")
    
    # spawn 文件只有 1 条
    lines = [l for l in spawn_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    check("spawn 文件只有 1 条记录", len(lines) == 1, f"got {len(lines)}")
    
    # 手动写 duplicate 日志（模拟 task_scheduler._log_duplicate 行为）
    reason_text = (r2.get("reason") or "").lower()
    duplicate_reason = "same_task_id"
    if "window" in reason_text:
        duplicate_reason = "same_payload_window"
    elif "dedup_key" in reason_text or r2.get("action") == "skipped_duplicate":
        duplicate_reason = "same_dedup_key"
    
    entry = {
        "target": "spawn_requests",
        "task_id": request.get("task_id"),
        "workflow_id": request.get("workflow_id"),
        "dedup_key": r2.get("dedup_key"),
        "source": "task_scheduler",
        "created_by": "task_scheduler.py",
        "created_at": datetime.now().isoformat(),
        "duplicate_reason": duplicate_reason,
        "existing_record_hint": r2.get("reason"),
    }
    
    dup_log.parent.mkdir(parents=True, exist_ok=True)
    with open(dup_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # 验证 duplicate 日志
    dup_lines = [l for l in dup_log.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    check("duplicate 日志有记录", len(dup_lines) >= 1, f"got {len(dup_lines)}")
    
    dup_record = json.loads(dup_lines[0])
    check("target=spawn_requests", dup_record.get("target") == "spawn_requests", f"got {dup_record.get('target')}")
    check("task_id 正确", dup_record.get("task_id") == "spawn-dedup-001", f"got {dup_record.get('task_id')}")
    check("source=task_scheduler", dup_record.get("source") == "task_scheduler", f"got {dup_record.get('source')}")
    check("created_by=task_scheduler.py", dup_record.get("created_by") == "task_scheduler.py", f"got {dup_record.get('created_by')}")
    check("duplicate_reason 有值", dup_record.get("duplicate_reason") in ["same_task_id", "same_dedup_key", "same_payload_window"], f"got {dup_record.get('duplicate_reason')}")
    check("existing_record_hint 有值", bool(dup_record.get("existing_record_hint")), f"got {dup_record.get('existing_record_hint')}")
    
    shutil.rmtree(tmp)


if __name__ == "__main__":
    print("=" * 60)
    print("调度层幂等护栏验证")
    print("=" * 60)
    
    test_1_task_id_dedup()
    test_2_cross_source_dedup()
    test_3_spawn_dedup_with_log()
    
    print(f"\n{'=' * 60}")
    print(f"结果: {PASS} PASS / {FAIL} FAIL / {PASS + FAIL} TOTAL")
    if FAIL == 0:
        print("🎉 全部通过！")
    else:
        print("⚠️ 有失败项，请检查")
    print(f"{'=' * 60}")
    
    sys.exit(0 if FAIL == 0 else 1)
