# 太极OS API 规范 v1.0

## 概述

太极OS 提供三层 API 接口：
1. **Memory Server API** - 语义记忆服务
2. **Dashboard API** - 可视化和监控
3. **AIOS CLI** - 命令行接口

---

## 1. Memory Server API

**Base URL:** `http://127.0.0.1:7788`

### 1.1 健康检查

```http
GET /status
```

**响应：**
```json
{
  "status": "ok",
  "model_loaded": true,
  "uptime_seconds": 3600
}
```

### 1.2 语义搜索

```http
POST /query
```

**请求体：**
```json
{
  "query": "如何启动 Dashboard？",
  "top_k": 5,
  "min_score": 0.5
}
```

**响应：**
```json
{
  "results": [
    {
      "text": "启动 Dashboard: python server.py",
      "score": 0.85,
      "metadata": {
        "source": "docs/DASHBOARD_GUIDE.md",
        "timestamp": "2026-03-10T12:00:00Z"
      }
    }
  ],
  "query_time_ms": 45
}
```

### 1.3 数据摄入

```http
POST /ingest
```

**请求体：**
```json
{
  "texts": [
    "新的知识点 1",
    "新的知识点 2"
  ],
  "metadata": {
    "source": "user_input",
    "category": "knowledge"
  }
}
```

**响应：**
```json
{
  "ingested": 2,
  "status": "success"
}
```

### 1.4 反馈记录

```http
POST /feedback
```

**请求体：**
```json
{
  "query": "原始查询",
  "result_id": "result_123",
  "feedback": "positive",
  "comment": "很有帮助"
}
```

**响应：**
```json
{
  "status": "recorded"
}
```

---

## 2. Dashboard API

**Base URL:** `http://127.0.0.1:8888`

### 2.1 系统状态

```http
GET /api/status
```

**响应：**
```json
{
  "health_score": 85.71,
  "evolution_score": 72.5,
  "agents": {
    "total": 15,
    "active": 12,
    "idle": 3
  },
  "tasks": {
    "pending": 2,
    "running": 1,
    "completed": 45,
    "failed": 3
  }
}
```

### 2.2 事件列表

```http
GET /api/events?limit=50&offset=0
```

**响应：**
```json
{
  "events": [
    {
      "id": "evt_123",
      "type": "task_completed",
      "timestamp": "2026-03-10T12:00:00Z",
      "agent": "coder-dispatcher",
      "data": {
        "task_id": "task_456",
        "duration_ms": 2100
      }
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### 2.3 Agent 状态

```http
GET /api/agents
```

**响应：**
```json
{
  "agents": [
    {
      "id": "coder-dispatcher",
      "name": "Coder Dispatcher",
      "status": "active",
      "tasks_completed": 25,
      "tasks_failed": 2,
      "success_rate": 0.926,
      "last_active": "2026-03-10T12:00:00Z"
    }
  ]
}
```

### 2.4 指标数据

```http
GET /api/metrics?period=24h
```

**响应：**
```json
{
  "period": "24h",
  "metrics": {
    "tasks_per_hour": 3.5,
    "avg_task_duration_ms": 2100,
    "success_rate": 0.85,
    "agent_utilization": 0.65
  },
  "timeseries": [
    {
      "timestamp": "2026-03-10T11:00:00Z",
      "tasks_completed": 4,
      "tasks_failed": 1
    }
  ]
}
```

### 2.5 WebSocket 实时推送

```http
WS /ws
```

**消息格式：**
```json
{
  "type": "event",
  "data": {
    "event_type": "task_completed",
    "agent": "coder-dispatcher",
    "timestamp": "2026-03-10T12:00:00Z"
  }
}
```

---

## 3. AIOS CLI

### 3.1 提交任务

```bash
python aios.py submit --desc "重构 scheduler.py" --type code --priority high
```

**输出：**
```
Task submitted: task_789
Priority: high
Type: code
Status: pending
```

### 3.2 查看状态

```bash
python aios.py status
```

**输出：**
```
AIOS Status Report
==================
Health Score: 85.71/100
Evolution Score: 72.5/100

Tasks:
  Pending: 2
  Running: 1
  Completed: 45
  Failed: 3

Agents:
  Total: 15
  Active: 12
  Idle: 3
```

### 3.3 Agent 管理

```bash
python aios.py agents list
```

**输出：**
```
Agent ID              Status    Tasks    Success Rate
----------------------------------------------------
coder-dispatcher      active    25       92.6%
analyst-dispatcher    active    18       88.9%
monitor-dispatcher    idle      12       100.0%
```

### 3.4 队列管理

```bash
python aios.py queue list
```

**输出：**
```
Task ID    Type      Priority  Status    Created
-------------------------------------------------
task_789   code      high      pending   2026-03-10 12:00
task_790   analysis  normal    running   2026-03-10 11:55
```

### 3.5 触发改进

```bash
python aios.py improve --target coder-dispatcher
```

**输出：**
```
Triggering improvement for: coder-dispatcher
Analyzing recent failures...
Generating improvement suggestions...
Improvement applied: timeout increased to 120s
```

---

## 4. 错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求格式 |
| 404 | 资源不存在 | 确认资源 ID |
| 500 | 服务器内部错误 | 查看日志 |
| 503 | 服务不可用 | 检查服务状态 |

---

## 5. 认证（未来版本）

当前版本仅支持本地访问（127.0.0.1），无需认证。

未来版本将支持：
- API Key 认证
- JWT Token
- OAuth 2.0

---

## 6. 速率限制（未来版本）

当前版本无速率限制。

未来版本将实施：
- 每分钟 60 次请求
- 每小时 1000 次请求
- 超限返回 429 Too Many Requests

---

## 7. 版本控制

当前 API 版本：**v1.0**

版本策略：
- 主版本号变更：不兼容的 API 变更
- 次版本号变更：向后兼容的功能新增
- 修订号变更：向后兼容的问题修复

---

## 8. 示例代码

### Python

```python
import requests

# Memory Server 查询
response = requests.post(
    "http://127.0.0.1:7788/query",
    json={
        "query": "如何启动 Dashboard？",
        "top_k": 5
    }
)
results = response.json()["results"]

# Dashboard 状态
response = requests.get("http://127.0.0.1:8888/api/status")
status = response.json()
print(f"Health Score: {status['health_score']}")
```

### JavaScript

```javascript
// Memory Server 查询
const response = await fetch('http://127.0.0.1:7788/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: '如何启动 Dashboard？',
    top_k: 5
  })
});
const results = await response.json();

// Dashboard WebSocket
const ws = new WebSocket('ws://127.0.0.1:8888/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

### cURL

```bash
# Memory Server 查询
curl -X POST http://127.0.0.1:7788/query \
  -H "Content-Type: application/json" \
  -d '{"query": "如何启动 Dashboard？", "top_k": 5}'

# Dashboard 状态
curl http://127.0.0.1:8888/api/status
```

---

## 9. 更新日志

### v1.0 (2026-03-10)
- 初始版本
- Memory Server API
- Dashboard API
- AIOS CLI

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-10
