# TaijiOS 五层逻辑架构图 v0.1

**创建时间：** 2026-03-09  
**状态：** Draft  
**目标：** 指导实现，不追求完整

---

## 设计原则

任意一次任务都能映射到这五层里。

每层回答 4 件事：
1. 职责是什么
2. 当前已有模块落在哪层
3. 层与层之间怎么传递
4. 哪些地方现在还缺

---

## 五层架构

```
┌─────────────────────────────────────────────────────────┐
│                      感知层 (Perception)                  │
│  输入解析、信号提取、上下文整理                            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      决策层 (Decision)                    │
│  路由、优先级、策略选择、风险判断                          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      执行层 (Execution)                   │
│  Agent 调度、Skill 执行、任务推进                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      记忆层 (Memory)                      │
│  短期状态、长期经验、失败模式、检索                        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      进化层 (Evolution)                   │
│  复盘、指标、建议、规则更新、质量门禁                      │
└─────────────────────────────────────────────────────────┘
```

---

## L1 感知层 (Perception)

### 职责
- 接收原始输入（用户消息、文件、事件、心跳）
- 提取信号（关键词、文件类型、错误模式、任务标签）
- 整理上下文（当前状态、历史记录、环境信息）

### 当前已有模块
- ✅ 消息解析（Telegram/Discord 输入）
- ✅ 文件检测（media inbound）
- ✅ 心跳触发（HEARTBEAT.md）
- ⚠️ 信号提取（部分存在，未统一）

### 输入
- 用户消息
- 文件上传
- 定时触发
- 系统事件

### 输出
```json
{
  "task_text": "用户原始输入",
  "task_type": "code|analysis|monitor|chat",
  "file_signals": ["pdf", "image", "video"],
  "error_signals": ["timeout", "network_error"],
  "runtime_state": {
    "queue_length": 3,
    "active_agents": ["coder", "analyst"],
    "recent_failures": []
  },
  "recent_history": ["上一次任务", "上上次任务"]
}
```

### 层间传递
感知层 → 决策层：`PerceptionContext`

### 当前缺失
- ❌ 统一的信号提取器
- ❌ 上下文整理器
- ❌ 多源输入归一化

---

## L2 决策层 (Decision)

### 职责
- 任务路由（该由谁处理）
- 优先级判断（先做什么后做什么）
- 策略选择（用什么方式处理）
- 风险判断（是否需要确认/降级/拒绝）

### 当前已有模块
- ✅ 任务队列（task_queue.jsonl）
- ✅ Agent 路由（coder/analyst/monitor dispatcher）
- ⚠️ 优先级（有字段，未充分使用）
- ❌ 风险判断（缺失）

### 输入
`PerceptionContext`（来自感知层）

### 输出
```json
{
  "decision": {
    "handler": "coder-dispatcher",
    "priority": "high",
    "strategy": "direct_execute",
    "risk_level": "low",
    "requires_confirmation": false,
    "reason": "代码任务，成功率高，直接执行"
  },
  "alternatives": [
    {
      "handler": "analyst-dispatcher",
      "reason": "也可以先分析再编码",
      "rejected_because": "当前任务明确，无需分析"
    }
  ]
}
```

### 层间传递
决策层 → 执行层：`DecisionResult`

### 当前缺失
- ❌ **Skill 三层触发器**（本周 MVP 1）
- ❌ 风险评估器
- ❌ 策略选择器
- ❌ 决策可解释性

---

## L3 执行层 (Execution)

### 职责
- Agent 调度（启动、监控、超时控制）
- Skill 执行（工具调用、参数传递）
- 任务推进（状态更新、结果回写）

### 当前已有模块
- ✅ Agent System（agents.json, learning_agents.py）
- ✅ sessions_spawn（真实 Agent 执行）
- ✅ Skill 注册（skills/ 目录）
- ✅ 任务队列处理（heartbeat_v5.py）
- ⚠️ 超时控制（部分存在）

### 输入
`DecisionResult`（来自决策层）

### 输出
```json
{
  "execution": {
    "agent": "coder-dispatcher",
    "skill": "git-skill",
    "status": "completed",
    "duration_ms": 21200,
    "result": "成功提交代码",
    "artifacts": ["commit_hash", "diff_file"]
  },
  "state_updates": {
    "task_status": "completed",
    "agent_stats": {
      "tasks_completed": 15,
      "success_rate": 0.93
    }
  }
}
```

### 层间传递
执行层 → 记忆层：`ExecutionResult`

### 当前缺失
- ❌ 统一的执行监控
- ❌ 资源限制（CPU/内存/时间）
- ❌ 执行沙箱

