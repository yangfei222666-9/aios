# 路径真源规则（硬约束）

## 规则

**所有数据文件路径必须从 `paths.py` 获取，不允许硬编码。**

```python
# ✅ 正确
from paths import TASK_QUEUE, TASK_EXECUTIONS, SPAWN_REQUESTS

# ❌ 错误
queue_file = Path(__file__).parent / "task_queue.jsonl"
queue_file = workspace / "aios" / "agent_system" / "task_queue.jsonl"
```

## 真源文件

`aios/agent_system/paths.py` 是唯一的路径定义点。

所有数据文件统一存放在 `data/` 子目录：
- `data/task_queue.jsonl`
- `data/task_executions.jsonl`
- `data/task_traces.jsonl`
- `data/spawn_requests.jsonl`
- `data/spawn_pending.jsonl`
- `data/agents.json`
- ...

## 新模块接入

新模块必须：
1. `from paths import XXX` 获取路径
2. 如果 paths.py 没有定义，先在 paths.py 注册
3. fallback 用 `data/` 子目录，不用根目录

## 历史问题

2026-03-07 发现路径碎片化：auto_dispatcher 写根目录，heartbeat 读 data/。
导致任务创建成功但不被消费。已修复 10+ 个文件统一到 paths.py。

## 已修复文件

- auto_dispatcher.py
- task_executor.py
- task_router.py
- baseline_snapshot.py
- daily_report_data.py
- daily_metrics.py
- task_queue.py
- task_queue_manager.py
- check_agent_status.py
- check_all_agents_work.py
- show_agent_status.py
- meta_agent.py

---

**版本：** v1.0
**生效日期：** 2026-03-07
