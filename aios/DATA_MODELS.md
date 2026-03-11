# 太极OS 数据模型 v1.0

## 概述

太极OS 使用 JSONL（JSON Lines）格式存储数据，每行一个 JSON 对象。

---

## 1. 核心数据模型

### 1.1 Event（事件）

**文件：** `agent_system/data/events.jsonl`

```json
{
  "id": "evt_1234567890",
  "type": "task_completed",
  "timestamp": "2026-03-10T12:00:00Z",
  "agent": "coder-dispatcher",
  "data": {
    "task_id": "task_456",
    "duration_ms": 2100,
    "success": true
  },
  "metadata": {
    "session_id": "sess_123",
    "user": "珊瑚海"
  }
}
```

**字段说明：**
- `id` (string) - 唯一事件 ID
- `type` (string) - 事件类型（task_completed, task_failed, agent_started 等）
- `timestamp` (string) - ISO 8601 时间戳
- `agent` (string) - 触发事件的 Agent ID
- `data` (object) - 事件数据（根据类型不同）
- `metadata` (object) - 元数据

**事件类型：**
- `task_submitted` - 任务提交
- `task_started` - 任务开始
- `task_completed` - 任务完成
- `task_failed` - 任务失败
- `agent_started` - Agent 启动
- `agent_stopped` - Agent 停止
- `improvement_applied` - 改进应用
- `error_detected` - 错误检测

---

### 1.2 Task（任务）

**文件：** `agent_system/data/task_queue.jsonl`

```json
{
  "id": "task_1234567890",
  "type": "code",
  "description": "重构 scheduler.py",
  "priority": "high",
  "status": "pending",
  "created_at": "2026-03-10T12:00:00Z",
  "updated_at": "2026-03-10T12:00:00Z",
  "assigned_to": null,
  "metadata": {
    "requester": "珊瑚海",
    "tags": ["refactor", "scheduler"]
  }
}
```

**字段说明：**
- `id` (string) - 唯一任务 ID
- `type` (string) - 任务类型（code, analysis, monitor）
- `description` (string) - 任务描述
- `priority` (string) - 优先级（low, normal, high, critical）
- `status` (string) - 状态（pending, running, completed, failed）
- `created_at` (string) - 创建时间
- `updated_at` (string) - 更新时间
- `assigned_to` (string|null) - 分配的 Agent ID
- `metadata` (object) - 元数据

**任务类型：**
- `code` - 代码相关（重构、修复、优化）
- `analysis` - 分析相关（日志分析、性能分析）
- `monitor` - 监控相关（健康检查、资源监控）
- `research` - 研究相关（GitHub 学习、技术调研）
- `documentation` - 文档相关（文档更新、API 文档）

**任务状态：**
- `pending` - 待处理
- `running` - 执行中
- `completed` - 已完成
- `failed` - 失败
- `cancelled` - 已取消

---

### 1.3 Agent（代理）

**文件：** `agent_system/data/agents.json`

```json
{
  "id": "coder-dispatcher",
  "name": "Coder Dispatcher",
  "type": "dispatcher",
  "status": "active",
  "capabilities": ["code_generation", "refactoring", "bug_fixing"],
  "config": {
    "model": "claude-sonnet-4-6",
    "timeout_seconds": 120,
    "max_retries": 3
  },
  "stats": {
    "tasks_completed": 25,
    "tasks_failed": 2,
    "success_rate": 0.926,
    "avg_duration_ms": 2100
  },
  "last_active": "2026-03-10T12:00:00Z",
  "created_at": "2026-03-01T00:00:00Z"
}
```

**字段说明：**
- `id` (string) - 唯一 Agent ID
- `name` (string) - Agent 名称
- `type` (string) - Agent 类型（dispatcher, worker, monitor）
- `status` (string) - 状态（active, idle, offline, error）
- `capabilities` (array) - 能力列表
- `config` (object) - 配置
- `stats` (object) - 统计数据
- `last_active` (string) - 最后活跃时间
- `created_at` (string) - 创建时间

