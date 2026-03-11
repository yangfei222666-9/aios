# Spawn 执行链契约统一设计

**存档 ID：** r8n2fd  
**状态：** design-only（观察期内不落地）  
**创建时间：** 2026-03-10  
**触发原因：** heartbeat 写端与执行器读端文件不一致，导致 sessions_spawn 未接上

---

## 1. 问题定义

### 当前状态

```
heartbeat_full.py  ──写入──>  spawn_requests.jsonl
                                    ↓
                              （断裂点：无人搬运）
                                    ↓
OpenClaw 主会话心跳  ──读取──>  spawn_pending.jsonl  ──>  sessions_spawn
```

**根因：** 写端和读端的文件契约没对齐。heartbeat 创建请求写入 `spawn_requests.jsonl`，但 HEARTBEAT.md 中定义的执行流程读取的是 `spawn_pending.jsonl`。

### 影响范围

- 所有通过 heartbeat 创建的 spawn 请求都不会被执行
- 任务队列中的任务虽然被处理，但 Agent 不会真正启动
- 回写链（spawn_results.jsonl → task_queue.jsonl 状态更新）无法闭环

---

## 2. 方案对比

### 方案 A：统一文件契约（推荐）

**核心思路：** 让 heartbeat 直接写入 `spawn_pending.jsonl`，消除中间环节。

```
heartbeat_full.py  ──写入──>  spawn_pending.jsonl
                                    ↓
OpenClaw 主会话心跳  ──读取──>  spawn_pending.jsonl  ──>  sessions_spawn
```

**改动点：**
1. `heartbeat_full.py` 中将输出文件从 `spawn_requests.jsonl` 改为 `spawn_pending.jsonl`
2. 确认记录格式与执行器期望一致
3. 废弃 `spawn_requests.jsonl`（或保留为历史归档）

**优点：**
- 最简单，无中间层
- 写端和读端直接对齐
- 无额外维护成本

**风险：**
- 需要确认 heartbeat 写入的记录格式与执行器期望完全一致
- 如果未来需要在创建和执行之间加审批/过滤，没有中间层

**缓解：**
- 格式对齐可以在落地前通过对比两个文件的 schema 验证
- 审批/过滤需求出现时再加中间层（YAGNI 原则）

---

### 方案 B：桥接脚本（过渡方案）

**核心思路：** 保留两个文件，用 `spawn_bridge.py` 搬运。

```
heartbeat_full.py  ──写入──>  spawn_requests.jsonl
                                    ↓
                            spawn_bridge.py（搬运 + 去重）
                                    ↓
OpenClaw 主会话心跳  ──读取──>  spawn_pending.jsonl  ──>  sessions_spawn
```

**改动点：**
1. 新增 `spawn_bridge.py`
2. 在心跳流程中调用 bridge（在读取 spawn_pending.jsonl 之前）
3. bridge 负责：转移新请求、幂等去重、记录日志

**优点：**
- 不改现有写端逻辑
- 可以在中间层加过滤/审批
- 可以记录搬运日志

**风险：**
- 多一个组件需要维护
- 多一个故障点
- 长期来看增加系统复杂度

---

## 3. 推荐方案

**方案 A**，理由：

1. 当前系统复杂度已经够高，不需要再加中间层
2. heartbeat 和执行器之间不需要审批/过滤（heartbeat 本身就是可信的内部组件）
3. 最小改动原则 — 改一个文件名比新增一个脚本更简单
4. 符合太极OS"先做得更稳"的原则

---

## 4. 落地计划（观察期后执行）

### Step 1：Schema 对齐验证

对比 `spawn_requests.jsonl` 和 `spawn_pending.jsonl` 的记录格式：

**spawn_pending.jsonl 期望格式（HEARTBEAT.md 定义）：**
```json
{
  "agent_id": "string",
  "task": "string",
  "label": "string",
  "cleanup": "delete|keep",
  "runTimeoutSeconds": 300
}
```

**spawn_requests.jsonl 实际格式（heartbeat_full.py 写入）：**
```
待验证 — 落地前必须对比确认
```

### Step 2：修改 heartbeat_full.py

将输出文件从 `spawn_requests.jsonl` 改为 `spawn_pending.jsonl`，确保格式一致。

### Step 3：验证闭环

1. 手动创建一条测试记录写入 spawn_pending.jsonl
2. 等待下一次心跳
3. 确认 sessions_spawn 被调用
4. 确认 spawn_results.jsonl 有回写
5. 确认 task_queue.jsonl 状态更新

### Step 4：清理

1. 归档 spawn_requests.jsonl（移到 data/archive/）
2. 更新 HEARTBEAT.md 中的相关说明
3. 更新 heartbeat_full.py 的注释

---

## 5. 幂等键设计

无论哪个方案，都需要明确幂等键，防止重复执行：

**推荐幂等键：** `task_id`（如果有）或 `agent_id + task_hash + timestamp`

**执行器行为：**
- 读取 spawn_pending.jsonl 中的记录
- 对每条记录调用 sessions_spawn
- 成功后从 spawn_pending.jsonl 中移除（或标记为 executed）
- 失败后保留，下次心跳重试（最多 3 次）

---

## 6. 回写链完整定义

```
sessions_spawn 执行
    ↓
spawn_results.jsonl  ←  记录执行结果（成功/失败/超时）
    ↓
task_queue.jsonl  ←  更新对应任务状态（completed/failed）
    ↓
task_executions.jsonl  ←  记录执行详情（耗时、输出摘要）
```

**回写链验证属于 P2，观察期后在 spawn 契约统一之后再做。**

---

## 7. 决策记录

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-03-10 | 观察期内不做桥接实现 | 珊瑚海确认：不改主链路 |
| 2026-03-10 | 推荐方案 A（统一文件） | 最小改动、最低复杂度 |
| 2026-03-10 | 方案 B 作为备选 | 若方案 A 有格式不兼容问题 |

---

**一句话收口：** 先把路权定义清楚，观察期后一步到位统一契约。
