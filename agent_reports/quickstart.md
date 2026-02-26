# AIOS Agent System 快速入门

## 什么是 AIOS Agent System

AIOS Agent System 是一个自主 Agent 管理系统，能够根据任务类型自动创建、分配和管理专业化的 AI Agent。系统通过智能路由引擎分析用户请求，匹配或创建合适的 Agent 来处理任务，实现高效的任务自动化。

### 核心概念

**Agent 模板**  
预定义的 Agent 配置，包含专业领域、技能、工具权限和系统提示词。系统内置 4 种模板：
- `coder` - 代码开发专员
- `analyst` - 数据分析专员
- `monitor` - 系统监控专员
- `researcher` - 信息研究专员

**任务路由**  
根据关键词和上下文自动识别任务类型，匹配最合适的 Agent 模板。如果没有可用的 Agent，系统会自动创建新的。

**Agent 生命周期**  
Agent 从创建到归档的完整流程：
1. **创建** - 根据模板初始化配置和工作空间
2. **活跃** - 处理分配的任务，记录性能统计
3. **闲置** - 超过设定时间未使用
4. **归档** - 自动清理闲置 Agent，释放资源

**性能追踪**  
每个 Agent 记录任务完成数、成功率、平均耗时等指标，用于优化和负载均衡。

---

## 如何创建 Agent

### CLI 命令

```bash
# 查看系统状态
python -m aios.agent_system status

# 列出所有活跃 Agent
python -m aios.agent_system list

# 列出特定类型的 Agent
python -m aios.agent_system list coder

# 手动创建 Agent
python -m aios.agent_system create coder

# 清理闲置 Agent（默认 24 小时未使用）
python -m aios.agent_system cleanup
python -m aios.agent_system cleanup 48
```

### Python API

```python
from aios.agent_system import AgentSystem

# 初始化系统
system = AgentSystem()

# 自动创建或分配 Agent 处理任务
result = system.handle_task("帮我写一个 Python 爬虫", auto_create=True)

# 返回结果示例
# {
#   'status': 'success',
#   'action': 'created',  # 或 'assigned'（复用现有 Agent）
#   'agent_id': 'coder-001',
#   'agent_name': '代码开发专员',
#   'task_analysis': {
#     'type': 'code',
#     'complexity': 'medium',
#     'keywords': ['写', '爬虫', 'Python']
#   },
#   'message': '已创建新 Agent: 代码开发专员 (coder-001)'
# }

# 获取 Agent 详情
agent = system.get_agent_detail('coder-001')
print(agent['template'])  # 'coder'
print(agent['status'])    # 'active'
print(agent['stats'])     # 性能统计
```

### Agent 模板说明

| 模板 | 触发关键词 | 模型 | 适用场景 |
|------|-----------|------|---------|
| **coder** | 写代码、实现、调试、bug、重构、函数、API、测试、爬虫 | claude-opus-4-6 | 编写代码、调试、重构、优化 |
| **analyst** | 分析、统计、数据、趋势、模式、报告、总结、对比 | claude-sonnet-4-5 | 数据分析、统计报告、趋势预测 |
| **monitor** | 监控、检查、状态、健康、性能、CPU、内存、进程 | claude-sonnet-4-5 | 系统健康检查、性能监控、异常告警 |
| **researcher** | 搜索、查找、研究、资料、信息、什么是、如何 | claude-sonnet-4-5 | 信息搜索、资料整理、知识总结 |

---

## 如何分配任务

### 自动路由（推荐）

系统会自动分析任务并选择最合适的 Agent：

```python
from aios.agent_system import AgentSystem

system = AgentSystem()

# 代码任务 → 自动创建或分配 coder Agent
result = system.handle_task("实现一个 REST API")
print(result['agent_id'])  # 'coder-001'

# 分析任务 → 自动创建或分配 analyst Agent
result = system.handle_task("分析最近的用户数据")
print(result['agent_id'])  # 'analyst-001'

# 监控任务 → 自动创建或分配 monitor Agent
result = system.handle_task("检查服务器状态")
print(result['agent_id'])  # 'monitor-001'
```

**路由逻辑**：
1. 根据关键词匹配任务类型
2. 查找相同模板的活跃 Agent
3. 如果有多个可用 Agent，选择最近最少使用的（负载均衡）
4. 如果没有可用 Agent，自动创建新的

### 手动分配

如果需要精确控制，可以先创建 Agent 再手动分配：

```bash
# 测试任务路由（不自动创建）
python -m aios.agent_system route "帮我写一个 Python 爬虫"

# 输出：
# Task Type: code
# Matched Template: coder
# Recommended Action: create (no active coder agents found)
```

```python
# 手动创建特定类型的 Agent
system = AgentSystem()
agent_id = system.create_agent('coder')

# 然后在代码中手动分配任务给该 Agent
# （需要与 OpenClaw sessions_spawn 集成）
```

### 报告任务结果

完成任务后，报告结果以更新 Agent 性能统计：

```python
system.report_task_result(
    agent_id='coder-001',
    success=True,        # 任务是否成功
    duration_sec=45.2    # 任务耗时（秒）
)

# 查看更新后的统计
agent = system.get_agent_detail('coder-001')
print(agent['stats'])
# {
#   'tasks_completed': 5,
#   'success_rate': 0.8,
#   'avg_duration_sec': 52.3
# }
```

---

## 常见问题

### Agent 状态

**Q: 如何查看所有 Agent 的状态？**

