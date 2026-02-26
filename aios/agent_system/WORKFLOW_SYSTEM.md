# Agent 工作流系统

## 概述

为每个 Agent 类型设计了标准工作流，确保任务执行的规范性和可追踪性。

## 已实现工作流

### 1. Coder Workflow（代码开发）
**文件：** `workflows/coder_workflow.json`

**5 个阶段：**
1. **理解需求** - 读取任务、识别需求、列出约束
2. **设计方案** - 设计数据结构、函数签名、错误处理
3. **编写代码** - 实现逻辑、添加注解、文档字符串
4. **测试验证** - 编写测试、运行用例、检查边界
5. **代码审查** - 检查风格、性能、安全

**质量门控：**
- 测试覆盖率 ≥ 80%
- 复杂度 ≤ 10
- 无安全问题

**回滚：** 启用（失败自动回滚）

### 2. Analyst Workflow（数据分析）
**文件：** `workflows/analyst_workflow.json`

**5 个阶段：**
1. **数据收集** - 读取数据源、验证完整性
2. **数据清洗** - 去重、处理缺失值、标准化
3. **数据分析** - 计算指标、识别趋势、发现异常
4. **洞察提取** - 总结发现、识别根因、生成建议
5. **可视化** - 生成图表、创建仪表盘、导出报告

**质量门控：**
- 最少数据点 ≥ 10
- 置信度 ≥ 95%
- 无数据泄漏

**回滚：** 禁用（分析失败不回滚）

### 3. Monitor Workflow（系统监控）
**文件：** `workflows/monitor_workflow.json`

**5 个阶段：**
1. **观察系统** - 读取指标、事件日志、错误日志
2. **异常检测** - 对比基线、识别模式、计算评分
3. **诊断根因** - 分析堆栈、追踪事件链、评估影响
4. **告警通知** - 评估级别、生成消息、发送通知
5. **修复建议** - 匹配 Playbook、生成方案、提交请求

**质量门控：**
- 误报率 ≤ 10%
- 告警延迟 ≤ 60秒
- 不漏报 critical 问题

**回滚：** 禁用（监控失败不回滚）

## 工作流引擎

**文件：** `workflow_engine.py`

**核心功能：**
1. **加载工作流定义** - 从 JSON 文件加载
2. **启动执行** - 创建执行记录，发布事件
3. **阶段执行** - 追踪进度，记录输出
4. **失败处理** - 回滚或标记失败
5. **状态查询** - 查看执行状态和历史

**事件发布：**
- `workflow.started` - 工作流启动
- `workflow.stage_completed` - 阶段完成
- `workflow.stage_failed` - 阶段失败
- `workflow.completed` - 工作流完成
- `workflow.rolled_back` - 工作流回滚

## 集成到 Auto Dispatcher

**修改文件：** `auto_dispatcher.py`

**集成点：**
1. **初始化** - 加载 WorkflowEngine
2. **任务分发** - 启动对应工作流
3. **消息增强** - 注入工作流指引到 Agent prompt

**增强的 Prompt 结构：**
```
# Your Role
**Role:** Senior Python Developer
**Goal:** Write clean, maintainable code
**Backstory:** 10+ years experience

# Your Workflow
**Execution ID:** coder-dispatcher-20260226033037
**Workflow:** 标准代码开发工作流

**Stages:**
1. **理解需求** (1_understand)
   - Actions: 读取任务描述, 识别关键需求, 列出技术约束
   - Output: 需求清单
2. **设计方案** (2_design)
   ...

**Quality Gates:**
- test_coverage: 0.8
- max_complexity: 10
- no_security_issues: True

# Your Task
实现一个简单的缓存装饰器
```

## 测试

**文件：** `test_workflow_integration.py`

**测试内容：**
1. 工作流引擎加载
2. 工作流定义读取
3. 执行启动
4. 阶段执行
5. 状态查询

**测试结果：** ✅ 全部通过

## 下一步

1. **Agent 实际执行** - 让 Agent 按工作流阶段报告进度
2. **Dashboard 集成** - 在 Dashboard 显示工作流执行状态
3. **质量门控验证** - 自动检查质量门控是否满足
4. **工作流模板扩展** - 增加更多 Agent 类型的工作流
5. **工作流编排** - 支持多 Agent 协作工作流（如 Coder → Reviewer → Tester）

## 文件清单

```
aios/agent_system/
├── workflows/
│   ├── coder_workflow.json      # 代码开发工作流
│   ├── analyst_workflow.json    # 数据分析工作流
│   └── monitor_workflow.json    # 系统监控工作流
├── workflow_engine.py           # 工作流引擎
├── auto_dispatcher.py           # 任务分发器（已集成）
└── test_workflow_integration.py # 集成测试
```

## 使用示例

```python
from workflow_engine import WorkflowEngine

# 初始化引擎
engine = WorkflowEngine()

# 启动工作流
execution_id = engine.start_execution(
    agent_id="coder-dispatcher",
    agent_type="coder",
    task={"description": "实现缓存装饰器"}
)

# 执行阶段
result = engine.execute_stage(execution_id, {
    "requirements": ["支持 TTL", "支持 LRU", "线程安全"]
})

# 查看状态
status = engine.get_execution_status(execution_id)
print(f"状态: {status['status']}")
print(f"进度: {status['current_stage']}/{len(workflow['stages'])}")
```

---

**创建时间：** 2026-02-26 03:30  
**状态：** ✅ 已完成并测试通过
