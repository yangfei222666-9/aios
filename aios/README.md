# 太极OS (AIOS) - AI Operating System

**一个会自我学习、持续进化的 AI 操作系统**

太极OS 不是传统的任务执行器，而是一个能够从失败中学习、自动改进、持续进化的智能系统。它像生物一样，通过观察、反思、实验来提升自己的能力。

---

## 核心特性

### 🧠 自我学习
- **从失败中学习** - 每次失败都会被记录、分析、转化为可复用的经验
- **自动改进** - 系统会根据历史数据自动生成改进建议并应用
- **持续进化** - Evolution Score 追踪系统整体进化程度

### 🔄 任务队列
- **异步执行** - 任务提交后立即返回，后台自动执行
- **状态追踪** - 实时查看任务状态（pending/running/completed/failed）
- **失败重试** - 自动重试失败任务，智能调整参数

### 🤖 Agent 系统
- **多 Agent 协作** - 不同 Agent 负责不同类型的任务
- **动态调度** - 根据任务类型自动选择最合适的 Agent
- **健康监控** - 自动检测 Agent 状态，发现问题及时处理

### 📊 可观测性
- **实时监控** - Dashboard 实时显示系统状态
- **历史回溯** - 完整的事件日志，支持任意时间点回溯
- **性能分析** - 自动分析系统瓶颈，提供优化建议

### 🛡️ 可靠性
- **备份与恢复** - 一键备份，生产等价恢复验证
- **状态一致性** - 统一的状态词表，避免状态混乱
- **错误处理** - 完善的错误捕获和处理机制

---

## 快速开始

### 1. 环境要求

- Python 3.12+
- Windows 10/11 或 Linux
- 8GB+ RAM（推荐 16GB）

### 2. 安装依赖

```bash
cd aios/agent_system
pip install -r requirements.txt
```

### 3. 启动 Memory Server（可选但推荐）

Memory Server 保持 embedding 模型热加载，消除冷启动延迟：

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" memory_server.py
```

访问 http://127.0.0.1:7788/status 验证启动成功。

### 4. 启动 Dashboard

```powershell
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v4.0
& "C:\Program Files\Python312\python.exe" server.py
```

访问 http://127.0.0.1:8889 查看系统状态。

### 5. 提交第一个任务

```python
from task_queue import TaskQueue

queue = TaskQueue()
task_id = queue.add_task(
    task_type="research",
    description="搜索 GitHub 上的 AIOS 项目",
    priority=1
)
print(f"任务已提交: {task_id}")
```

---

## 核心概念

### 任务队列 (Task Queue)

任务队列是太极OS 的核心调度系统，负责：
- 接收任务提交
- 分配给合适的 Agent
- 追踪执行状态
- 处理失败重试

**任务状态流转：**
```
pending → running → completed
                 ↓
              failed → retrying → completed
```

### Agent 系统

Agent 是执行任务的实体，每个 Agent 有自己的专长：

- **GitHub_Researcher** - 搜索和分析 GitHub 项目
- **Architecture_Analyst** - 分析项目架构
- **Code_Reviewer** - 代码审查
- **Documentation_Writer** - 文档编写

### 自我改进循环 (Self-Improving Loop)

太极OS 的核心能力，包含三个阶段：

1. **观察 (Observe)** - 收集系统运行数据
2. **反思 (Reflect)** - 分析问题，生成改进建议
3. **实验 (Experiment)** - 应用改进，验证效果

### Evolution Score

系统进化程度的量化指标，范围 0-1：

- **0.0-0.3** - 初始阶段，基础功能
- **0.3-0.6** - 成长阶段，开始学习
- **0.6-0.8** - 成熟阶段，稳定运行
- **0.8-1.0** - 进化阶段，持续优化

---

## 使用场景

### 场景 1：GitHub 项目学习

```python
# 提交学习任务
queue.add_task(
    task_type="github_research",
    description="学习 DeerFlow 的架构设计",
    metadata={"repo": "deerflow/deerflow"}
)

# 系统会自动：
# 1. 搜索项目
# 2. 分析架构
# 3. 提取关键设计
# 4. 生成学习报告
# 5. 更新知识库
```

### 场景 2：代码审查

```python
# 提交审查任务
queue.add_task(
    task_type="code_review",
    description="审查 scheduler.py 的改动",
    metadata={"file": "scheduler.py"}
)

# 系统会自动：
# 1. 读取代码
# 2. 分析改动
# 3. 检查潜在问题
# 4. 生成审查报告
```

### 场景 3：系统维护

```python
# 提交维护任务
queue.add_task(
    task_type="maintenance",
    description="清理旧日志文件",
    metadata={"days": 7}
)

