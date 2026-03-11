# 太极OS Dashboard - 数据模型文档

**版本：** v1.0  
**最后更新：** 2026-03-10

---

## 1. Agent（Agent）

### 数据结构
```typescript
interface Agent {
  id: string;                    // Agent ID（唯一标识）
  name: string;                  // Agent 名称
  type: AgentType;               // Agent 类型
  status: AgentStatus;           // 当前状态
  description: string;           // 描述
  stats: AgentStats;             // 统计数据
  last_run: string;              // 最后运行时间（ISO 8601）
  created_at: string;            // 创建时间（ISO 8601）
}

type AgentType = 'learning' | 'executor' | 'monitor';

type AgentStatus = 'active' | 'idle' | 'failed' | 'disabled';

interface AgentStats {
  total_tasks: number;           // 总任务数
  completed_tasks: number;       // 完成任务数
  failed_tasks: number;          // 失败任务数
  success_rate: number;          // 成功率（0-100）
  avg_execution_time: number;    // 平均执行时间（秒）
}
```

### 示例
```json
{
  "id": "agent-001",
  "name": "GitHub_Researcher",
  "type": "learning",
  "status": "active",
  "description": "搜索和分析最新项目",
  "stats": {
    "total_tasks": 45,
    "completed_tasks": 43,
    "failed_tasks": 2,
    "success_rate": 95.5,
    "avg_execution_time": 12.5
  },
  "last_run": "2026-03-10T18:30:00Z",
  "created_at": "2026-03-01T10:00:00Z"
}
```

---

## 2. Task（任务）

### 数据结构
```typescript
interface Task {
  id: string;                    // 任务 ID（唯一标识）
  type: TaskType;                // 任务类型
  status: TaskStatus;            // 当前状态
  priority: TaskPriority;        // 优先级
  description: string;           // 任务描述
  agent_id: string;              // 执行 Agent ID
  agent_name: string;            // 执行 Agent 名称
  result?: TaskResult;           // 执行结果（可选）
  logs?: LogEntry[];             // 执行日志（可选）
  created_at: string;            // 创建时间（ISO 8601）
  started_at?: string;           // 开始时间（ISO 8601，可选）
  completed_at?: string;         // 完成时间（ISO 8601，可选）
  execution_time?: number;       // 执行时间（秒，可选）
}

type TaskType = 'code' | 'analysis' | 'monitor' | 'learning';

type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

type TaskPriority = 'high' | 'normal' | 'low';

interface TaskResult {
  success: boolean;              // 是否成功
  message: string;               // 结果消息
  data?: any;                    // 结果数据（可选）
}

interface LogEntry {
  time: string;                  // 时间（ISO 8601）
  level: LogLevel;               // 日志级别
  message: string;               // 日志消息
}

type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
```

### 示例
```json
{
  "id": "task-001",
  "type": "code",
  "status": "completed",
  "priority": "high",
  "description": "重构 scheduler.py",
  "agent_id": "agent-002",
  "agent_name": "Coder_Agent",
  "result": {
    "success": true,
    "message": "重构完成",
    "data": {
      "files_modified": ["scheduler.py"]
    }
  },
  "logs": [
    {
      "time": "2026-03-10T18:00:00Z",
      "level": "INFO",
      "message": "开始执行任务"
    },
    {
      "time": "2026-03-10T18:15:00Z",
      "level": "INFO",
      "message": "任务完成"
    }
  ],
  "created_at": "2026-03-10T18:00:00Z",
  "started_at": "2026-03-10T18:00:05Z",
  "completed_at": "2026-03-10T18:15:00Z",
  "execution_time": 15.2
}
```

---

## 3. Skill（技能）

### 数据结构
```typescript
interface Skill {
  id: string;                    // Skill ID（唯一标识）
  name: string;                  // Skill 名称
  version: string;               // 版本号
  status: SkillStatus;           // 当前状态
  description: string;           // 描述
  trigger_conditions: string[];  // 触发条件
  stats: SkillStats;             // 统计数据
  last_used: string;             // 最后使用时间（ISO 8601）
  created_at: string;            // 创建时间（ISO 8601）
}

type SkillStatus = 'production' | 'draft' | 'testing' | 'deprecated';

interface SkillStats {
  call_count: number;            // 调用次数
  success_count: number;         // 成功次数
  failed_count: number;          // 失败次数
  success_rate: number;          // 成功率（0-100）
  avg_execution_time: number;    // 平均执行时间（秒）
}
```

### 示例
```json
{
  "id": "skill-001",
  "name": "heartbeat_alert_deduper",
  "version": "1.0.0",
  "status": "production",
  "description": "告警去重工具",
  "trigger_conditions": [
    "heartbeat",
    "alert",
    "告警"
  ],
  "stats": {
    "call_count": 234,
    "success_count": 232,
    "failed_count": 2,
    "success_rate": 99.1,
    "avg_execution_time": 0.5
  },
  "last_used": "2026-03-10T18:30:00Z",
  "created_at": "2026-03-01T10:00:00Z"
}
```

---

## 4. Alert（告警）

### 数据结构
```typescript
interface Alert {
  id: string;                    // 告警 ID（唯一标识）
  timestamp: string;             // 时间（ISO 8601）
  level: AlertLevel;             // 告警级别
  source: string;                // 来源
  message: string;               // 告警消息
  status: AlertStatus;           // 当前状态
  metadata?: any;                // 元数据（可选）
  acknowledged_at?: string;      // 确认时间（ISO 8601，可选）
  resolved_at?: string;          // 解决时间（ISO 8601，可选）
}

type AlertLevel = 'INFO' | 'WARN' | 'CRIT';

type AlertStatus = 'new' | 'acknowledged' | 'resolved';
```

