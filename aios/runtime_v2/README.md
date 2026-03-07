# Runtime v2 - Event-Driven Task Execution Runtime

**状态：** Shadow Mode（不影响现有系统）

**核心理念：** 所有状态变化必须通过 event log

---

## 架构设计

### 核心模块

```
┌─────────────────────────────────────────────────────────┐
│                      CLI / API                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    TaskQueue                            │
│  - enqueue(task) → task_created event                   │
│  - list_tasks() → 调用 state projection                 │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   EventLog                              │
│  - append_event(event_type, task_id, data)              │
│  - read_events() → List[Event]                          │
│  - 每个 event 有 event_id (uuid4)                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                StateProjection                          │
│  - events → group by task_id → last event → state       │
│  - list_pending_tasks()                                 │
│  - list_running_tasks()                                 │
│  - list_completed_tasks()                               │
│  - list_failed_tasks()                                  │
│  - list_stalled_tasks()                                 │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Dispatcher                            │
│  - tick() → scan pending + check capacity + spawn       │
│  - spawn_worker(task) → task_started event              │
│  - 不做 queue/state/event logic                         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     Worker                              │
│  - execute(task) → 执行任务                             │
│  - 写入 task_completed / task_failed event              │
│  - 根据 task.type 路由到对应 Agent                      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Runner                               │
│  - Shadow loop（每 5 秒 tick 一次）                     │
│  - 不影响现有系统                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Event Schema

所有 event 遵循统一格式：

```json
{
  "event_id": "uuid4",
  "timestamp": "ISO8601",
  "event_type": "task_created|task_started|task_completed|task_failed|task_timeout",
  "task_id": "t-xxx",
  "data": {...}
}
```

### Event Types

1. **task_created** - 任务创建
   ```json
   {
     "event_type": "task_created",
     "task_id": "t-xxx",
     "data": {
       "task_id": "t-xxx",
       "type": "code|analysis|monitor",
       "description": "...",
       "priority": "high|normal|low",
       "created_at": "ISO8601",
       "source": "cli|heartbeat|user"
     }
   }
   ```

2. **task_started** - 任务开始执行
   ```json
   {
     "event_type": "task_started",
     "task_id": "t-xxx",
     "data": {
       "started_at": 1234567890.123,
       "worker_id": "worker-t-xxx"
     }
   }
   ```

3. **task_completed** - 任务完成
   ```json
   {
     "event_type": "task_completed",
     "task_id": "t-xxx",
     "data": {
       "completed_at": 1234567890.123,
       "result": {...}
     }
   }
   ```

4. **task_failed** - 任务失败
   ```json
   {
     "event_type": "task_failed",
     "task_id": "t-xxx",
     "data": {
       "failed_at": 1234567890.123,
       "error": "..."
     }
   }
   ```

5. **task_timeout** - 任务超时
   ```json
   {
     "event_type": "task_timeout",
     "task_id": "t-xxx",
     "data": {
       "timeout_at": 1234567890.123
     }
   }
   ```

---

## State Machine

```
task_created → pending
task_started → running
task_completed → completed
task_failed → failed
task_timeout → timeout
```

---

## 使用方式

### 1. 提交任务（CLI）

```bash
cd C:\Users\A\.openclaw\workspace\aios\runtime_v2

# 提交任务
python cli.py submit --type code --desc "重构 scheduler.py" --priority high

# 列出任务
python cli.py list
python cli.py list --filter pending
python cli.py list --filter running
python cli.py list --filter completed
python cli.py list --filter failed

# 查看状态
python cli.py status
```

### 2. 提交任务（Python API）

```python
from aios.runtime_v2 import get_queue

queue = get_queue()
task_id = queue.enqueue(
    task_type="code",
    description="重构 scheduler.py",
    priority="high",
    source="cli"
)
print(f"Task submitted: {task_id}")
```

### 3. 启动 Runtime（Shadow Loop）

```bash
cd C:\Users\A\.openclaw\workspace\aios\runtime_v2
python runner.py
```

或者：

```python
from aios.runtime_v2 import run_runtime

run_runtime(tick_interval=5)  # 每 5 秒 tick 一次
```

### 4. 查询状态（Python API）

```python
from aios.runtime_v2 import get_state

state = get_state()

# 查询单个任务
task = state.get_task_state("t-xxx")
print(task["state"])  # pending|running|completed|failed|timeout

# 列出所有 pending 任务
pending = state.list_pending_tasks()
for task in pending:
    print(task["task_id"], task["task_data"]["description"])

# 列出所有 running 任务
running = state.list_running_tasks()

# 列出所有 completed 任务
completed = state.list_completed_tasks()

# 列出所有 failed 任务
failed = state.list_failed_tasks()

# 列出所有 stalled 任务（running 超过 5 分钟）
stalled = state.list_stalled_tasks()
```

---

## 测试

```bash
cd C:\Users\A\.openclaw\workspace\aios\runtime_v2
python test_runtime_v2.py
```

**预期输出：**

```
============================================================
Runtime v2 完整流程测试
============================================================

