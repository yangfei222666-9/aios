# AgentSystem 使用文档

## 概述

`AgentSystem` 是 AIOS 的自主 Agent 管理系统，提供智能任务路由、Agent 生命周期管理和自动进化能力。它整合了 `AgentManager`（Agent 管理）、`UnifiedRouter`（智能路由）和 `AgentEvolution`（进化系统）三大核心组件。

### 主要功能

- **智能任务路由**：根据任务类型、复杂度、风险等级自动选择最合适的 Agent 模板
- **自动 Agent 管理**：按需创建、复用、归档 Agent，避免资源浪费
- **任务执行追踪**：记录任务结果、统计成功率、分析失败原因
- **自动进化**：基于历史数据生成改进建议，持续优化 Agent 性能
- **系统状态监控**：实时监控错误率、性能指标，动态调整路由策略

---

## 初始化参数

```python
AgentSystem(data_dir: str = None, config_dir: str = None)
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data_dir` | `str` | `None` | 数据存储目录（Agent 配置、日志、统计数据）。默认为 `aios/data` |
| `config_dir` | `str` | `None` | 配置文件目录（暂未使用，预留扩展） |

### 初始化示例

```python
from aios.agent_system import AgentSystem

# 使用默认目录
system = AgentSystem()

# 自定义数据目录
system = AgentSystem(data_dir="./my_agents_data")
```

---

## 核心方法

### 1. `handle_task()` - 处理任务（主入口）

智能路由任务到合适的 Agent，自动创建或复用现有 Agent。

```python
def handle_task(
    self,
    message: str,
    auto_create: bool = True,
    task_type: TaskType = None,
    complexity: int = 5,
    risk_level: RiskLevel = RiskLevel.MEDIUM
) -> Dict
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `message` | `str` | 必填 | 任务描述（用于推断任务类型） |
| `auto_create` | `bool` | `True` | 如果没有合适的 Agent，是否自动创建 |
| `task_type` | `TaskType` | `None` | 任务类型（可选，不指定则自动推断） |
| `complexity` | `int` | `5` | 复杂度 1-10（影响模型选择和超时时间） |
| `risk_level` | `RiskLevel` | `MEDIUM` | 风险等级（`LOW`/`MEDIUM`/`HIGH`） |

#### 返回值

```python
{
    'status': 'success' | 'error',
    'action': 'assigned' | 'created' | 'failed',
    'agent_id': str,           # Agent ID
    'agent_name': str,         # Agent 名称
    'agent_template': str,     # Agent 模板类型
    'decision': {              # 路由决策详情
        'agent': str,          # 选择的 Agent 模板
        'model': str,          # 推荐的模型
        'thinking': bool,      # 是否启用深度思考
        'timeout': int,        # 超时时间（秒）
        'reason': str,         # 决策原因（向后兼容）
        'reason_codes': List[str],  # 决策原因代码列表
        'confidence': float,   # 置信度 0-1
        'execution_mode': str, # 执行模式
        'input_snapshot': Dict # 输入快照
    },
    'message': str             # 人类可读的结果描述
}
```

#### 使用示例

```python
# 基础用法（自动推断任务类型）
result = system.handle_task("修复登录页面的 bug")
print(f"分配给: {result['agent_name']} ({result['agent_id']})")

# 指定任务类型和复杂度
from aios.agent_system import TaskType, RiskLevel

result = system.handle_task(
    message="重构支付模块",
    task_type=TaskType.REFACTOR,
    complexity=8,
    risk_level=RiskLevel.HIGH
)

# 仅路由不创建（测试路由决策）
result = system.handle_task(
    message="分析用户行为数据",
    auto_create=False
)
if result['status'] == 'error':
    print("没有合适的 Agent，需要手动创建")
```

---

### 2. `report_task_result()` - 报告任务结果

记录任务执行结果，更新 Agent 统计数据，触发自动进化分析。

```python
def report_task_result(
    self,
    agent_id: str,
    success: bool,
    duration_sec: float,
    task_type: str = None,
    error_msg: str = None,
    context: Dict = None
)
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `agent_id` | `str` | 必填 | Agent ID |
| `success` | `bool` | 必填 | 任务是否成功 |
| `duration_sec` | `float` | 必填 | 任务耗时（秒） |
| `task_type` | `str` | `None` | 任务类型（`code`/`analysis`/`monitor`/`research`） |
| `error_msg` | `str` | `None` | 错误信息（失败时提供） |
| `context` | `Dict` | `None` | 额外上下文（如文件路径、工具调用等） |

#### 使用示例

```python
# 成功案例
system.report_task_result(
    agent_id="agent-123",
    success=True,
    duration_sec=45.2,
    task_type="code"
)

# 失败案例（会触发失败分析）
system.report_task_result(
    agent_id="agent-123",
    success=False,
    duration_sec=120.5,
    task_type="code",
    error_msg="Timeout: 编译超时",
    context={"file": "src/main.py", "line": 42}
)
```