### 示例
```json
{
  "id": "alert-001",
  "timestamp": "2026-03-10T18:00:00Z",
  "level": "WARN",
  "source": "coder-dispatcher",
  "message": "连续失败 3 次",
  "status": "new",
  "metadata": {
    "failure_count": 3,
    "last_error": "timeout"
  }
}
```

---

## 5. SystemHealth（系统健康度）

### 数据结构
```typescript
interface SystemHealth {
  health_score: number;          // 健康分数（0-100）
  status: HealthStatus;          // 状态
  uptime_seconds: number;        // 运行时间（秒）
  last_check: string;            // 最后检查时间（ISO 8601）
}

type HealthStatus = 'healthy' | 'warning' | 'critical';
```

### 示例
```json
{
  "health_score": 85.5,
  "status": "healthy",
  "uptime_seconds": 86400,
  "last_check": "2026-03-10T19:00:00Z"
}
```

---

## 6. SystemStats（系统统计）

### 数据结构
```typescript
interface SystemStats {
  evolution_score: number;       // 进化分数（0-100）
  active_agents: number;         // 活跃 Agent 数
  total_tasks: number;           // 总任务数
  task_success_rate: number;     // 任务成功率（0-100）
  pending_tasks: number;         // 待处理任务数
  running_tasks: number;         // 执行中任务数
  completed_tasks: number;       // 已完成任务数
  failed_tasks: number;          // 失败任务数
}
```

### 示例
```json
{
  "evolution_score": 78.5,
  "active_agents": 12,
  "total_tasks": 1523,
  "task_success_rate": 92.3,
  "pending_tasks": 5,
  "running_tasks": 2,
  "completed_tasks": 1500,
  "failed_tasks": 16
}
```

---

## 7. TrendData（趋势数据）

### 数据结构
```typescript
interface TrendData {
  date: string;                  // 日期（YYYY-MM-DD）
  value: number;                 // 数值
}

interface TrendDataSet {
  [metric: string]: TrendData[]; // 指标名 -> 趋势数据数组
}
```

### 示例
```json
{
  "health_score": [
    { "date": "2026-03-04", "value": 85.5 },
    { "date": "2026-03-05", "value": 87.2 },
    { "date": "2026-03-06", "value": 86.8 }
  ],
  "task_success_rate": [
    { "date": "2026-03-04", "value": 92.3 },
    { "date": "2026-03-05", "value": 93.1 },
    { "date": "2026-03-06", "value": 92.8 }
  ]
}
```

---

## 8. Log（日志）

### 数据结构
```typescript
interface Log {
  id: string;                    // 日志 ID（唯一标识）
  timestamp: string;             // 时间（ISO 8601）
  level: LogLevel;               // 日志级别
  source: string;                // 来源
  message: string;               // 日志消息
  metadata?: any;                // 元数据（可选）
}

type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
```

### 示例
```json
{
  "id": "log-001",
  "timestamp": "2026-03-10T18:30:00Z",
  "level": "INFO",
  "source": "heartbeat",
  "message": "Heartbeat completed successfully",
  "metadata": {
    "duration": 1.2,
    "tasks_processed": 3
  }
}
```

---

## 9. PaginatedResponse（分页响应）

### 数据结构
```typescript
interface PaginatedResponse<T> {
  items: T[];                    // 数据项数组
  total: number;                 // 总数
  page: number;                  // 当前页码
  limit: number;                 // 每页数量
  has_next: boolean;             // 是否有下一页
  has_prev: boolean;             // 是否有上一页
}
```

### 示例
```json
{
  "items": [ ... ],
  "total": 1523,
  "page": 1,
  "limit": 20,
  "has_next": true,
  "has_prev": false
}
```

---

## 10. APIResponse（API 响应）

### 数据结构
```typescript
interface APIResponse<T> {
  success: boolean;              // 是否成功
  data?: T;                      // 数据（可选）
  error?: APIError;              // 错误（可选）
  timestamp: string;             // 时间戳（ISO 8601）
}

interface APIError {
  code: string;                  // 错误码
  message: string;               // 错误消息
  details?: any;                 // 错误详情（可选）
}
```

### 示例（成功）
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-03-10T19:00:00Z"
}
```

### 示例（失败）
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Agent not found",
    "details": {
      "agent_id": "agent-999"
    }
  },
  "timestamp": "2026-03-10T19:00:00Z"
}
```

---

## 关系图

```
Agent (1) ----< (N) Task
  |
  +-- AgentStats

Task (1) ----< (N) LogEntry
  |
  +-- TaskResult

Skill (1) ----< (N) SkillCallHistory
  |
  +-- SkillStats

Alert (1) ---- (1) AlertMetadata

SystemHealth (1) ---- (1) SystemStats

TrendData (N) ---- (1) Metric
```

---

## 字段约束

### 时间格式
所有时间字段使用 ISO 8601 格式：`YYYY-MM-DDTHH:mm:ssZ`

### ID 格式
所有 ID 字段使用以下格式：
- Agent ID: `agent-{number}` 或 `agent-{uuid}`
- Task ID: `task-{number}` 或 `task-{uuid}`
- Skill ID: `skill-{number}` 或 `skill-{uuid}`
- Alert ID: `alert-{number}` 或 `alert-{uuid}`
- Log ID: `log-{number}` 或 `log-{uuid}`

### 数值范围
- `health_score`: 0-100
- `evolution_score`: 0-100
- `success_rate`: 0-100
- `execution_time`: >= 0（秒）
- `uptime_seconds`: >= 0

---

**版本：** v1.0  
**最后更新：** 2026-03-10
