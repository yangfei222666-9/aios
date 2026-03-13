# P0 真链修复完成报告

**日期：** 2026-03-13  
**执行者：** 小九  
**审核者：** 珊瑚海

---

## 修复前状态

主链断裂：任务能入队，但无法被消费执行。

**4 个断点：**
1. 两套状态名并存（"queued" vs "pending"），消费端只认 "pending"
2. 两套队列入口（task_queue.py vs task_submitter.py），字段格式不同
3. heartbeat_v6 通过 subprocess 调 v5，壳套壳
4. 执行结果只写 spawn_pending.jsonl，无人消费

---

## 修复内容

### Step 1：统一状态名 → "pending"

**改动文件（7 个）：**
- `task_queue.py` — TaskStatus 类型定义、默认值、入队状态、acquire 查询
- `heartbeat_v5.py` — 僵尸任务恢复时的目标状态
- `durable_recovery.py` — 恢复重试的目标状态
- `demo_recovery.py` — 演示恢复的目标状态
- `spawn_lock.py` — 锁释放后的状态转换 + 注释
- `spawn_manager.py` — spawn 请求创建时的初始状态
- `learning_report.py` — 队列统计的过滤条件

**数据修复：** `data/task_queue.jsonl` 中 2 个 "queued" 任务改为 "pending"

**验证：** `list_tasks(status="pending")` 能捞到所有待处理任务 ✅

### Step 2：统一队列入口

**决策：** `core/task_submitter.submit_task()` 为唯一对外提交入口（Source of Truth）

**改动：** `core/task_submitter.py` 添加文档注释，明确 TaskQueue 类仅供消费端内部使用

**验证：** 两套入口写同一文件，消费端兼容两种字段名（`id` / `task_id`）✅

### Step 3：v6 直接消费

**改动：** `heartbeat_v6.py` 的 `process_task_queue()` 从 `run_command('python heartbeat_v5.py')` 改为 `from heartbeat_v5 import process_task_queue`

**删除：** stdout 解析逻辑（正则匹配 Processed/Success/Failed）

**验证：** v6 直接调用 v5 函数，返回结构化结果 ✅

### Step 4：spawn_pending 链路验证

**确认：** 当前执行架构为桥接式：
```
Python heartbeat → spawn_pending.jsonl → OpenClaw 主会话 heartbeat → sessions_spawn → 真执行
```

**操作：** 清理 stale spawn_pending 请求，验证完整链路

**验证：** submit → consume → spawn_pending 写入 ✅

---

## 验证结果

### 第一次验证（修复过程中）
```
submit_task('P0 端到端验证：生成系统健康摘要') → pending
→ heartbeat_v6.process_task_queue() → consumed
→ spawn_pending.jsonl → 1 request written
→ task status → completed
```

### 第二次验证（干净环境）
```
queue_stats: {completed: 11, failed: 2, pending: 0}  # 干净起点
submit_task('干净闭环验证：生成当日 Agent 状态摘要') → pending
→ heartbeat_v6.process_task_queue() → consumed (9ms)
→ spawn_pending.jsonl → 1 request written
→ task status → completed
```

两次验证均通过，链路可复现。

---

## 当前链路图

```
┌─────────────────┐
│ submit_task()    │  ← 唯一对外入口
│ (task_submitter) │
└────────┬────────┘
         │ 写入 data/task_queue.jsonl (status=pending)
         ▼
┌─────────────────┐
│ heartbeat_v6    │  ← 直接调用 v5 函数
│ process_task_   │
│ queue()         │
└────────┬────────┘
         │ list_tasks(status="pending") → execute_batch()
         ▼
┌─────────────────┐
│ task_executor   │
│ _real_execute() │
└────────┬────────┘
         │ 写入 data/spawn_pending.jsonl
         │ 写入 task_executions (v1/v2)
         │ 更新 task_queue.jsonl (status=completed)
         ▼
┌─────────────────┐
│ OpenClaw 主会话  │  ← 心跳时消费
│ sessions_spawn  │
└────────┬────────┘
         │ 真正执行任务
         ▼
      [Agent 执行]
```

---

## 剩余技术债

### 高优先级
1. **spawn_pending 桥接依赖** — 执行仍依赖主会话 heartbeat 消费 spawn_pending，不是原生 worker。心跳间隔内的请求会堆积。
2. **双格式兼容** — task_submitter 用 `id` 字段，TaskQueue 用 `task_id` 字段。消费端用 `task.get("id") or task.get("task_id")` 兼容，但长期应统一。
3. **task_executions 双文件** — `task_executions.jsonl`（212 条）和 `task_executions_v2.jsonl`（10 条）并存，schema 不同。

### 中优先级
4. **Dashboard 数据源** — v3.4/v4.0 仍使用随机数，未接真实队列/Agent 数据
5. **events.jsonl 编码问题** — 文件中有非 UTF-8 字节，需要用 `errors='replace'` 读取
6. **v5 未废弃** — heartbeat_v5.py 仍是实际执行逻辑所在，v6 只是薄壳。长期应合并。

### 低优先级
7. **历史测试数据** — 队列中有旧 smoke test 任务（已 completed），可清理
8. **Evaluator API 不匹配** — QUICKSTART 引用的 `check_system_health()` 不存在

---

**结论：** P0 主链从"断裂"修复到"可运行"。两次独立验证通过，链路可复现。

**下一步：** GitHub_Researcher 真跑通一条 → Learning Loop 最小闭环