**Agent 类型：**
- `dispatcher` - 调度器（分发任务）
- `worker` - 工作者（执行任务）
- `monitor` - 监控器（监控系统）
- `learner` - 学习者（GitHub 学习）

**Agent 状态：**
- `active` - 活跃（正在执行任务）
- `idle` - 空闲（等待任务）
- `offline` - 离线（未启动）
- `error` - 错误（需要修复）

---

### 1.4 Lesson（经验）

**文件：** `agent_system/data/lessons.json`

```json
{
  "id": "lesson_001",
  "title": "Coder 超时问题修复",
  "category": "performance",
  "severity": "high",
  "problem": "Coder Agent 频繁超时",
  "solution": "增加超时时间到 120s",
  "rules_derived": [
    "code 类型任务默认超时 120s",
    "复杂任务优先拆分"
  ],
  "applied_at": "2026-03-10T12:00:00Z",
  "effectiveness": 0.85,
  "metadata": {
    "affected_agents": ["coder-dispatcher"],
    "related_tasks": ["task_123", "task_456"]
  }
}
```

**字段说明：**
- `id` (string) - 唯一经验 ID
- `title` (string) - 标题
- `category` (string) - 分类（performance, reliability, security）
- `severity` (string) - 严重程度（low, medium, high, critical）
- `problem` (string) - 问题描述
- `solution` (string) - 解决方案
- `rules_derived` (array) - 衍生规则
- `applied_at` (string) - 应用时间
- `effectiveness` (number) - 有效性（0-1）
- `metadata` (object) - 元数据

---

### 1.5 Metric（指标）

**文件：** `agent_system/data/metrics.jsonl`

```json
{
  "timestamp": "2026-03-10T12:00:00Z",
  "type": "system",
  "metrics": {
    "health_score": 85.71,
    "evolution_score": 72.5,
    "tasks_per_hour": 3.5,
    "success_rate": 0.85,
    "agent_utilization": 0.65
  },
  "metadata": {
    "period": "1h",
    "source": "heartbeat"
  }
}
```

**字段说明：**
- `timestamp` (string) - 时间戳
- `type` (string) - 指标类型（system, agent, task）
- `metrics` (object) - 指标数据
- `metadata` (object) - 元数据

**指标类型：**
- `system` - 系统级指标（健康度、进化分数）
- `agent` - Agent 级指标（成功率、平均耗时）
- `task` - 任务级指标（完成率、失败率）

---

### 1.6 Spawn Request（生成请求）

**文件：** `agent_system/data/spawn_pending.jsonl`

```json
{
  "id": "spawn_1234567890",
  "agent_id": "coder-dispatcher",
  "task": "重构 scheduler.py",
  "label": "refactor-scheduler",
  "cleanup": "delete",
  "runTimeoutSeconds": 300,
  "created_at": "2026-03-10T12:00:00Z",
  "status": "pending"
}
```

**字段说明：**
- `id` (string) - 唯一请求 ID
- `agent_id` (string) - Agent ID
- `task` (string) - 任务描述
- `label` (string) - 标签
- `cleanup` (string) - 清理策略（delete, keep）
- `runTimeoutSeconds` (number) - 超时时间（秒）
- `created_at` (string) - 创建时间
- `status` (string) - 状态（pending, processing, completed, failed）

---

### 1.7 Hexagram State（卦象状态）

**文件：** `agent_system/data/hexagram_state.json`

```json
{
  "current_hexagram": 1,
  "hexagram_name": "乾",
  "phase": "observation",
  "risk_level": "low",
  "allow_changes": false,
  "timestamp": "2026-03-10T12:00:00Z",
  "history": [
    {
      "hexagram": 1,
      "phase": "observation",
      "entered_at": "2026-03-08T00:00:00Z",
      "duration_hours": 48
    }
  ]
}
```