[STEP 1] 提交任务
  [OK] Task 1: t-xxx
  [OK] Task 2: t-xxx
  [OK] Task 3: t-xxx

[STEP 2] 检查初始状态
  Pending tasks: 3
    - t-xxx | code | 重构 scheduler.py
    - t-xxx | analysis | 分析失败日志
    - t-xxx | monitor | 检查磁盘使用率

[STEP 3] 运行 dispatcher（3 个 tick）

  Tick #1
[DISPATCHER] Spawned worker for task: t-xxx
[DISPATCHER] Spawned worker for task: t-xxx
[DISPATCHER] Spawned worker for task: t-xxx
    Pending: 3
    Running: 0
    Spawned: 3
[WORKER] Executing task: t-xxx (type: code)
[WORKER] Task completed: t-xxx
[WORKER] Executing task: t-xxx (type: analysis)
[WORKER] Task completed: t-xxx
[WORKER] Executing task: t-xxx (type: monitor)
[WORKER] Task completed: t-xxx

  Tick #2
    Pending: 0
    Running: 0
    Spawned: 0

  Tick #3
    Pending: 0
    Running: 0
    Spawned: 0

[STEP 4] 检查最终状态
  Pending: 0
  Running: 0
  Completed: 3
  Failed: 0

[STEP 5] 验证结果
  [OK] 所有任务都完成！

  完成的任务：
    - t-xxx | code | 重构 scheduler.py
    - t-xxx | analysis | 分析失败日志
    - t-xxx | monitor | 检查磁盘使用率

============================================================
测试完成
============================================================
```

---

## 设计原则

### 1. 所有状态变化必须通过 event log

❌ **错误：**
```python
task.status = "completed"  # 直接修改状态
```

✅ **正确：**
```python
event_log.append_event("task_completed", task_id, {...})  # 写入 event
```

### 2. queue 不做 dequeue

❌ **错误：**
```python
task = queue.dequeue()  # queue 不应该有 dequeue
```

✅ **正确：**
```python
pending = state.list_pending_tasks()  # 通过 state projection 查询
dispatcher.spawn_worker(pending[0])   # dispatcher 负责调度
```

### 3. 每个模块职责单一

- **event_log** - 只做 append + read
- **queue** - 只做 enqueue + list
- **state** - 只做 projection（events → state）
- **dispatcher** - 只做 scheduling
- **worker** - 只做 execution
- **runner** - 只做 loop

### 4. task schema 固定

所有 task 必须包含：
- `task_id` - 唯一标识
- `type` - 任务类型（code|analysis|monitor）
- `description` - 任务描述
- `priority` - 优先级（high|normal|low）
- `created_at` - 创建时间
- `source` - 来源（cli|heartbeat|user）

### 5. event 必须有 event_id

每个 event 必须有 `event_id`（uuid4），方便 debugging。

---

## 未来扩展

### Phase 1（当前）：Shadow Mode
- ✅ Event log（JSONL）
- ✅ Queue abstraction
- ✅ State projection
- ✅ Dispatcher（FIFO）
- ✅ Worker（模拟执行）
- ✅ Runner（shadow loop）

### Phase 2：真实 Agent 集成
- 替换 worker 模拟逻辑为真实 sessions_spawn
- 验证真实任务执行效果
- 记录成功率变化

### Phase 3：Priority Scheduling
- 实现 priority queue
- dispatcher 优先执行 high priority 任务
- 验证调度效果

### Phase 4：存储升级
- 从 JSONL 升级到 SQLite
- 保持 queue API 不变（queue.enqueue() 不变）
- 只改 event_log 底层实现

### Phase 5：分布式
- 从 SQLite 升级到 Redis
- 支持多 worker 并发执行
- 支持跨机器调度

---

## 核心价值

1. **Event-Driven** - 所有状态变化通过 event log，完整可追溯
2. **Queue Abstraction** - 上层不关心底层存储（JSONL/SQLite/Redis）
3. **State Projection** - 从 event log 投影出当前状态，无需维护双写
4. **Shadow Mode** - 不影响现有系统，可以安全验证
5. **模块化** - 每个模块职责单一，易于测试和扩展

---

## 文件结构

```
runtime_v2/
├── __init__.py           # 模块导出
├── event_log.py          # Event log（append + read）
├── queue.py              # Task queue（enqueue + list）
├── state.py              # State projection（events → state）
├── dispatcher.py         # Dispatcher（scheduling）
├── worker.py             # Worker（execution）
├── runner.py             # Runner（shadow loop）
├── cli.py                # CLI 工具
├── test_runtime_v2.py    # 完整流程测试
├── event_log.jsonl       # Event log 存储（自动生成）
└── README.md             # 本文档
```

---

**版本：** v1.0  
**最后更新：** 2026-03-05  
**维护者：** 小九 + 珊瑚海
