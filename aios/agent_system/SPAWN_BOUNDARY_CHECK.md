# SPAWN_BOUNDARY_CHECK
> 生成时间：2026-03-07
> 目的：明确谁有权写入 spawn_requests.jsonl，避免重复 spawn/重复 enqueue。

---

## 范围
仅核查 3 个核心入口：
- auto_dispatcher.py
- Task Scheduler Agent (agents/task_scheduler.py)
- Heartbeat (heartbeat_v5.py)

---

## 入口边界表

| 入口任务名 | 是否写 spawn_requests.jsonl | 触发条件 | 写入的任务类型 | 是否写 task_queue.jsonl | 是否可能与其他入口重复 | 当前结论 |
|---|---|---|---|---|---|---|
| auto_dispatcher.py | ✅ 写入 | cron 调用 check_scheduled_tasks()：每日/每周/每小时规则触发；以及处理 task_queue.jsonl 中待分发任务 | 写入 task_type + message + model + label，走 sessions_spawn | ✅ 写入（enqueue_task 写 task_queue.jsonl） | **高**：与 Task Scheduler 都写 spawn_requests.jsonl | 任务创建入口，不能删。需明确与 Task Scheduler 分工边界 |
| Task Scheduler Agent | ✅ 写入 | 定时运行后读取 task_queue.jsonl → 评分/排程 → 生成 spawn_requests.jsonl | 写入 agent + task_id + priority + status=scheduled | ✅ 读取并重写 task_queue.jsonl | **高**：与 auto_dispatcher 共用 spawn_requests.jsonl | 排程入口，不能删。需确认其职责是否只是“排程” |
| Heartbeat (heartbeat_v5.py) | ❌ 不写（只读） | 读取 spawn_requests.jsonl → 写入 spawn_pending.jsonl | 不创建任务，仅桥接执行 | ❌ 不写 | 低 | 仅桥接层，不应写入 spawn_requests.jsonl |

---

## 初步判断

1. **auto_dispatcher 与 Task Scheduler 均写 spawn_requests.jsonl**，是当前最大风险点。
2. Heartbeat 只做桥接（spawn_requests → spawn_pending），不是任务创建入口。

---

## 下一步必须确认的 4 个问题

1. **写入来源是否不同**
   - auto_dispatcher：基于规则/状态触发？
   - task_scheduler：基于排程/时间触发？

2. **写入的任务类型是否不同**
   - 是否有 task_type/agent 的明确边界？

3. **是否存在重复写同类任务**
   - 同一时刻/同一条件/同一 payload 是否可能双写？

4. **唯一规范入口是谁**
   - 需要定一句规则：谁有权写 spawn_requests.jsonl

---

## 建议边界模型（待验证）

- **Heartbeat**：只负责桥接，不写 spawn_requests
- **Task Scheduler**：只负责时间型/排程型 spawn
- **auto_dispatcher**：只负责状态/策略型 spawn

---

## ✅ 核查结果（2026-03-07 13:56）

### 发现的问题

1. **task_queue.jsonl 已出现重复任务**
   - 任务 ID: `task-1772851980360-3d68c64c`
   - 重复次数: 3 次
   - 描述: "测试路径统一"
   - 状态: completed
   - **结论: 冲突已经落地到队列层，不是理论问题**

2. **spawn_requests.jsonl 目前未发现双写**
   - 当前只有 1 条记录（LowSuccess Agent）
   - 但两个入口都有写入能力，需要提前保护

3. **缺少来源追踪**
   - 当前日志无 `source` 字段
   - 无法定位重复写来自哪个入口

### 当前状态判定

**情况 B：有重复写，但尚未确认重复执行**

- 冲突已经发生在调度层（task_queue）
- 执行层（spawn_requests/task_executions）尚未证实重复

---

## 🛠️ 解决方案（已实施）

### 1. 统一写入接口

创建 `task_queue_manager.py`，提供：

- **TaskQueueManager** - 任务队列统一写入
- **SpawnRequestManager** - Spawn 请求统一写入

### 2. 幂等保护规则

#### 规则 1：队列写入必须带来源
- 补充字段：`source` / `created_by` / `enqueued_at` / `dedup_key`
- 没有 source 的写入视为不合规

#### 规则 2：同一任务只能入队一次
- 检查：相同 task_id 且状态未终结 → 不再写
- 检查：相同 dedup_key 且时间窗口很近（60分钟）→ 不再写
- 发现重复时只记日志，不重复入队

#### 规则 3：spawn 只能幂等写
- 检查：相同 task_id/workflow_id → 不再写
- 检查：相同 dedup_key 且时间窗口很近 → 不再写
- 重复写尝试要记日志

### 3. dedup_key 计算规则

**任务队列：**
- 优先：`id:{task_id}`
- 退化：`hash:{md5(task_type|description|workflow_id)[:12]}`

**Spawn 请求：**
- 优先：`id:{task_id}:wf:{workflow_id}` 或 `id:{task_id}`
- 退化：`hash:{md5(agent_id|task|label)[:12]}`

---

## 📋 下一步行动

1. ✅ 创建统一写入接口（task_queue_manager.py）
2. ⏳ 修改 auto_dispatcher.py 调用 TaskQueueManager
3. ⏳ 修改 task_scheduler.py 调用 TaskQueueManager
4. ⏳ 测试幂等保护效果
5. ⏳ 查 task_executions.jsonl 是否有重复执行

---

*该文档记录 spawn 边界核查结果和解决方案*