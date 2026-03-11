# Self-Improving Loop

> 让 AI Agent 自动进化 - 完整的自我改进闭环，包含自动回滚、自适应阈值和实时通知

[![Tests](https://img.shields.io/badge/tests-17%2F17%20passing-brightgreen)](tests/)
[![Performance](https://img.shields.io/badge/overhead-%3C1%25-brightgreen)](docs/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🌟 核心特性

- 🔄 **完整的 7 步改进闭环** - 执行 → 记录 → 分析 → 生成 → 应用 → 验证 → 更新
- 🛡️ **自动回滚** - 效果变差自动回滚，保护生产环境
- 🧠 **自适应阈值** - 根据 Agent 特性动态调整触发条件
- 📱 **实时通知** - Telegram 推送改进和回滚事件
- ✅ **高测试覆盖** - 17/17 测试用例全部通过
- ⚡ **低性能开销** - <1% 性能影响

## 📖 目录

- [快速开始](#快速开始)
- [安装说明](#安装说明)
- [工作原理](#工作原理)
- [使用场景](#使用场景)
- [API 参考](#api-参考)
- [教程](#教程)
- [性能指标](#性能指标)
- [高级配置](#高级配置)
- [测试](#测试)
- [贡献](#贡献)

---

## 🚀 快速开始

### 基础使用

```python
from self_improving_loop import SelfImprovingLoop

# 创建实例
loop = SelfImprovingLoop()

# 包装任务执行
result = loop.execute_with_improvement(
    agent_id="my-agent",
    task="处理用户请求",
    execute_fn=lambda: agent.run_task(task)
)

# 检查结果
if result["improvement_triggered"]:
    print(f"应用了 {result['improvement_applied']} 项改进")

if result["rollback_executed"]:
    print(f"已回滚: {result['rollback_executed']['reason']}")
```

---

## 📦 安装说明

### 方法 1: 从源码安装

```bash
git clone https://github.com/yangfei222666-9/self-improving-loop.git
cd self-improving-loop
pip install -e .
```

### 方法 2: 使用 pip（如果已发布）

```bash
pip install self-improving-loop
```

### 依赖要求

- Python 3.8+
- 无外部依赖（纯 Python 实现）

### 验证安装

```bash
python -c "from self_improving_loop import SelfImprovingLoop; print('安装成功')"
```

---

## 📖 工作原理

### 完整闭环

```
执行任务 → 记录结果 → 分析失败模式 → 生成改进建议 
    ↓                                          ↑
更新配置 ← 验证效果 ← 自动应用 ← ─────────────┘
```

### 自动回滚

当检测到以下情况时自动回滚：
- 成功率下降 >10%
- 平均耗时增加 >20%
- 连续失败 ≥5 次

### 自适应阈值

根据 Agent 特性自动调整：

| Agent 类型 | 失败阈值 | 分析窗口 | 冷却期 |
|-----------|---------|---------|--------|
| 高频      | 5 次    | 48 小时 | 3 小时 |
| 中频      | 3 次    | 24 小时 | 6 小时 |
| 低频      | 2 次    | 72 小时 | 12 小时 |
| 关键      | 1 次    | 24 小时 | 6 小时 |

---

## 🎯 使用场景

### 1. AI Agent 系统
```python
class MyAgent:
    def __init__(self):
        self.loop = SelfImprovingLoop()
    
    def run_task(self, task):
        return self.loop.execute_with_improvement(
            agent_id=self.id,
            task=task,
            execute_fn=lambda: self._do_task(task)
        )
```

### 2. 微服务监控
```python
@with_self_improvement("api-service")
def handle_request(request):
    # 自动监控和改进
    return process_request(request)
```

### 3. 批量任务处理
```python
for task in task_queue:
    result = loop.execute_with_improvement(
        agent_id=f"worker-{task.type}",
        task=task.description,
        execute_fn=lambda: process_task(task)
    )
```

---

## 📚 API 参考

### SelfImprovingLoop

主引擎类，协调所有改进流程。

#### 初始化

```python
SelfImprovingLoop(
    data_dir: str = "./data",
    notifier: Optional[Notifier] = None,
    adaptive_threshold: Optional[AdaptiveThreshold] = None
)
```

**参数：**
- `data_dir`: 数据存储目录（默认 `./data`）
- `notifier`: 通知器实例（可选）
- `adaptive_threshold`: 自适应阈值实例（可选）

#### execute_with_improvement()

执行任务并自动改进。

```python
execute_with_improvement(
    agent_id: str,
    task: str,
    execute_fn: Callable,
    context: Optional[Dict] = None
) -> Dict
```

**参数：**
- `agent_id`: Agent 唯一标识符
- `task`: 任务描述
- `execute_fn`: 任务执行函数
- `context`: 任务上下文（可选）

**返回值：**
```python
{
    "success": bool,              # 是否成功
    "result": Any,                # 执行结果
    "error": Optional[str],       # 错误信息
    "duration_sec": float,        # 执行耗时
    "improvement_triggered": bool,# 是否触发改进
    "improvement_applied": int,   # 应用的改进数量
    "rollback_executed": Optional[Dict]  # 回滚信息
}
```

#### get_improvement_stats()

获取改进统计信息。

```python
get_improvement_stats(agent_id: Optional[str] = None) -> Dict
```

**参数：**
- `agent_id`: Agent ID（可选，不传则返回全局统计）

**返回值（单个 Agent）：**
```python
{
    "agent_id": str,
    "agent_stats": {
        "tasks_completed": int,
        "tasks_failed": int,
        "success_rate": float
    },
    "last_improvement": str,      # ISO 时间戳
    "cooldown_remaining_hours": float,
    "rollback_count": int
}
```

**返回值（全局）：**
```python
{
    "total_agents": int,
    "total_improvements": int,
    "total_rollbacks": int,
    "agents_improved": List[str]
}
```

### AgentTracer

任务追踪器，记录执行细节。

#### trace_execution()

追踪任务执行。

```python
trace_execution(
    agent_id: str,
    task: str,
    execute_fn: Callable,
    context: Optional[Dict] = None
) -> Dict
```

### AutoRollback

自动回滚管理器。

#### backup_config()

备份配置。

```python
backup_config(
    agent_id: str,
    config: Dict,
    improvement_id: str
) -> str  # 返回备份 ID
```

#### should_rollback()

判断是否需要回滚。

```python
should_rollback(
    agent_id: str,
    improvement_id: str,
    before_metrics: Dict,
    after_metrics: Dict
) -> Tuple[bool, str]  # (是否回滚, 原因)
```

#### rollback()

执行回滚。

```python
rollback(agent_id: str, backup_id: str) -> Dict
```

### AdaptiveThreshold

自适应阈值管理器。

#### get_threshold()

获取 Agent 的阈值配置。

```python
get_threshold(
    agent_id: str,
    recent_tasks: List[Dict]
) -> Tuple[int, int, int]  # (失败阈值, 窗口小时, 冷却小时)
```

#### set_manual_threshold()

手动设置阈值。

```python
set_manual_threshold(
    agent_id: str,
    failure_threshold: int,
    analysis_window_hours: int,
    cooldown_hours: int,
    is_critical: bool = False
)
```

#### get_agent_profile()

获取 Agent 配置档案。

```python
get_agent_profile(agent_id: str, recent_tasks: List[Dict]) -> Dict
```

### TelegramNotifier

Telegram 通知器。

#### 初始化

```python
TelegramNotifier(
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    enabled: bool = True
)
```

#### notify_improvement()

发送改进通知。

```python
notify_improvement(
    agent_id: str,
    improvements_applied: int,
    details: Optional[Dict] = None
)
```

#### notify_rollback()

发送回滚通知。

```python
notify_rollback(
    agent_id: str,
    reason: str,
    metrics: Optional[Dict] = None
)
```

---

## 📖 教程

### 快速开始（5分钟）

#### 1. 安装

```bash
git clone https://github.com/yangfei222666-9/self-improving-loop.git
cd self-improving-loop
pip install -e .
```

#### 2. 第一个例子

创建 `hello.py`：

```python
from self_improving_loop import SelfImprovingLoop

# 创建循环
loop = SelfImprovingLoop()

# 包装你的任务
def my_task():
    print("Hello, Self-Improving Loop!")
    return {"status": "success"}

# 执行任务（自动追踪 + 改进）
result = loop.execute_with_improvement(
    agent_id="hello-agent",
    task="打招呼",
    execute_fn=my_task
)

print(f"成功: {result['success']}")
print(f"耗时: {result['duration_sec']:.2f}s")
```

运行：
```bash
python hello.py
```

### 核心概念

#### 什么是 Self-Improving Loop？

Self-Improving Loop 是一个让 AI Agent 自动进化的系统。它会：

1. **追踪**每个任务的执行过程
2. **分析**失败模式
3. **生成**改进建议
4. **自动应用**低风险改进
5. **验证**改进效果
6. **回滚**效果变差的改进

#### 7 步闭环

```
┌─────────────────────────────────────────────────────────┐
│                  Self-Improving Loop                     │
│                                                          │
│  1. Execute Task    → 执行任务（透明代理）               │
│  2. Record Result   → 记录结果（Tracer）                 │
│  3. Analyze Failure → 分析失败模式                       │
│  4. Generate Fix    → 生成改进建议                       │
│  5. Auto Apply      → 自动应用低风险改进                 │
│  6. Verify Effect   → 验证效果                           │
│  7. Update Config   → 更新配置 + 自动回滚                │
└─────────────────────────────────────────────────────────┘
```

### 基础用法

#### 1. 追踪任务执行

```python
from self_improving_loop import SelfImprovingLoop

loop = SelfImprovingLoop(data_dir="./my_data")

def process_data(data):
    result = data * 2
    return result

result = loop.execute_with_improvement(
    agent_id="data-processor",
    task="处理数据",
    execute_fn=lambda: process_data(42),
    context={"input": 42}
)
```

#### 2. 处理失败

```python
def risky_task():
    import random
    if random.random() < 0.3:  # 30% 失败率
        raise Exception("网络超时")
    return {"status": "ok"}

for i in range(10):
    result = loop.execute_with_improvement(
        agent_id="risky-agent",
        task=f"任务 {i+1}",
        execute_fn=risky_task
    )
    
    if result["improvement_triggered"]:
        print(f"第 {i+1} 次失败后触发改进！")
```

#### 3. 查看统计

```python
# 单个 Agent 统计
stats = loop.get_improvement_stats("risky-agent")
print(f"成功率: {stats['agent_stats']['success_rate']:.1%}")

# 全局统计
global_stats = loop.get_improvement_stats()
print(f"总改进次数: {global_stats['total_improvements']}")
```

### 高级用法

#### 1. 集成到 Agent 类

```python
class MyAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.loop = SelfImprovingLoop()
    
    def run(self, task, **kwargs):
        return self.loop.execute_with_improvement(
            agent_id=self.agent_id,
            task=task,
            execute_fn=lambda: self._execute(task, **kwargs),
            context=kwargs
        )
    
    def _execute(self, task, **kwargs):
        if "error" in task:
            raise RuntimeError(f"执行失败: {task}")
        return {"done": True, "task": task}
```

#### 2. 自定义通知器

```python
from self_improving_loop.notifier import Notifier

class SlackNotifier(Notifier):
    def __init__(self, webhook_url):
        super().__init__(enabled=True)
        self.webhook_url = webhook_url
    
    def notify_improvement(self, agent_id, improvements_applied, details=None):
        message = f"🔧 Agent {agent_id} 应用了 {improvements_applied} 项改进"
        self._send_to_slack(message)
    
    def _send_to_slack(self, message):
        import requests
        requests.post(self.webhook_url, json={"text": message})
```

#### 3. 自适应阈值配置

```python
from self_improving_loop import AdaptiveThreshold

at = AdaptiveThreshold()

# 手动配置
at.set_manual_threshold(
    "special-agent",
    failure_threshold=10,
    analysis_window_hours=48,
    cooldown_hours=1
)
```

### 最佳实践

#### 1. 数据目录管理

```python
# 为每个项目使用独立的数据目录
loop = SelfImprovingLoop(data_dir="./project_data")
```

#### 2. Agent ID 命名规范

```python
# 使用有意义的 ID
loop.execute_with_improvement(
    agent_id="coder-backend-api",  # ✅ 清晰
    task="修复登录 bug",
    execute_fn=fix_login_bug
)

# 关键 Agent 使用特殊前缀
loop.execute_with_improvement(
    agent_id="prod-monitor-database",  # 自动识别为关键 Agent
    task="监控数据库",
    execute_fn=monitor_db
)
```

#### 3. 错误处理

```python
def safe_execute(task_fn):
    try:
        return task_fn()
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        raise Exception(f"{str(e)}\n\n{error_detail}")

result = loop.execute_with_improvement(
    agent_id="my-agent",
    task="执行任务",
    execute_fn=lambda: safe_execute(my_task)
)
```

### 常见问题 FAQ

#### Q1: 什么时候会触发改进？

当 Agent 在指定时间窗口内失败次数达到阈值时触发。默认：
- 失败阈值：3 次
- 时间窗口：24 小时
- 冷却期：6 小时

#### Q2: 改进会自动应用吗？

只有**低风险**改进会自动应用。低风险改进包括：
- 增加超时时间
- 添加重试机制
- 降低请求频率

#### Q3: 如何防止改进后效果变差？

内置自动回滚机制。如果改进后成功率下降 >10%、平均耗时增加 >20% 或连续失败 ≥5 次，会自动回滚。

#### Q4: 支持多进程/多线程吗？

支持。每个进程/线程使用独立的 `SelfImprovingLoop` 实例即可。

#### Q5: 如何集成到现有系统？

最小侵入式集成：

```python
# 原代码
def my_function():
    return result

# 集成后
from self_improving_loop import SelfImprovingLoop
loop = SelfImprovingLoop()

def my_function():
    return loop.execute_with_improvement(
        agent_id="my-function",
        task="执行任务",
        execute_fn=lambda: original_logic()
    )["result"]
```

---

## 📊 性能指标

- **追踪记录**: ~5ms
- **失败分析**: ~100ms（仅触发时）
- **改进应用**: ~200ms（仅触发时）
- **回滚执行**: ~10ms
- **总体开销**: <1%

---

## 🔧 高级配置

### 手动设置阈值

```python
from adaptive_threshold import AdaptiveThreshold

adaptive = AdaptiveThreshold()
adaptive.set_manual_threshold(
    "critical-agent",
    failure_threshold=1,
    analysis_window_hours=12,
    cooldown_hours=1,
    is_critical=True
)
```

### 自定义通知

```python
from telegram_notifier import TelegramNotifier

notifier = TelegramNotifier(enabled=True)
notifier.notify_improvement(
    agent_id="my-agent",
    improvements_applied=2,
    details={"timeout": "30s → 45s"}
)
```

### 查看统计

```python
# 单个 Agent
stats = loop.get_improvement_stats("my-agent")
print(f"成功率: {stats['agent_stats']['success_rate']:.1%}")
print(f"回滚次数: {stats['rollback_count']}")

# 全局统计
global_stats = loop.get_improvement_stats()
print(f"总改进次数: {global_stats['total_improvements']}")
print(f"总回滚次数: {global_stats['total_rollbacks']}")
```

---

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python test_self_improving_loop.py
python test_auto_rollback.py
python test_adaptive_threshold.py
```

---

## 📚 文档

- [集成指南](docs/INTEGRATION.md)
- [架构设计](docs/ARCHITECTURE.md)
- [最佳实践](docs/BEST_PRACTICES.md)

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

### 开发设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/self-improving-loop.git
cd self-improving-loop

# 安装依赖
pip install -r requirements-dev.txt

# 运行测试
pytest
```

---

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md)

---

## 📄 许可证

[MIT License](LICENSE)

---

## 🙏 致谢

灵感来源于 AIOS 项目，感谢所有贡献者。

---

## 🔗 相关项目

- [AIOS](https://github.com/yourusername/aios) - AI 操作系统
- [Agent Evolution](https://github.com/yourusername/agent-evolution) - Agent 进化框架

---

## 📧 联系

- Issues: [GitHub Issues](https://github.com/yourusername/self-improving-loop/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/self-improving-loop/discussions)

---

**"Safety first, then automation."**

Made with ❤️ by the Self-Improving Loop team