---

## L4 记忆层 (Memory)

### 职责
- 短期状态（当前队列、活跃任务、临时上下文）
- 长期经验（成功模式、失败模式、用户偏好）
- 失败模式（错误类型、修复方案）
- 检索（根据当前任务检索相关经验）

### 当前已有模块
- ✅ 短期状态（task_queue.jsonl, spawn_pending.jsonl）
- ✅ 长期记忆（MEMORY.md, memory/*.md）
- ✅ 失败记录（lessons.json）
- ✅ 检索（memory_search, memory_get）
- ⚠️ 经验沉淀（部分手动）

### 输入
`ExecutionResult`（来自执行层）

### 输出
```json
{
  "memory_update": {
    "short_term": {
      "task_completed": "task-xxx",
      "queue_updated": true
    },
    "long_term": {
      "pattern_learned": "代码任务优先用 git-skill",
      "failure_recorded": false
    },
    "retrieval": {
      "similar_tasks": ["task-yyy", "task-zzz"],
      "relevant_lessons": ["lesson-001"]
    }
  }
}
```

### 层间传递
记忆层 → 进化层：`MemorySnapshot`

### 当前缺失
- ❌ 自动经验提取
- ❌ 模式识别
- ❌ 记忆压缩（防止 MEMORY.md 无限增长）

---

## L5 进化层 (Evolution)

### 职责
- 复盘（任务成功/失败分析）
- 指标（成功率、延迟、成本）
- 建议（改进方向、优化点）
- 规则更新（自动调整策略、阈值）
- 质量门禁（改进是否可应用）

### 当前已有模块
- ✅ Self-Improving Loop（self_improving_loop.py）
- ✅ Quality Gates（quality_gates.py）
- ✅ 健康度检查（health_check.py）
- ✅ 指标记录（agents.json stats）
- ⚠️ 自动规则更新（部分存在）

### 输入
`MemorySnapshot`（来自记忆层）

### 输出
```json
{
  "evolution": {
    "metrics": {
      "success_rate_24h": 0.85,
      "avg_latency_ms": 18500,
      "cost_24h": 0.42
    },
    "insights": [
      "coder-dispatcher 成功率下降 5%",
      "git-skill 超时次数增加"
    ],
    "recommendations": [
      "调整 coder-dispatcher 超时阈值",
      "优化 git-skill 执行逻辑"
    ],
    "rule_updates": [
      {
        "rule": "coder_timeout",
        "old_value": 60,
        "new_value": 90,
        "reason": "最近超时次数增加"
      }
    ]
  }
}
```

### 层间传递
进化层 → 感知层/决策层：`EvolutionFeedback`（闭环）

### 当前缺失
- ❌ 自动规则更新机制
- ❌ A/B 测试框架
- ❌ 回滚机制

---

## 层间数据流

```
用户输入
  ↓
感知层 → PerceptionContext
  ↓
决策层 → DecisionResult
  ↓
执行层 → ExecutionResult
  ↓
记忆层 → MemorySnapshot
  ↓
进化层 → EvolutionFeedback
  ↓ (闭环)
感知层/决策层
```

---

## 当前系统映射

### 已有能力分布

| 层级 | 已有模块 | 完成度 |
|------|---------|--------|
| 感知层 | 消息解析、文件检测、心跳触发 | 60% |
| 决策层 | 任务队列、Agent 路由 | 40% |
| 执行层 | Agent System、sessions_spawn、Skill 注册 | 70% |
| 记忆层 | MEMORY.md、lessons.json、memory_search | 65% |
| 进化层 | Self-Improving Loop、Quality Gates | 55% |

### 最弱链路

**决策层（40%）** - 缺少统一的中枢判定机制

这就是为什么要优先做 **Skill 三层触发器**。

---

## 验收标准

这张图的验收标准不是"完整"，而是：

✅ **任意一次任务都能映射到这五层里**

示例任务：用户说"帮我提交代码"

1. 感知层：提取信号（"提交代码" → code 任务）
2. 决策层：路由到 coder-dispatcher，优先级 high
3. 执行层：调用 git-skill，执行 git commit + push
4. 记忆层：记录成功，更新 coder-dispatcher 统计
5. 进化层：分析成功率，无需调整

---

## 下一步

1. ✅ 完成五层架构图（本文档）
2. ⏭️ MVP 1：Skill 三层触发器
3. ⏭️ MVP 2：四层观测报告
4. ⏭️ 统一中枢判定接口

---

**版本：** v0.1  
**状态：** Draft  
**维护者：** 小九 + 珊瑚海
