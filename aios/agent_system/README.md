# 自主 Agent 管理系统 (AIOS Agent System)

## 架构概览

```
用户请求
    ↓
任务路由引擎 (task_router.py)
    ↓
Agent 管理器 (agent_manager.py)
    ↓
Agent 模板库 (templates/)
    ↓
AIOS 协作层 (collaboration/)
    ↓
执行 & 监控
```

## 核心模块

### 1. Agent 模板库 (`templates/`)
- `coder.json` - 代码开发专员
- `analyst.json` - 数据分析专员
- `monitor.json` - 系统监控专员
- `researcher.json` - 信息研究专员

### 2. Agent 管理器 (`agent_manager.py`)
- `create_agent(template, task)` - 根据模板创建 Agent
- `list_agents()` - 列出所有活跃 Agent
- `get_agent_status(agent_id)` - 查询 Agent 状态
- `archive_agent(agent_id)` - 归档闲置 Agent
- `optimize_agent(agent_id)` - 根据表现优化配置

### 3. 任务路由引擎 (`task_router.py`)
- `analyze_task(message)` - 分析任务类型和复杂度
- `match_agent(task_type)` - 匹配合适的 Agent
- `should_create_new(task)` - 判断是否需要新建 Agent
- `route_task(task, agent_id)` - 分配任务

### 4. 协作编排器 (`orchestrator.py`)
- `decompose_task(complex_task)` - 拆解复杂任务
- `parallel_execute(subtasks)` - 并行执行
- `aggregate_results(results)` - 结果聚合
- `cross_validate(results)` - 交叉验证

## 数据结构

### Agent 配置
```json
{
  "id": "coder-001",
  "template": "coder",
  "created_at": "2026-02-22T13:16:00Z",
  "status": "active",
  "workspace": "~/.openclaw/agents/coder-001",
  "skills": ["coding-agent", "github"],
  "tools": {
    "allow": ["exec", "read", "write", "edit"],
    "deny": ["message", "cron"]
  },
  "system_prompt": "你是代码开发专员...",
  "stats": {
    "tasks_completed": 0,
    "success_rate": 0.0,
    "avg_duration_sec": 0
  }
}
```

### 任务分类规则
```json
{
  "code": {
    "keywords": ["写代码", "调试", "重构", "bug", "实现"],
    "agent_template": "coder",
    "model": "claude-opus-4-6"
  },
  "analysis": {
    "keywords": ["分析", "统计", "数据", "趋势"],
    "agent_template": "analyst",
    "model": "claude-sonnet-4-5"
  },
  "monitor": {
    "keywords": ["监控", "检查", "状态", "健康"],
    "agent_template": "monitor",
    "model": "claude-sonnet-4-5"
  },
  "research": {
    "keywords": ["搜索", "查找", "研究", "资料"],
    "agent_template": "researcher",
    "model": "claude-sonnet-4-5"
  }
}
```

## 实现计划

### Phase 1: 基础设施 (30min)
- [x] 创建目录结构
- [ ] Agent 模板定义
- [ ] Agent 管理器核心功能
- [ ] 数据持久化（agents.jsonl）

### Phase 2: 任务路由 (30min)
- [ ] 任务分类规则
- [ ] 关键词匹配引擎
- [ ] Agent 选择逻辑
- [ ] 自动创建决策

### Phase 3: 协作编排 (45min)
- [ ] 任务拆解算法
- [ ] 并行执行框架
- [ ] 结果聚合逻辑
- [ ] 失败重试机制

### Phase 4: 监控优化 (30min)
- [ ] Agent 性能追踪
- [ ] 自动优化建议
- [ ] 闲置检测清理
- [ ] Dashboard 可视化

### Phase 5: 集成测试 (15min)
- [ ] 端到端测试
- [ ] 边界情况处理
- [ ] 文档完善

## 使用示例

```python
# 用户发送："帮我写一个 Python 爬虫"
# 1. 任务路由识别为 "code" 类型
# 2. 匹配或创建 coder Agent
# 3. 分配任务给 coder-001
# 4. 监控执行，记录结果
# 5. 返回给用户

from aios.agent_system import AgentSystem

system = AgentSystem()
result = system.handle_task("帮我写一个 Python 爬虫")
```

## 配置文件

位置：`aios/agent_system/config.json`

```json
{
  "auto_create": true,
  "max_agents": 10,
  "idle_timeout_hours": 24,
  "archive_after_days": 7,
  "default_model": "claude-sonnet-4-5",
  "complex_task_model": "claude-opus-4-6"
}
```
