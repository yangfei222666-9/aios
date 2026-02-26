# Phase 2: Agent Team Orchestration - 架构设计

## 核心目标
从"单个 Agent 独立执行"升级到"多 Agent 协同工作"

## 三大核心组件

### 1. Router Agent（路由总管）
**职责：** 理解用户意图，生成执行计划

**输入：** 自然语言指令
**输出：** 执行计划（JSON）

**示例：**
```python
用户输入："检查系统状态并生成报告"

Router 输出：
{
  "intent": "health_check_and_report",
  "steps": [
    {
      "agent": "aios_health_check",
      "action": "execute",
      "params": {},
      "output_key": "health_data"
    },
    {
      "agent": "document_agent",
      "action": "generate_report",
      "params": {
        "input": "{{health_data}}",
        "format": "markdown"
      },
      "output_key": "report"
    }
  ]
}
```

**核心能力：**
- 意图识别（基于 agents.json 的能力描述）
- 任务拆解（单任务 → 多步骤）
- 依赖分析（Step 2 依赖 Step 1 的输出）

---

### 2. Workflow Engine（工作流引擎）
**职责：** 执行计划，管理数据流

**核心功能：**
- 顺序执行（Step 1 → Step 2 → Step 3）
- 数据传递（Step 1 的输出 → Step 2 的输入）
- 错误处理（某步失败 → 触发 Self-Correction）
- 超时控制（单步最长 60s）

**执行流程：**
```python
context = {}  # 共享上下文

for step in plan.steps:
    # 1. 解析参数（替换 {{变量}}）
    params = resolve_params(step.params, context)
    
    # 2. 调用 Agent
    result = execute_agent(step.agent, params)
    
    # 3. 保存输出
    context[step.output_key] = result
    
    # 4. 错误处理
    if result.failed:
        trigger_self_correction(step, result.error)
```

---

### 3. Self-Correction Loop（自我修正）
**职责：** 失败时自动修复

**触发条件：**
- Agent 执行失败（exit_code != 0）
- 超时（>60s）
- 输出格式错误

**修复策略：**
1. **参数调整** - 路径错误 → 修正路径
2. **重试** - 网络超时 → 重试 3 次
3. **降级** - 复杂任务 → 拆分为简单任务
4. **求助** - 无法自动修复 → 通知用户

**示例：**
```python
# 原始任务失败
Step 1: aios_health_check
Error: FileNotFoundError: metrics.json

# Self-Correction
分析错误 → 文件不存在
生成修复计划 → 先创建 metrics.json
重试 → 成功
```

---

## 统一入口：TeamOrchestration

**API 设计：**
```python
from aios.agent_system.team_orchestration import TeamOrchestration

# 初始化
team = TeamOrchestration(agents_json_path="agents.json")

# 执行任务
result = team.execute(
    user_input="检查系统状态并生成报告",
    max_retries=3,
    timeout=180
)

# 输出
{
  "success": True,
  "steps_executed": 2,
  "final_output": "# 系统健康报告\n\nCPU: 45%\n...",
  "execution_time": 5.2,
  "errors": []
}
```

---

## 文件结构

```
aios/agent_system/
├── orchestrator.py              # 现有（保留）
├── router_agent.py              # 新增：路由总管
├── workflow_engine.py           # 新增：工作流引擎
├── self_correction.py           # 新增：自我修正
├── team_orchestration.py        # 新增：统一入口
├── agents.json                  # 现有（Agent 配置）
└── tests/
    ├── test_router.py
    ├── test_workflow.py
    ├── test_self_correction.py
    └── test_team_orchestration.py
```

---

## 实现计划

### 今天（2026-02-26）
1. ✅ 架构设计（30 分钟）
2. ⏳ 实现 Router Agent（1 小时）
3. ⏳ 实现 Workflow Engine（1 小时）
4. ⏳ 测试"检查系统状态并生成报告"（30 分钟）

### 明天（2026-02-27）
1. ⏳ 实现 Self-Correction Loop
2. ⏳ 集成到 AIOS Heartbeat
3. ⏳ 写文档 + 测试用例

---

## 核心优势

1. **完整闭环** - 路由 → 执行 → 修正 → 重试
2. **数据流管理** - Agent 之间无缝传递数据
3. **自动修复** - 失败时自动尝试修复
4. **扩展性强** - 新增 Agent 只需更新 agents.json
5. **用户友好** - 自然语言输入，自动拆解任务

---

## 测试场景

### 场景 1：简单任务（单 Agent）
```
用户："检查系统健康"
Router → 识别为 aios_health_check
Workflow → 直接执行
输出：健康数据
```

### 场景 2：复杂任务（多 Agent）
```
用户："检查系统状态并生成报告"
Router → 拆解为 2 步
  Step 1: aios_health_check
  Step 2: document_agent
Workflow → 顺序执行，数据传递
输出：Markdown 报告
```

### 场景 3：失败修复
```
用户："分析文档 /path/to/doc.pdf"
Router → document_agent
Workflow → 执行失败（文件不存在）
Self-Correction → 检查路径，提示用户
输出：错误信息 + 修复建议
```

---

## 下一步

立即开始实现 `router_agent.py`！