**字段说明：**
- `current_hexagram` (number) - 当前卦象（1-64）
- `hexagram_name` (string) - 卦象名称
- `phase` (string) - 阶段（observation, active, recovery）
- `risk_level` (string) - 风险等级（low, medium, high）
- `allow_changes` (boolean) - 是否允许变更
- `timestamp` (string) - 时间戳
- `history` (array) - 历史记录

---

## 2. 关系模型

### 2.1 Task → Agent

一个任务分配给一个 Agent：

```
Task.assigned_to → Agent.id
```

### 2.2 Event → Task

一个事件关联一个任务：

```
Event.data.task_id → Task.id
```

### 2.3 Event → Agent

一个事件由一个 Agent 触发：

```
Event.agent → Agent.id
```

### 2.4 Lesson → Agent

一个经验影响多个 Agent：

```
Lesson.metadata.affected_agents[] → Agent.id
```

---

## 3. 数据流

### 3.1 任务提交流程

```
1. 用户提交任务
   → 创建 Task (status: pending)
   → 写入 task_queue.jsonl

2. Heartbeat 检测任务
   → 读取 task_queue.jsonl
   → 创建 Spawn Request
   → 写入 spawn_pending.jsonl

3. Heartbeat 执行 Spawn
   → 读取 spawn_pending.jsonl
   → 调用 sessions_spawn
   → 更新 Task (status: running)
   → 清空 spawn_pending.jsonl

4. Agent 执行任务
   → 创建 Event (type: task_started)
   → 写入 events.jsonl
   → 执行任务逻辑
   → 创建 Event (type: task_completed/failed)
   → 更新 Task (status: completed/failed)

5. 记录指标
   → 创建 Metric
   → 写入 metrics.jsonl
```

### 3.2 改进应用流程

```
1. 检测问题
   → 分析 events.jsonl
   → 识别失败模式

2. 生成经验
   → 创建 Lesson
   → 写入 lessons.json

3. 应用改进
   → 更新 Agent.config
   → 写入 agents.json
   → 创建 Event (type: improvement_applied)
```

---

## 4. 数据存储

### 4.1 文件结构

```
agent_system/data/
├── events.jsonl           # 事件日志
├── task_queue.jsonl       # 任务队列
├── spawn_pending.jsonl    # 待处理的生成请求
├── metrics.jsonl          # 指标数据
├── agents.json            # Agent 配置和状态
├── lessons.json           # 经验库
└── hexagram_state.json    # 卦象状态
```

### 4.2 数据保留策略

- **events.jsonl** - 保留 30 天，超过 30 天归档
- **task_queue.jsonl** - 保留已完成任务 7 天
- **metrics.jsonl** - 保留 90 天
- **agents.json** - 永久保留
- **lessons.json** - 永久保留
- **hexagram_state.json** - 永久保留

---

## 5. 数据迁移

### 5.1 版本兼容性

当数据模型变更时，提供迁移脚本：

```bash
python migrate.py --from v1.0 --to v1.1
```

### 5.2 备份策略

每日自动备份：

```bash
python backup.py --target data --output backups/2026-03-10
```

---

## 6. 查询示例

### 6.1 查询最近 10 个事件

```python
import json

events = []
with open('agent_system/data/events.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        events.append(json.loads(line))

recent_events = sorted(events, key=lambda x: x['timestamp'], reverse=True)[:10]
```

### 6.2 查询待处理任务

```python
import json

tasks = []
with open('agent_system/data/task_queue.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        task = json.loads(line)
        if task['status'] == 'pending':
            tasks.append(task)
```

### 6.3 查询 Agent 统计

```python
import json

with open('agent_system/data/agents.json', 'r', encoding='utf-8') as f:
    agents = json.load(f)

for agent in agents:
    print(f"{agent['name']}: {agent['stats']['success_rate']:.2%}")
```

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-10
