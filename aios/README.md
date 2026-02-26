# AIOS - AI Operating System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.1-orange.svg)](https://github.com/yangfei222666-9/aios)
[![Tests](https://img.shields.io/badge/Tests-27%2F27-brightgreen.svg)]()

**自监控 · 自修复 · 自进化 — 零依赖 AI 操作系统框架**

AIOS 是一个轻量级 AI 操作系统，提供完整的 Kernel（上下文/内存/存储管理）、SDK（Planning/Action/Memory/Storage）、事件驱动架构和安全自我进化闭环。

---

## 10 秒快速开始

```bash
git clone https://github.com/yangfei222666-9/aios.git
cd aios
python aios.py demo      # 运行演示
python aios.py status    # 查看系统状态
python aios.py version   # 查看版本
```

零依赖，只需 Python 3.8+。

---

## 架构总览

```
┌─────────────────────────────────────────────────────┐
│                    AIOS Kernel                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │   Context     │ │   Memory     │ │   Storage    │ │
│  │   Manager     │ │   Manager    │ │   Manager    │ │
│  │  (上下文切换) │ │ (内存配额)   │ │  (SQLite)    │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ │
├─────────────────────────────────────────────────────┤
│                     SDK Layer                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Planning │ │  Action  │ │  Memory  │ │Storage │ │
│  │  (CoT)   │ │ (执行器) │ │ (向量)   │ │ (持久) │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
├─────────────────────────────────────────────────────┤
│                  Runtime Layer                        │
│  EventBus → Scheduler → Reactor → Self-Improving     │
│  Tracer   → Metrics   → Logger → Dashboard          │
├─────────────────────────────────────────────────────┤
│                  Safety Layer                         │
│  DataCollector → Evaluator → Quality Gates           │
│  (数据采集)     (量化评估)   (三层门禁)              │
└─────────────────────────────────────────────────────┘
```

---

## 核心模块

### Kernel（内核层）

#### Context Manager — 上下文管理
管理 Agent 执行上下文：创建/销毁、保存/恢复（抢占支持）、上下文切换、磁盘快照、资源限制。

```python
from kernel.context_manager import ContextManager

cm = ContextManager()
ctx = cm.create("coder-001", metadata={"role": "coder"})
ctx.add_message("user", "Fix the bug in scheduler.py")
ctx.record_llm_call(tokens=1500)

# 抢占：保存当前 → 切换到另一个 Agent
cm.switch("coder-001", "analyst-002", save_state={"line": 42})

# 磁盘快照（崩溃恢复）
cm.snapshot("coder-001")
```

#### Memory Manager — 内存管理
Per-agent 内存配额、全局限制、LRU 驱逐策略。

```python
from kernel.memory_manager import MemoryManager

mm = MemoryManager(global_limit_mb=512)
mm.register("coder-001", quota_mb=64)
mm.allocate("coder-001", size_bytes=1024*1024)

# 内存压力时自动驱逐
evicted = mm.evict_lru(target_free_bytes=100*1024*1024)
```

#### Storage Manager — 存储管理
基于 aiosqlite 的持久化层，支持 Agent 状态、上下文、事件、任务历史。

```python
from storage.storage_manager import StorageManager
import asyncio

async def main():
    sm = StorageManager("aios.db")
    await sm.initialize()
    await sm.save_agent_state("coder-001", "coder", "active")
    await sm.log_event("task.completed", {"agent": "coder-001"})
    await sm.close()

asyncio.run(main())
```

### SDK（开发套件）

| 模块 | 功能 | 关键特性 |
|------|------|----------|
| Planning | 任务规划 | CoT 拆解、依赖分析、执行策略 |
| Action | 执行引擎 | 工具注册、风险分级、护栏机制 |
| Memory | 记忆系统 | 三层记忆（working/episodic/long_term）、向量检索 |
| Storage | 持久化 | 统一存储接口 |

### Runtime（运行时）

| 组件 | 功能 |
|------|------|
| EventBus | 事件驱动通信，发布/订阅模式 |
| Scheduler | 任务调度，优先级队列 + Planning 集成 |
| Reactor | 自动故障检测和修复（Playbook 驱动） |
| Self-Improving Loop | 安全自我进化闭环 |

### Safety（安全层）

| 组件 | 功能 |
|------|------|
| DataCollector | 统一数据采集（5 种 Schema） |
| Evaluator | 量化评估（0-100 分，S/A/B/C/D/F 等级） |
| Quality Gates | 三层门禁（L0 自动/L1 回归/L2 人工） |

---

## 性能基准

在 Ryzen 7 9800X3D / Python 3.12 / Windows 11 上的测试结果：

### Kernel

| 操作 | 吞吐量 | 平均延迟 | 状态 |
|------|--------|----------|------|
| Context 创建（100 agents） | 11.2K ops/s | 89μs | ✅ |
| Context 切换 | 763K ops/s | 1.3μs | ✅ PASS |
| Context 切换 p99 | — | 2.4μs | ✅ |
| 消息添加 | 3.18M ops/s | 0.3μs | ✅ PASS |
| 磁盘快照（50 msgs） | 3.9K ops/s | 257μs | ✅ |
| 快照加载 | 14.3K ops/s | 70μs | ✅ |
| 资源限制检查 | 3.43M ops/s | 0.3μs | ✅ PASS |
| Save/Restore 循环 | 918K ops/s | 1.1μs | ✅ |
| 内存分配（单次） | 3.68M ops/s | 0.3μs | ✅ PASS |
| 内存释放 | 4.72M ops/s | 0.2μs | ✅ PASS |
| LRU 驱逐（80 agents） | 15.2K ops/s | 66μs | ✅ |

### Storage（SQLite in-memory）

| 操作 | 吞吐量 | 平均延迟 |
|------|--------|----------|
| Agent 状态写入 | 10.5K ops/s | 95μs |
| Agent 状态读取 | 8.4K ops/s | 119μs |
| 事件写入 | 11.1K ops/s | 90μs |
| 事件查询 | 3.3K ops/s | 300μs |
| 任务写入 | 13.2K ops/s | 76μs |
| 任务读取 | 9.8K ops/s | 103μs |

运行 benchmark：
```bash
python benchmark.py          # 完整报告
python benchmark.py --json   # JSON 输出
python benchmark.py --module kernel  # 仅 kernel
```

---

## 自我进化闭环

```
DataCollector → Evaluator → Quality Gates → Self-Improving Loop → Heartbeat
  (眼睛)        (大脑)       (刹车)          (进化)              (监控)
```

1. **DataCollector** 采集所有运行数据（5 种标准 Schema）
2. **Evaluator** 量化评估（任务成功率、Agent 评分、系统健康度）
3. **Quality Gates** 三层门禁确保改进安全（L0 自动 → L1 回归 → L2 人工）
4. **Self-Improving Loop** 自动应用安全改进
5. **Heartbeat** 定期监控，健康度 < 60 自动告警

---

## Agent 系统

AIOS 内置 64 个 Agent（27 Learning + 37 Skill），通过 Task Router 智能路由：

```python
# 提交任务
python -c "from agent_system.task_router import TaskRouter; tr = TaskRouter(); print(tr.route('分析系统性能'))"

# 心跳自动分发
python agent_system/heartbeat_v5.py
```

Task Router 支持 80+ 中英文关键词，三层匹配策略（精确 → 关键词 → 模糊 Jaccard）。

---

## Dashboard

```bash
cd dashboard/AIOS-Dashboard-v3.4
python server.py
# 访问 http://127.0.0.1:8888
```

---

## 项目结构

```
aios/
├── kernel/              # 内核层
│   ├── context_manager.py   # 上下文管理
│   └── memory_manager.py    # 内存管理
├── sdk/                 # SDK 层
│   ├── planning.py          # 规划模块（CoT）
│   ├── action.py            # 执行引擎
│   ├── memory.py            # 记忆系统
│   └── storage.py           # 存储接口
├── storage/             # 持久化层
│   ├── storage_manager.py   # SQLite 存储管理
│   └── sql/schema.sql       # 数据库 Schema
├── core/                # 核心运行时
│   ├── event_bus.py         # 事件总线
│   └── engine.py            # 引擎
├── agent_system/        # Agent 系统
│   ├── task_router.py       # 智能路由
│   ├── heartbeat_v5.py      # 心跳分发
│   └── agents.json          # Agent 注册表
├── data_collector/      # 数据采集
├── observability/       # 可观测性（Tracer/Metrics/Logger）
├── dashboard/           # Web Dashboard
├── benchmark.py         # 性能基准测试
├── aios.py              # CLI 入口
└── README.md
```

---

## 配置

```yaml
# config.yaml
system:
  name: "AIOS"
  version: "1.1"
  log_level: "INFO"

scheduler:
  max_concurrent: 5
  default_timeout: 60

memory:
  global_limit_mb: 512
  default_quota_mb: 64

storage:
  backend: "sqlite"
  db_path: "aios.db"
```

---

## API 参考

### Kernel API

```python
# Context Manager
cm = ContextManager(snapshot_dir=Path("./snapshots"))
ctx = cm.create(agent_id, metadata={}, limits={})
cm.save(agent_id, extra_state={})
state = cm.restore(agent_id)
cm.switch(from_agent, to_agent, save_state={})
cm.snapshot(agent_id)
cm.load_snapshot(agent_id)
cm.check_limits(agent_id) -> dict
cm.enforce_limits(agent_id) -> str | None
cm.stats() -> dict

# Memory Manager
mm = MemoryManager(global_limit_mb=512)
mm.register(agent_id, quota_mb=64)
mm.allocate(agent_id, size_bytes) -> (bool, str)
mm.release(agent_id, size_bytes) -> bool
mm.release_all(agent_id) -> int
mm.evict_lru(target_free_bytes) -> list[str]
mm.usage(agent_id) -> dict
mm.top(n=5) -> list[dict]
mm.stats() -> dict
```

### Storage API

```python
# StorageManager (async)
sm = StorageManager("aios.db")
await sm.initialize()
await sm.save_agent_state(agent_id, role, state, goal=None, stats=None)
await sm.get_agent_state(agent_id) -> dict | None
await sm.log_event(event_type, data, agent_id=None)
await sm.list_events(event_type=None, agent_id=None, limit=100)
await sm.log_task(task_id, agent_id, task_type, priority="normal")
await sm.update_task_status(task_id, status, result=None)
await sm.get_task(task_id) -> dict | None
await sm.close()
```

### SDK API

```python
# Planning
planner = PlanningModule(agent_id="coder-001")
plan = planner.plan("Refactor scheduler")
deps = planner.analyze_dependencies(tasks)

# Action
engine = ActionEngine(agent_id="coder-001")
engine.register_tool("read_file", fn, risk="low")
result = engine.execute("read_file", "/path/to/file")

# Memory
mem = MemoryModule(agent_id="coder-001")
mem.store("key", data, layer="working")
result = mem.retrieve("key")
results = mem.search("query", top_k=10)
```

---

## 开发

```bash
# 运行测试
python -m pytest tests/ -v

# 运行 benchmark
python benchmark.py

# 检查系统健康度
python agent_system/heartbeat_v4.py
```

---

## Roadmap

- [x] Week 1-3: 队列系统 + 调度算法
- [x] Week 4-6: Context/Memory/Storage Manager
- [x] Week 7-8: Benchmark + 文档
- [ ] Month 4-6: VM Controller + CloudRouter 集成
- [ ] Month 6+: 学术论文

---

## License

MIT License - see [LICENSE](LICENSE)

---

*Built by 珊瑚海 + 小九 🐾*
