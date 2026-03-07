# AIOS Architecture — State / Execution Boundary

**日期：** 2026-03-07  
**目的：** 固化今天确认过的执行与状态边界，防止后续把 Queue、Ledger、Executor、Report 混成一层。

---

## 1. 核心结论

AIOS 里至少有两套不同抽象层的状态：

1. **Queue 状态**：描述“任务排到哪了 / 当前调度进度如何”
2. **Reality Ledger 状态**：描述“一个 action 的真实生命周期是否发生、如何结束”

它们 **不是同一个东西**，不能强行收拢为单一状态机。

### 正确原则

- **Queue 是调度层**
- **Ledger 是执行审计层**
- **task_executor 是两层之间唯一桥接点**
- **Daily report / metrics 对 Ledger 做执行真实性判断，对 Queue 做调度健康判断**

---

## 2. Queue 状态 ≠ Ledger 状态

## 2.1 Queue 状态的职责

Queue 层回答的问题是：
- 任务是否在等待执行
- 是否已经被 worker 取走
- 是否执行完成
- 是否需要重试 / 死信

典型状态示例：
- `pending`
- `queued`
- `running`
- `completed`
- `failed`
- `retrying`
- `dead_letter`

这些状态用于：
- 调度
- 重试
- 死信处理
- worker 协调
- 负载管理

**它不负责审计真实 action 生命周期。**

## 2.2 Ledger 状态的职责

Reality Ledger 回答的问题是：
- action 是否被提出（proposed）
- 是否被接受/锁定（locked）
- 是否真正开始执行（executing）
- 执行结果是 completed / failed / skipped / rejected
- 生命周期是否结束（released）

当前主链路状态：
- `proposed`
- `locked`
- `executing`
- `completed`
- `failed`
- `released`
- `skipped`
- `rejected`

这些状态用于：
- 审计真实发生过什么
- 计算 success rate / start rate / release_without_execution
- 检查执行链是否闭合
- 为日报、heartbeat、metrics 提供可信基础

**它不负责队列调度。**

## 2.3 为什么不能合并

如果把 Queue 和 Ledger 强行收拢，会出现几个问题：

1. Queue 会被迫理解 `released / skipped / rejected` 等审计语义
2. Ledger 会被迫承载 `retrying / dead_letter / worker lease` 等调度语义
3. 报告层会混淆“调度失败”和“执行失败”
4. 同一个字段会同时承载两种意义，后续指标必然失真

**结论：保留两层，严格分工。**

---

## 3. task_executor 是唯一桥接点

## 3.1 桥接责任

`core/task_executor.py` 是 Queue 层与 Ledger 层之间的唯一桥接点。

它负责：
1. 接收 heartbeat / queue 派发过来的 task
2. 读取 task 上注入的 `action_id`
3. 推进 Ledger 生命周期：
   - `locked -> executing`
   - `executing -> completed/failed`
4. 在 Ledger terminal transition 成功后，再推进 Queue terminal 状态

## 3.2 当前硬规则

### 规则 A：Ledger 先于 Queue

如果 task 已绑定 `action_id`，则：

- 先写 Ledger terminal state
- 再写 Queue terminal state

也就是：
- 先 `transition_action(action_id, "completed"/"failed")`
- 后 `_update_task_status(task_id, ...)`

### 规则 B：Ledger 失败时，Queue 不得继续写 terminal

当前已实现 `ledger_terminal_ok` gate：

- 如果 Ledger terminal transition 失败
- Queue terminal 状态更新必须跳过

原因：
- **Ledger 是 source of truth**
- Queue 是派生层，可修复
- 反过来如果 Queue 先写成功、Ledger 没写成，会制造“任务看起来完成了，但审计链不存在”的脏数据

### 规则 C：除 task_executor 外，其他模块不得同时推进两层状态

- Queue 管理模块只能改 Queue
- Ledger 模块只能改 Ledger
- 只有 `task_executor` 能同时碰两层

这条规则用于避免多入口并发改写，导致状态分叉。

---

## 4. 命令一旦入队，不可变

今天确认的另一个关键约束：

