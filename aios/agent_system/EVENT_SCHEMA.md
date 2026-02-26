# AIOS 统一事件 Schema v1.0

## 核心原则
- 所有事件必须包含：timestamp, event_type, trace_id
- 所有任务必须记录：task_id, task_type, status, duration_ms
- 所有错误必须记录：error_type, error_message, retry_count

## 事件类型

### 1. Task Event（任务事件）
```json
{
  "timestamp": "2026-02-26T05:30:00.000Z",
  "event_type": "task",
  "trace_id": "task-1234567890",
  "task_id": "task-1234567890",
  "task_type": "code|analysis|monitor|research|design",
  "description": "任务描述",
  "priority": "high|normal|low",
  "status": "pending|running|success|failed",
  "duration_ms": 1234,
  "model": "claude-sonnet-4-6",
  "cost_usd": 0.001,
  "retry_count": 0,
  "error_type": "timeout|api_error|execution_error|null",
  "error_message": "错误信息或null",
  "metadata": {
    "agent": "coder-agent",
    "source": "orchestrator",
    "output_file": "path/to/output.py"
  }
}
```

### 2. API Call Event（API调用事件）
```json
{
  "timestamp": "2026-02-26T05:30:00.000Z",
  "event_type": "api_call",
  "trace_id": "task-1234567890",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "endpoint": "/v1/messages",
  "status": "success|failed",
  "duration_ms": 1234,
  "input_tokens": 100,
  "output_tokens": 200,
  "cost_usd": 0.001,
  "error_type": "rate_limit|auth_error|timeout|null",
  "error_message": "错误信息或null"
}
```

### 3. Execution Event（执行事件）
```json
{
  "timestamp": "2026-02-26T05:30:00.000Z",
  "event_type": "execution",
  "trace_id": "task-1234567890",
  "execution_type": "code|command|playbook",
  "status": "success|failed",
  "duration_ms": 1234,
  "exit_code": 0,
  "stdout": "输出内容（截断到1000字符）",
  "stderr": "错误输出（截断到1000字符）",
  "error_type": "timeout|dependency_missing|runtime_error|null"
}
```

### 4. Incident Event（故障事件）
```json
{
  "timestamp": "2026-02-26T05:30:00.000Z",
  "event_type": "incident",
  "trace_id": "incident-1234567890",
  "severity": "critical|high|medium|low",
  "incident_type": "timeout|api_error|resource_exhaustion|circuit_breaker",
  "affected_component": "coder-agent|api|database",
  "status": "detected|investigating|resolved",
  "resolution": "retry|fallback|manual|null",
  "duration_ms": 1234,
  "metadata": {
    "playbook_executed": "auto_retry",
    "retry_count": 3,
    "fallback_model": "claude-haiku-4-5"
  }
}
```

### 5. Cost Event（成本事件）
```json
{
  "timestamp": "2026-02-26T05:30:00.000Z",
  "event_type": "cost",
  "trace_id": "task-1234567890",
  "cost_type": "api|compute|storage",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "cost_usd": 0.001,
  "budget_daily": 1.0,
  "budget_used": 0.5,
  "budget_remaining": 0.5,
  "alert_triggered": false
}
```

## 存储格式

### events.jsonl（追加写入）
每行一个 JSON 事件，按时间顺序追加

### 索引文件（可选）
- events_by_date/2026-02-26.jsonl
- events_by_type/task.jsonl
- events_by_trace/task-1234567890.jsonl

## 查询示例

```python
# 查询今天的所有失败任务
events = load_events(date="2026-02-26", event_type="task", status="failed")

# 查询某个 trace 的所有事件
events = load_events(trace_id="task-1234567890")

# 统计今天的成本
total_cost = sum(e["cost_usd"] for e in load_events(date="2026-02-26", event_type="cost"))
```

## 保留策略

- 原始事件：保留 30 天
- 聚合统计：永久保留
- 错误事件：保留 90 天