# 系统会自动：
# 1. 扫描日志目录
# 2. 识别过期文件
# 3. 安全删除
# 4. 生成清理报告
```

---

## 架构设计

### 核心模块

```
aios/
├── agent_system/          # Agent 系统核心
│   ├── agents.json        # Agent 配置
│   ├── task_queue.py      # 任务队列
│   ├── scheduler.py       # 调度器
│   ├── memory_server.py   # Memory Server
│   └── data/              # 数据存储
│       ├── events.db      # 事件数据库
│       ├── task_queue.jsonl
│       └── spawn_pending.jsonl
├── dashboard/             # 可视化界面
│   └── AIOS-Dashboard-v4.0/
├── core/                  # 核心工具
│   ├── app_alias.py       # 应用别名
│   └── state_vocab.py     # 状态词表
└── docs/                  # 文档
    └── TAIJIOS_PRINCIPLES.md
```

### 数据流

```
用户提交任务
    ↓
Task Queue 接收
    ↓
Scheduler 调度
    ↓
Agent 执行
    ↓
结果回写
    ↓
Learning Loop 学习
    ↓
系统进化
```

---

## 配置说明

### agents.json

定义所有 Agent 的配置：

```json
{
  "agents": [
    {
      "id": "GitHub_Researcher",
      "name": "GitHub 研究员",
      "description": "搜索和分析 GitHub 项目",
      "capabilities": ["search", "analyze"],
      "model": "claude-sonnet-4-6",
      "timeout": 120
    }
  ]
}
```

### task_queue.jsonl

任务队列数据格式：

```json
{
  "task_id": "task-123",
  "task_type": "research",
  "description": "搜索 AIOS 项目",
  "status": "pending",
  "priority": 1,
  "created_at": "2026-03-13T08:00:00Z"
}
```

---

## 监控与维护

### 健康检查

```python
from evaluator import Evaluator

evaluator = Evaluator()
health = evaluator.check_system_health()

print(f"Evolution Score: {health['evolution_score']}")
print(f"Active Agents: {health['active_agents']}")
print(f"Pending Tasks: {health['pending_tasks']}")
```

### 备份与恢复

```bash
# 备份
python backup.py

# 恢复
python restore.py --backup-id backup-20260313
```

### 日志查看

```bash
# 查看最近的事件
python cli.py events --limit 10

# 查看特定 Agent 的日志
python cli.py agent-logs --agent GitHub_Researcher

# 查看任务执行历史
python cli.py task-history --task-id task-123
```

---

## 性能优化

### 数据库优化

```sql
-- 启用 WAL 模式（已自动配置）
PRAGMA journal_mode=WAL;

-- 创建索引（已自动创建）
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
```

### Memory Server

使用 Memory Server 可以：
- 消除 embedding 模型冷启动延迟（9s → 0s）
- 减少内存占用（模型只加载一次）
- 提升检索速度（常驻内存）

---

## 故障排查

### 任务一直 pending

**可能原因：**
- Scheduler 未运行
- Agent 配置错误
- spawn_pending.jsonl 未处理

**解决方法：**
```bash
# 检查 Scheduler 状态
python cli.py scheduler-status

# 手动触发调度
python cli.py trigger-schedule

# 清空 spawn_pending
python cli.py clear-pending
```

### Agent 连续失败

**可能原因：**
- 任务超时
- 模型 API 错误
- 任务描述不清晰

**解决方法：**
```bash
# 查看失败日志
python cli.py agent-logs --agent <agent_id> --failed-only

# 调整超时时间
python cli.py update-agent --agent <agent_id> --timeout 180

# 重试任务
python cli.py retry-task --task-id <task_id>
```

### Evolution Score 不增长

**可能原因：**
- Learning Loop 未运行
- 没有新的学习数据
- 改进建议未应用

**解决方法：**
```bash
# 触发学习循环
python cli.py trigger-learning

# 查看待应用的改进
python cli.py list-improvements

# 手动应用改进
python cli.py apply-improvement --id <improvement_id>
```

---

## 开发指南

### 添加新 Agent

1. 在 `agents.json` 中添加配置
2. 实现 Agent 逻辑（继承 `BaseAgent`）
3. 注册到 Scheduler
4. 测试验证

### 添加新任务类型

1. 在 `task_queue.py` 中定义任务类型
2. 实现任务处理逻辑
3. 更新 Scheduler 路由规则
4. 添加测试用例

### 扩展 Learning Loop

1. 在 `learning_loop.py` 中添加新的学习规则
2. 定义改进建议格式
3. 实现应用逻辑
4. 验证效果

---

## 社区与支持

- **文档：** `docs/`
- **问题反馈：** 提交 Issue
- **讨论：** 加入 Discord/Telegram 群组

---

## 许可证

MIT License

---

## 致谢

太极OS 的设计灵感来自：
- DeerFlow - 工作流引擎
- Mem0 - 记忆系统
- Hive - Agent 协作
- MetaGPT - 多 Agent 框架

---

**版本：** v1.0  
**最后更新：** 2026-03-13  
**维护者：** 小九 + 珊瑚海