**命令模板一旦进入执行链，就必须原样复制执行，不允许 agent 自作聪明改写。**

## 4.1 背景

已经出现过 isolated session 把：
- 绝对路径改成 `~\...`
- `;` 改成 `&&`

导致 PowerShell 命令解析失败。

这说明问题不只是“命令写错了”，而是：

> 执行代理在擅自重写命令。

## 4.2 当前协议

已写入 `HEARTBEAT.md` 的硬规则：

1. 禁止把绝对路径改成 `~\`
2. 禁止把 `;` 改成 `&&`
3. 禁止改写引号、变量形式、命令顺序
4. 命令必须原样复制执行
5. 命令必须放在代码格式中，降低二次改写概率

这不是文档风格问题，而是执行可靠性协议。

## 4.3 观察标准

当前进入观察期，验收标准：

连续 3 次 isolated session 执行 heartbeat，均未出现：
- 绝对路径被改成 `~\`
- `;` 被改成 `&&`
- 引号、变量、命令顺序被改写

通过后，再考虑把该协议抽成独立的 `COMMAND_EXECUTION_RULES.md`。

---

## 5. Daily Report 读哪个层、怎么看异常

## 5.1 Daily Report 的数据层次

Daily report 必须分两层看：

### A. 历史窗口层（24h）
用于看总体趋势：
- Proposed / Accepted / Started / Completed / Failed
- acceptance rate
- start rate
- success rate
- release_without_execution_rate
- stale_lock_rate
- queue / exec / lock latency

**注意：** 如果窗口横跨修复点，24h 指标可能被旧脏数据污染。

### B. 修复后增量层（post-fix incremental observation）
用于看“当前系统真实行为是否已闭合”：
- 新 action 是否完整经过 `proposed -> locked -> executing -> completed/failed -> released`
- 是否仍存在 `locked -> released(outcome=unknown)` 的异常回收路径
- heartbeat 是否真的接入执行路径，而不是只记前半段

## 5.2 读数原则

### 原则 1：用 Ledger 判断执行真实性
关于下面这些问题，只能看 Ledger：
- 是否真的执行过
- 是否真的开始过
- 是否真的完成 / 失败
- release_without_execution 是否存在

### 原则 2：用 Queue 判断调度健康
关于下面这些问题，看 Queue：
- 是否堆积
- 是否 pending 太多
- 是否 zombie / retry / dead_letter 异常
- worker / lease / retry 行为是否正常

### 原则 3：异常要区分“历史污染”与“当前行为”

如果 24h 指标异常，不要立刻推断系统当前仍异常。
先分辨：
- 是不是修复前旧数据残留
- 修复后新增 action 是否已经恢复正常

因此日报必须明确写出：
- **Historical Window**
- **Post-Fix Incremental Observation**
- **Change Note / Confidence Note**

---

## 6. 已确认的主链路

当前可信执行主链路：

```text
heartbeat_v5.py
  -> create_action(proposed)
  -> transition_action(locked)
  -> core/task_executor.py
       -> transition_action(executing)
       -> transition_action(completed/failed)
       -> queue terminal update (only if ledger terminal ok)
  -> heartbeat_v5.py
       -> transition_action(released, release_reason="execution_done")
```

异常路径约束：

- `execute_batch` 成功：
  `locked -> executing -> completed -> released`

- `execute_batch` 失败 / 返回失败：
  `locked -> executing -> failed -> released`

- `execute_batch` 抛异常且 executor 未成功推进 `executing`：
  heartbeat 必须补 `failed -> released`

**不允许再出现：**
- `executing -> released`
- `locked -> released` 作为常规失败路径
- Ledger 失败但 Queue 继续写 terminal

---

## 7. 本文档的用途

本文档不是对外说明，而是内部工程约束。

后续如果有人改下面任一项，必须先回看本文档：
- heartbeat 执行链
- task_executor 状态推进逻辑
- queue / ledger 指标口径
- daily report 模板
- command execution rules

---

## 8. 一句话版本

> Queue 管调度，Ledger 管真实生命周期，task_executor 是唯一桥接点；命令一旦入队必须原样执行；日报必须区分历史污染和修复后真实行为。