```python
system = AgentSystem()
status = system.get_status()

print(status)
# {
#   'total_active': 3,
#   'total_archived': 1,
#   'active_agents_by_template': {
#     'coder': [
#       {
#         'id': 'coder-001',
#         'created_at': '2026-02-22T13:16:00Z',
#         'last_used': '2026-02-22T14:30:00Z',
#         'tasks_completed': 5
#       }
#     ],
#     'analyst': [...],
#     'monitor': [...]
#   }
# }
```

**Q: Agent 什么时候会被归档？**

默认情况下，超过 24 小时未使用的 Agent 会在下次清理时被归档。可以通过配置文件修改：

```json
// aios/agent_system/config.json
{
  "idle_timeout_hours": 24,
  "archive_after_days": 7
}
```

**Q: 如何手动清理闲置 Agent？**

```bash
# 清理 24 小时未使用的 Agent
python -m aios.agent_system cleanup

# 清理 48 小时未使用的 Agent
python -m aios.agent_system cleanup 48
```

```python
# Python API
system = AgentSystem()
archived = system.cleanup_idle_agents(idle_hours=24)
print(f"Archived {len(archived)} agents")
```

### 任务队列

**Q: 系统支持任务队列吗？**

当前版本（v1.0）不支持任务队列，每个任务立即分配给 Agent。未来版本将支持：
- 任务队列和优先级
- 并行执行多个任务
- 任务依赖和编排

**Q: 如何处理多个并发任务？**

目前需要为每个任务创建或分配独立的 Agent：

```python
system = AgentSystem()

# 任务 1 → coder-001
result1 = system.handle_task("写一个爬虫")

# 任务 2 → coder-002（如果 coder-001 忙碌）
result2 = system.handle_task("调试这段代码")

# 任务 3 → analyst-001（不同类型）
result3 = system.handle_task("分析数据")
```

### 错误处理

**Q: 如果任务路由失败怎么办？**

```python
result = system.handle_task("不明确的任务")

if result['status'] == 'error':
    print(result['error'])
    # 可能的错误：
    # - 'No matching template found'
    # - 'Failed to create agent'
    # - 'Max agents limit reached'
```

**Q: 如何限制 Agent 数量？**

在配置文件中设置最大 Agent 数量：

```json
// aios/agent_system/config.json
{
  "max_agents": 10,
  "auto_create": true
}
```

当达到上限时，系统会：
1. 优先复用现有 Agent
2. 如果无法复用，返回错误提示
3. 建议清理闲置 Agent

**Q: Agent 执行任务失败后会怎样？**

```python
# 报告失败
system.report_task_result(
    agent_id='coder-001',
    success=False,
    duration_sec=10.5
)

# 失败会影响 Agent 的成功率统计
agent = system.get_agent_detail('coder-001')
print(agent['stats']['success_rate'])  # 降低
```

系统不会自动重试失败的任务，需要手动处理或重新分配。

### 配置和自定义

**Q: 如何添加自定义 Agent 模板？**

编辑 `aios/agent_system/templates/templates.json`：

```json
{
  "my_custom_agent": {
    "name": "自定义专员",
    "description": "处理特定领域任务",
    "model": "claude-sonnet-4-5",
    "skills": ["custom-skill"],
    "tools": {
      "allow": ["read", "write", "exec"],
      "deny": ["message"]
    },
    "system_prompt": "你是自定义专员..."
  }
}
```

然后在 `aios/agent_system/config/task_rules.json` 添加路由规则：

```json
{
  "custom": {
    "keywords": ["自定义", "特殊"],
    "agent_template": "my_custom_agent",
    "model": "claude-sonnet-4-5"
  }
}
```

**Q: 数据存储在哪里？**

- Agent 配置：`~/.openclaw/workspace/aios/agent_system/data/agents.jsonl`
- 系统日志：`~/.openclaw/workspace/aios/agent_system/data/system.log`

每个 Agent 一行 JSON，方便追加和查询。

---

## 完整示例

### 场景：代码开发工作流

```python
from aios.agent_system import AgentSystem

system = AgentSystem()

# 第一次：创建 coder Agent
result = system.handle_task("写一个 Python 爬虫")
print(result['action'])  # 'created'
print(result['agent_id'])  # 'coder-001'

# 第二次：复用现有 coder Agent
result = system.handle_task("调试这段代码")
print(result['action'])  # 'assigned'
print(result['agent_id'])  # 'coder-001'（复用）

# 报告任务结果
system.report_task_result('coder-001', success=True, duration_sec=120)

# 查看 Agent 状态
agent = system.get_agent_detail('coder-001')
print(f"完成任务数: {agent['stats']['tasks_completed']}")
print(f"成功率: {agent['stats']['success_rate']}")
```

### 场景：多类型任务管理

```python
system = AgentSystem()

# 代码任务
system.handle_task("实现一个 REST API")

# 分析任务
system.handle_task("分析最近的用户数据")

# 监控任务
system.handle_task("检查服务器状态")

# 查看系统状态
status = system.get_status()
print(f"活跃 Agent 总数: {status['total_active']}")

for template, agents in status['active_agents_by_template'].items():
    print(f"{template}: {len(agents)} 个 Agent")

# 定期清理
archived = system.cleanup_idle_agents(idle_hours=24)
print(f"归档了 {len(archived)} 个闲置 Agent")
```

---

## 下一步

- 查看 [README.md](../aios/agent_system/README.md) 了解架构设计
- 查看 [USAGE.md](../aios/agent_system/USAGE.md) 了解更多 API 用法
- 自定义 Agent 模板和任务路由规则
- 集成到 OpenClaw 主会话或 HEARTBEAT 中

**提示**：系统设计为"即插即用"，大多数情况下只需调用 `handle_task()` 即可自动完成 Agent 创建和任务分配。
