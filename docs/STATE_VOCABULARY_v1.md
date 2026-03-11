# 统一状态词表 v1

**版本：** v1.0  
**创建日期：** 2026-03-11  
**维护者：** 小九 + 珊瑚海

---

## 核心原则

**不要让一个 `status` 字段承载所有含义。**

太极OS 的状态混乱本质上是把这些东西混在一起了：
- 是否注册
- 是否可执行
- 是否验收通过
- 最近一次运行结果
- 是否启用/可路由

**解决方案：拆成 3 层状态 + 2 个辅助标记。**

---

## 1. readiness_status

**回答：** 这个对象现在"准备到哪一步了"

**适用于：** Agent / Skill

**允许值：**

| 状态 | 含义 |
|------|------|
| `registered` | 已登记，尚未确认可执行 |
| `executable` | 已有可执行入口 |
| `validated` | 已通过正式验收 |
| `production-candidate` | 已可用，但还在观察/调优 |
| `production-ready` | 已可进入日常运行 |
| `stable` | 已连续观察通过，稳定可信 |
| `archived` | 已归档，不再参与日常运行 |
| `not-executable` | 已注册，但当前不可执行 |
| `not-evaluable` | 当前不满足验收前提，不能进入正式验收 |

---

## 2. run_status

**回答：** 最近一次运行结果是什么

**适用于：** Agent / Skill / Task

**允许值：**

| 状态 | 含义 |
|------|------|
| `no-sample` | 从未运行过 |
| `queued` | 已进入队列，等待执行 |
| `running` | 正在执行中 |
| `success` | 执行成功 |
| `partial` | 部分成功 |
| `failed` | 执行失败 |
| `timeout` | 执行超时 |
| `zombie-recovered` | 僵尸任务已恢复 |
| `blocked` | 被前置条件阻塞 |
| `canceled` | 已取消 |

**规则：**
- 没跑过，不要空着，统一记 `no-sample`
- 被前置条件挡住，统一记 `blocked`

---

## 3. health_status

**回答：** 当前运行健康度如何

**适用于：** Agent / Skill / System Component

**允许值：**

| 状态 | 含义 |
|------|------|
| `healthy` | 运行正常 |
| `degraded` | 功能降级，但仍可用 |
| `blocked` | 被阻塞，无法运行 |
| `unknown` | 状态不明 |

**示例：**
- Code_Reviewer 规则刚修完但还在观察 → `degraded` 或 `healthy`
- Memory Server 状态不清楚 → `unknown`

---

## 4. 辅助标记（不是 status）

### A. enabled

**回答：** 是否启用

**类型：** `boolean`

**允许值：** `true` / `false`

### B. routable

**回答：** 是否允许被路由

**类型：** `boolean`

**允许值：** `true` / `false`

---

## 5. 明确规定：这些词以后不再当主状态用

以下词可以保留为辅助信息，但**不能再当统一状态**：
- `mode`
- `active`
- `disabled`
- `shadow`
- `production_ready`（布尔）
- `routable`（作为主状态）

**原因：** 它们描述的是不同维度，不能混成一个状态。

---

## 6. 旧概念 → 新词表映射

### Agent 示例

#### GitHub_Researcher（生产就绪）
```json
{
  "readiness_status": "production-ready",
  "run_status": "success",
  "health_status": "healthy",
  "enabled": true,
  "routable": true
}
```

#### Code_Reviewer（生产候选）
```json
{
  "readiness_status": "production-candidate",
  "run_status": "success",
  "health_status": "healthy",
  "enabled": true,
  "routable": true,
  "notes": ["rule-tuned"]
}
```

#### Error_Analyzer（生产就绪）
```json
{
  "readiness_status": "production-ready",
  "run_status": "success",
  "health_status": "healthy",
  "enabled": true,
  "routable": true,
  "notes": ["multi-source-validated"]
}
```

#### 已注册但没跑过的 Agent
```json
{
  "readiness_status": "registered",
  "run_status": "no-sample",
  "health_status": "unknown",
  "enabled": false,
  "routable": false
}
```

#### 已注册但确认没有执行入口
```json
{
  "readiness_status": "not-executable",
  "run_status": "no-sample",
  "health_status": "blocked"
}
```

---

### Skill 示例

#### heartbeat_alert_deduper（已验证，待试运行）
```json
{
  "readiness_status": "validated",
  "run_status": "no-sample",
  "health_status": "unknown",
  "enabled": false,
  "routable": false
}
```

等补了执行入口并试运行后，再升级。

---

### Task 示例

任务不需要 `readiness_status`，只需要：

```json
{
  "run_status": "queued|running|success|partial|failed|timeout|blocked|canceled|zombie-recovered",
  "health_status": "healthy|degraded|blocked|unknown"
}
```

---

## 7. 使用规则

### 硬规则

以后所有首次验收前，必须先看：
- `readiness_status`
- `run_status`
- `health_status`

**不允许再只看：**
- `enabled`
- `routable`
- `active`

### 迁移策略

1. **先定义，再迁移** — 不要一上来全局替换
2. **先落文档和样例** — 建立 `state_index.json` 样例
3. **先手工映射 4 个对象** — GitHub_Researcher, Code_Reviewer, Error_Analyzer, heartbeat_alert_deduper
4. **再决定下一步** — Dashboard, health report, daily report, agents.json

---

## 8. 执行口径

**统一状态词表 v1：**

先定义 3 层状态（`readiness_status` / `run_status` / `health_status`）和 2 个辅助标记（`enabled` / `routable`），先落文档和 `state_index` 样例，不做全局替换。

---

**版本历史：**
- v1.0 (2026-03-11) - 初始版本，定义 3 层状态 + 2 个辅助标记
