#!/usr/bin/env python3
"""Quick integration test for Memory Retrieval in TaskExecutor."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # aios/
sys.path.insert(0, str(Path(__file__).parent))          # agent_system/

from core.task_executor import TaskExecutor

executor = TaskExecutor()

test_tasks = [
    {"id": "test-mem-001", "type": "code",     "description": "重构 scheduler.py 提升性能"},
    {"id": "test-mem-002", "type": "analysis", "description": "分析最近7天的错误日志趋势"},
    {"id": "test-mem-003", "type": "monitor",  "description": "检查 CPU 和内存使用率"},
    {"id": "test-mem-004", "type": "code",     "description": "优化 Memory Manager 缓存策略"},
    {"id": "test-mem-005", "type": "analysis", "description": "生成系统健康度报告"},
]

print("=== Memory Retrieval Integration Test ===\n")
ok_count = 0
for task in test_tasks:
    ctx = executor._build_memory_context(task["id"], task["description"], task["type"])
    status = "DEGRADED" if ctx["degraded"] else "OK"
    print(f"[{status}] {task['id']} | retrieved={ctx['retrieved_count']} used={ctx['used_count']} latency={ctx['latency_ms']}ms")
    if ctx["memory_hints"]:
        for h in ctx["memory_hints"]:
            print(f"  hint: {h[:100]}")
        ok_count += 1
    else:
        print("  (no hints - no semantic match in LanceDB)")

print(f"\n=== Results: {ok_count}/{len(test_tasks)} tasks got memory hints ===")

# Test feedback write
print("\n--- Testing feedback write ---")
fake_ctx = {"memory_ids": [], "memory_hints": []}
executor._write_memory_feedback("test-mem-001", fake_ctx, {"success": True})
print("feedback with empty ids: OK (no-op)")

# Check log file
log = Path(__file__).parent / "memory_retrieval_log.jsonl"
if log.exists():
    lines = log.read_text(encoding="utf-8").strip().split("\n")
    print(f"memory_retrieval_log.jsonl: {len(lines)} entries")
else:
    print("memory_retrieval_log.jsonl: not yet created (needs real memory_ids)")

print("\n=== Integration test complete ===")
