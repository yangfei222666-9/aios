from memory_v2.memory_agent import memory_agent
from memory_v2.memory_store import search_memories

samples = [
    (
        {"id": "mem-001", "type": "code", "description": "优化 Memory Manager 缓存策略"},
        {"success": True, "output": "引入 TTL + LRU 双层缓存，降低重复计算延迟"},
    ),
    (
        {"id": "mem-002", "type": "code", "description": "修复 task_executor 超时问题"},
        {"success": True, "output": "使用 asyncio.wait_for 包裹任务执行，并补充 timeout 错误分类"},
    ),
    (
        {"id": "mem-003", "type": "research", "description": "收集相关资料并生成优化建议"},
        {"success": False, "error": "API error: 502 Bad gateway"},
    ),
    (
        {"id": "mem-004", "type": "analysis", "description": "分析系统错误率并生成报告"},
        {"success": True, "output": "按 agent / task_type / time_window 拆分指标后更容易定位问题"},
    ),
]

for task, result in samples:
    memory = memory_agent.build_memory_record(task, result)
    rid = memory_agent.queue_memory_write(memory)
    print("UPSERT", rid)

print("\n=== QUERY 1 ===")
for r in search_memories("优化缓存性能", memory_type="success_case", task_type="code", top_k=3):
    print(r["id"], r.get("memory_type"), r.get("task_type"), r.get("_score"), r.get("summary"))

print("\n=== QUERY 2 ===")
for r in search_memories("502 gateway", memory_type=["failure_pattern", "fix_solution"], error_type="upstream_api_error", top_k=3):
    print(r["id"], r.get("memory_type"), r.get("error_type"), r.get("_score"), r.get("summary"))