**注意**：如果 Agent 失败率超过 30%，系统会自动生成改进建议。

---

### 3. `get_status()` - 获取系统状态

查看系统整体状态和活跃 Agent 分布。

```python
def get_status(self) -> Dict
```

#### 返回值

```python
{
    'summary': {
        'total_agents': int,
        'active_agents': int,
        'archived_agents': int
    },
    'active_agents_by_template': {
        'code-specialist': [
            {
                'id': 'agent-123',
                'name': 'CodeAgent-001',
                'tasks_completed': 15,
                'success_rate': 0.93,
                'last_active': '2024-01-15T10:30:00'
            }
        ],
        'data-analyst': [...]
    },
    'total_active': int
}
```

#### 使用示例

```python
status = system.get_status()
print(f"活跃 Agent: {status['total_active']}")

for template, agents in status['active_agents_by_template'].items():
    print(f"\n{template}:")
    for agent in agents:
        print(f"  - {agent['name']}: {agent['success_rate']:.1%} 成功率")
```

---

### 4. `list_agents()` - 列出 Agent

查询符合条件的 Agent 列表。

```python
def list_agents(
    self,
    template: str = None,
    status: str = "active"
) -> List[Dict]
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `template` | `str` | `None` | 过滤模板类型（如 `code-specialist`） |
| `status` | `str` | `"active"` | 过滤状态（`active`/`archived`） |

#### 使用示例

```python
# 列出所有活跃 Agent
agents = system.list_agents()

# 列出特定模板的 Agent
code_agents = system.list_agents(template="code-specialist")

# 列出已归档的 Agent
archived = system.list_agents(status="archived")
```

---

### 5. `get_agent_detail()` - 获取 Agent 详情

查看单个 Agent 的完整信息。

```python
def get_agent_detail(self, agent_id: str) -> Optional[Dict]
```

#### 使用示例

```python
agent = system.get_agent_detail("agent-123")
if agent:
    print(f"名称: {agent['name']}")
    print(f"模板: {agent['template']}")
    print(f"成功率: {agent['stats']['success_rate']:.1%}")
    print(f"完成任务: {agent['stats']['tasks_completed']}")
```

---

### 6. `cleanup_idle_agents()` - 清理闲置 Agent

归档长时间未使用的 Agent，释放资源。

```python
def cleanup_idle_agents(self, idle_hours: int = 24) -> List[str]
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `idle_hours` | `int` | `24` | 闲置时长阈值（小时） |

#### 返回值

归档的 Agent ID 列表。

#### 使用示例

```python
# 归档 24 小时未活跃的 Agent
archived = system.cleanup_idle_agents(idle_hours=24)
print(f"已归档 {len(archived)} 个 Agent")

# 更激进的清理（12 小时）
archived = system.cleanup_idle_agents(idle_hours=12)
```

---

## 完整使用示例

### 示例 1：基础任务处理流程

```python
from aios.agent_system import AgentSystem
import time

# 初始化系统
system = AgentSystem()

# 1. 处理任务
result = system.handle_task("优化数据库查询性能")

if result['status'] == 'success':
    agent_id = result['agent_id']
    print(f"✓ {result['message']}")
    print(f"  模型: {result['decision']['model']}")
    print(f"  超时: {result['decision']['timeout']}s")
    
    # 2. 模拟任务执行
    start = time.time()
    # ... 实际任务执行逻辑 ...
    duration = time.time() - start
    
    # 3. 报告结果
    system.report_task_result(
        agent_id=agent_id,
        success=True,
        duration_sec=duration,
        task_type="optimize"
    )
else:
    print(f"✗ 任务失败: {result['message']}")
```

### 示例 2：批量任务处理

```python
tasks = [
    ("修复登录 bug", TaskType.DEBUG, 3),
    ("重构支付模块", TaskType.REFACTOR, 8),
    ("分析用户留存", TaskType.ANALYZE, 5),
]

for message, task_type, complexity in tasks:
    result = system.handle_task(
        message=message,
        task_type=task_type,
        complexity=complexity
    )
    
    print(f"{message} -> {result['agent_name']}")
```

### 示例 3：监控和维护

```python
import schedule
import time

def daily_maintenance():
    # 查看系统状态
    status = system.get_status()
    print(f"活跃 Agent: {status['total_active']}")
    
    # 清理闲置 Agent
    archived = system.cleanup_idle_agents(idle_hours=48)
    print(f"归档 {len(archived)} 个闲置 Agent")

# 每天凌晨 2 点执行
schedule.every().day.at("02:00").do(daily_maintenance)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

### 示例 4：高级路由控制

```python
from aios.agent_system import TaskType, RiskLevel

# 高风险任务（使用更强模型 + 深度思考）
result = system.handle_task(
    message="重构核心支付逻辑",
    task_type=TaskType.REFACTOR,
    complexity=9,
    risk_level=RiskLevel.HIGH
)

