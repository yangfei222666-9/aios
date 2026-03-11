# 太极OS Dashboard - API 接口文档

**版本：** v1.0  
**最后更新：** 2026-03-10  
**Base URL：** `http://localhost:8888/api`

---

## 认证

当前版本暂不需要认证（本地开发环境）。

未来版本可能需要：
- API Key（Header: `X-API-Key`）
- JWT Token（Header: `Authorization: Bearer <token>`）

---

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-03-10T19:00:00Z"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  },
  "timestamp": "2026-03-10T19:00:00Z"
}
```

---

## 1. 系统状态 API

### 1.1 获取系统健康度
**端点：** `GET /system/health`

**响应：**
```json
{
  "success": true,
  "data": {
    "health_score": 85.5,
    "status": "healthy",
    "uptime_seconds": 86400,
    "last_check": "2026-03-10T19:00:00Z"
  }
}
```

**字段说明：**
- `health_score` - 健康分数（0-100）
- `status` - 状态（healthy/warning/critical）
- `uptime_seconds` - 运行时间（秒）
- `last_check` - 最后检查时间

### 1.2 获取系统统计
**端点：** `GET /system/stats`

**响应：**
```json
{
  "success": true,
  "data": {
    "evolution_score": 78.5,
    "active_agents": 12,
    "total_tasks": 1523,
    "task_success_rate": 92.3,
    "pending_tasks": 5,
    "running_tasks": 2,
    "completed_tasks": 1500,
    "failed_tasks": 16
  }
}
```

---

## 2. Agent API

### 2.1 获取 Agent 列表
**端点：** `GET /agents`

**查询参数：**
- `status` - 状态筛选（active/idle/failed/disabled）
- `type` - 类型筛选（learning/executor/monitor）
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 20）
- `search` - 搜索关键词

**响应：**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "agent-001",
        "name": "GitHub_Researcher",
        "type": "learning",
        "status": "active",
        "description": "搜索和分析最新项目",
        "total_tasks": 45,
        "success_rate": 95.5,
        "last_run": "2026-03-10T18:30:00Z",
        "created_at": "2026-03-01T10:00:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "limit": 20
  }
}
```

### 2.2 获取 Agent 详情
**端点：** `GET /agents/:agentId`

**响应：**
```json
{
  "success": true,
  "data": {
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
}
```

### 2.3 获取 Agent 任务历史
**端点：** `GET /agents/:agentId/tasks`

**查询参数：**
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 20）

**响应：**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "task-001",
        "type": "learning",
        "status": "completed",
        "description": "搜索 AIOS 相关项目",
        "created_at": "2026-03-10T18:00:00Z",
        "completed_at": "2026-03-10T18:15:00Z",
        "execution_time": 15.2
      }
    ],
    "total": 45,
    "page": 1,
    "limit": 20
  }
}
```

### 2.4 获取 Agent 趋势数据
**端点：** `GET /agents/:agentId/trends`

**查询参数：**
- `days` - 天数（默认 7）

**响应：**
```json
{
  "success": true,
  "data": {
    "execution_time": [
      { "date": "2026-03-04", "value": 12.3 },
      { "date": "2026-03-05", "value": 11.8 },
      { "date": "2026-03-06", "value": 13.1 }
    ],
    "success_rate": [
      { "date": "2026-03-04", "value": 94.5 },
      { "date": "2026-03-05", "value": 96.2 },
      { "date": "2026-03-06", "value": 95.8 }
    ]
  }
}
```

---

## 3. 任务 API

### 3.1 获取任务列表
**端点：** `GET /tasks`

**查询参数：**
- `status` - 状态筛选（pending/running/completed/failed）
- `type` - 类型筛选（code/analysis/monitor/learning）
- `priority` - 优先级筛选（high/normal/low）
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 20）
- `search` - 搜索关键词

**响应：**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "task-001",
        "type": "code",
        "status": "completed",
        "priority": "high",
        "description": "重构 scheduler.py",
        "agent_id": "agent-002",
        "agent_name": "Coder_Agent",
        "created_at": "2026-03-10T18:00:00Z",
        "completed_at": "2026-03-10T18:15:00Z",
        "execution_time": 15.2
      }
    ],
    "total": 1523,
    "page": 1,
    "limit": 20
  }
}
```

### 3.2 获取任务详情
**端点：** `GET /tasks/:taskId`

**响应：**
```json
{
  "success": true,
  "data": {
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
      "files_modified": ["scheduler.py"]
    },
    "logs": [
      { "time": "2026-03-10T18:00:00Z", "level": "INFO", "message": "开始执行任务" },
      { "time": "2026-03-10T18:15:00Z", "level": "INFO", "message": "任务完成" }
    ],
    "created_at": "2026-03-10T18:00:00Z",
    "started_at": "2026-03-10T18:00:05Z",
    "completed_at": "2026-03-10T18:15:00Z",
    "execution_time": 15.2
  }
}
```