print(f"模型: {result['decision']['model']}")
print(f"深度思考: {result['decision']['thinking']}")
print(f"超时: {result['decision']['timeout']}s")
print(f"决策原因: {', '.join(result['decision']['reason_codes'])}")
```

---

## 注意事项

### 1. 数据持久化

- 所有 Agent 配置和统计数据存储在 `data_dir`（默认 `aios/data`）
- 系统日志写入 `data_dir/system.log`
- 进化数据存储在 `data_dir/evolution/`
- **重要**：定期备份 `data_dir` 以防数据丢失

### 2. 任务类型推断

`handle_task()` 会根据消息关键词自动推断任务类型：

| 关键词 | 任务类型 |
|--------|----------|
| 重构、refactor | `REFACTOR` |
| 调试、修复、bug、debug、fix | `DEBUG` |
| 测试、test | `TEST` |
| 优化、性能、optimize | `OPTIMIZE` |
| 监控、检查、monitor | `MONITOR` |
| 部署、发布、deploy | `DEPLOY` |
| 分析、统计、analyze | `ANALYZE` |
| 搜索、调研、research | `RESEARCH` |
| 审查、review | `REVIEW` |
| 文档、doc | `DOCUMENT` |
| 其他 | `CODING`（默认） |

**建议**：对于关键任务，显式指定 `task_type` 以确保准确路由。

### 3. Agent 复用策略

- 系统优先复用同模板的活跃 Agent（按最近活跃时间排序）
- 如果没有合适的 Agent 且 `auto_create=True`，会自动创建新 Agent
- 新创建的 Agent 会在返回结果中标记 `action='created'`

### 4. 失败处理和自动进化

- 当 Agent 失败率超过 30% 时，系统自动生成改进建议
- 建议存储在 `data_dir/evolution/suggestions/`
- 需要人工审查建议并应用到 Agent 配置

### 5. 性能优化

- 定期调用 `cleanup_idle_agents()` 清理闲置 Agent
- 监控 `system.log` 中的错误和警告
- 使用 `get_status()` 检查 Agent 分布，避免某类 Agent 过多

### 6. 系统状态监控

系统会自动监控以下指标（从 `aios/data/events.jsonl` 读取）：

- **错误率**：最近 100 个事件中的错误比例
- **性能下降**：工具调用平均耗时（基线 500ms）
- **CPU/内存使用率**：需要配合 `system-resource-monitor` 使用

这些指标会影响路由决策（如错误率高时降级到更稳定的模型）。

### 7. 线程安全

当前实现**不是线程安全的**。如果需要并发处理任务，建议：

- 使用进程池而非线程池
- 或为每个线程创建独立的 `AgentSystem` 实例

### 8. CLI 工具

系统提供命令行接口用于调试和管理：

```bash
# 查看系统状态
python -m aios.agent_system status

# 列出所有 Agent
python -m aios.agent_system list

# 列出特定模板的 Agent
python -m aios.agent_system list code-specialist

# 测试任务路由（不创建 Agent）
python -m aios.agent_system route "修复登录 bug"

# 清理闲置 Agent
python -m aios.agent_system cleanup 48
```

---

## 常见问题

### Q: 如何选择合适的 `complexity` 值？

**A**: 参考以下指南：

- **1-3**：简单任务（修改配置、查询数据）
- **4-6**：中等任务（修复 bug、编写单元测试）
- **7-8**：复杂任务（重构模块、性能优化）
- **9-10**：极复杂任务（架构设计、大规模重构）

复杂度会影响模型选择和超时时间。

### Q: 什么时候应该设置 `risk_level=HIGH`？

**A**: 以下情况建议使用高风险等级：

- 修改核心业务逻辑
- 涉及支付、安全、隐私的代码
- 数据库迁移或结构变更
- 生产环境部署

高风险任务会使用更强的模型和更长的超时时间。

### Q: 如何查看 Agent 的失败原因？

**A**: 查看进化系统的失败分析：

```python
from aios.agent_system.evolution import AgentEvolution

evolution = AgentEvolution()
analysis = evolution.analyze_failures("agent-123", lookback_hours=24)

print(f"失败率: {analysis['failure_rate']:.1%}")
print(f"常见错误: {analysis['common_errors']}")
print(f"改进建议: {analysis['suggestions']}")
```

### Q: 系统会自动删除 Agent 吗？

**A**: 不会。`cleanup_idle_agents()` 只会**归档** Agent（状态改为 `archived`），不会删除数据。归档的 Agent 可以随时恢复。

---

## 相关文档

- [AgentManager API](./core/agent_manager.py) - Agent 生命周期管理
- [UnifiedRouter](./unified_router_v1.py) - 智能路由算法
- [AgentEvolution](./evolution.py) - 自动进化系统
- [TaskType 枚举](./unified_router_v1.py#L15) - 支持的任务类型

---

**版本**: 1.0  
**最后更新**: 2024-01-15