### 3.3 获取任务队列统计
**端点：** `GET /tasks/stats`

**响应：**
```json
{
  "success": true,
  "data": {
    "total": 1523,
    "pending": 5,
    "running": 2,
    "completed": 1500,
    "failed": 16,
    "success_rate": 98.9
  }
}
```

---

## 4. Skill API

### 4.1 获取 Skill 列表
**端点：** `GET /skills`

**查询参数：**
- `status` - 状态筛选（production/draft/testing/deprecated）
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 20）
- `search` - 搜索关键词

**响应：**
```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "id": "skill-001",
        "name": "heartbeat_alert_deduper",
        "version": "1.0.0",
        "status": "production",
        "description": "告警去重工具",
        "call_count": 234,
        "success_rate": 99.1,
        "last_used": "2026-03-10T18:30:00Z",
        "created_at": "2026-03-01T10:00:00Z"
      }
    ],
    "total": 45,
    "page": 1,
    "limit": 20
  }
}
```

### 4.2 获取 Skill 详情
**端点：** `GET /skills/:skillId`

**响应：**
```json
{
  "success": true,
  "data": {
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
}
```

### 4.3 获取 Skill 使用历史
**端点：** `GET /skills/:skillId/history`

**查询参数：**
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 20）

**响应：**
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "id": "call-001",
        "status": "success",
        "execution_time": 0.5,
        "timestamp": "2026-03-10T18:30:00Z"
      }
    ],
    "total": 234,
    "page": 1,
    "limit": 20
  }
}
```

---

## 5. 日志 API

### 5.1 获取系统日志
**端点：** `GET /logs`

**查询参数：**
- `level` - 级别筛选（DEBUG/INFO/WARN/ERROR/CRITICAL）
- `source` - 来源筛选
- `start_time` - 开始时间（ISO 8601）
- `end_time` - 结束时间（ISO 8601）
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 50）
- `search` - 搜索关键词

**响应：**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": "log-001",
        "timestamp": "2026-03-10T18:30:00Z",
        "level": "INFO",
        "source": "heartbeat",
        "message": "Heartbeat completed successfully"
      }
    ],
    "total": 5234,
    "page": 1,
    "limit": 50
  }
}
```

---

## 6. 告警 API

### 6.1 获取告警列表
**端点：** `GET /alerts`

**查询参数：**
- `level` - 级别筛选（INFO/WARN/CRIT）
- `status` - 状态筛选（new/acknowledged/resolved）
- `start_time` - 开始时间（ISO 8601）
- `end_time` - 结束时间（ISO 8601）
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 20）

**响应：**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert-001",
        "timestamp": "2026-03-10T18:00:00Z",
        "level": "WARN",
        "source": "coder-dispatcher",
        "message": "连续失败 3 次",
        "status": "new"
      }
    ],
    "total": 23,
    "page": 1,
    "limit": 20
  }
}
```

### 6.2 标记告警状态
**端点：** `PATCH /alerts/:alertId`

**请求体：**
```json
{
  "status": "acknowledged"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "id": "alert-001",
    "status": "acknowledged",
    "updated_at": "2026-03-10T19:00:00Z"
  }
}
```

### 6.3 获取告警统计
**端点：** `GET /alerts/stats`

**响应：**
```json
{
  "success": true,
  "data": {
    "total": 23,
    "new": 5,
    "acknowledged": 10,
    "resolved": 8,
    "critical": 2,
    "warning": 15,
    "info": 6
  }
}
```

---

## 7. 趋势数据 API

### 7.1 获取系统趋势
**端点：** `GET /trends/system`

**查询参数：**
- `days` - 天数（默认 7）
- `metrics` - 指标列表（逗号分隔，如：health_score,task_success_rate）

**响应：**
```json
{
  "success": true,
  "data": {
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
}
```

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| `INVALID_REQUEST` | 请求参数无效 |
| `NOT_FOUND` | 资源不存在 |
| `INTERNAL_ERROR` | 服务器内部错误 |
| `UNAUTHORIZED` | 未授权 |
| `FORBIDDEN` | 禁止访问 |

---

## WebSocket 实时更新（可选）

### 连接
**端点：** `ws://localhost:8888/ws`

### 订阅事件
```json
{
  "action": "subscribe",
  "channels": ["system", "agents", "tasks", "alerts"]
}
```

### 接收更新
```json
{
  "channel": "tasks",
  "event": "task_completed",
  "data": {
    "id": "task-001",
    "status": "completed"
  }
}
```

---

**版本：** v1.0  
**最后更新：** 2026-03-10
