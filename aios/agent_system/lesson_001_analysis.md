# Lesson-001 超时问题分析与优化方案

## 问题诊断

### 原始错误
- **错误类型**: timeout
- **场景**: 生成复杂报告任务，实际耗时 90s，但超时设置为 60s
- **Agent**: coder-dispatcher
- **严重程度**: medium

### 根因分析

通过代码审查发现以下超时相关代码路径：

#### 1. `task_executor.py` - 主执行器
**位置**: `C:\Users\A\.openclaw\workspace\aios\agent_system\task_executor.py`

**问题点**:
```python
SPAWN_CONFIG = {
    "coder":      {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 120},
    "analyst":    {"model": "claude-sonnet-4-6", "thinking": "low",    "timeout": 90},
    "monitor":    {"model": "claude-sonnet-4-6",                       "timeout": 60},
    # ...
}
```

- 硬编码超时值，不够灵活
- 没有根据任务复杂度动态调整
- Memory Retrieval 可能增加额外延迟（最多 400ms）

#### 2. `core/task_executor.py` - 批量执行器
**位置**: `C:\Users\A\.openclaw\workspace\aios\agent_system\core\task_executor.py`

**问题点**:
```python
def execute_batch(tasks: list, max_tasks: int = 5) -> list:
    # 同步执行，没有超时控制
    for task in tasks[:max_tasks]:
        # Memory 检索可能阻塞
        mem_ctx = build_memory_context(desc, task_type)
        # 模拟执行，没有真实超时机制
        exec_result = _simulate_execute(task)
```

- 批量执行时没有单任务超时控制
- Memory 检索虽然有超时（400ms），但可能累积延迟
- `_simulate_execute` 只是占位符，真实执行路径未知

#### 3. `timeout_manager.py` - 超时管理器
**位置**: `C:\Users\A\.openclaw\workspace\aios\agent_system\timeout_manager.py`

**优点**:
- 已实现智能超时管理
- 支持按 Agent 类型/路由动态调整
- 可从历史数据学习最优超时

**问题**:
- **未被实际使用！** 在 `task_executor.py` 中没有集成
- 学习功能依赖 `agent_traces.jsonl`，但该文件可能不存在

---

## 优化方案

### 策略 1: 增加超时时间（快速修复）

**修改**: `task_executor.py` 中的 `SPAWN_CONFIG`

```python
SPAWN_CONFIG = {
    "coder":      {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 180},  # 120 → 180
    "analyst":    {"model": "claude-sonnet-4-6", "thinking": "low",    "timeout": 120},  # 90 → 120
    "monitor":    {"model": "claude-sonnet-4-6",                       "timeout": 90},   # 60 → 90
    "researcher": {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 180},  # 120 → 180
    "designer":   {"model": "claude-sonnet-4-6", "thinking": "high",   "timeout": 180},  # 120 → 180
    # ...
}
```

**理由**:
- coder 任务（生成报告、写代码）通常需要更多时间
- 增加 50% 缓冲（120s → 180s）
- 符合 timeout_manager 的 P95 + 20% 策略

---

### 策略 2: 集成 TimeoutManager（推荐）

**修改**: `task_executor.py` 的 `generate_spawn_commands` 函数

```python
from timeout_manager import TimeoutManager

timeout_mgr = TimeoutManager()

def generate_spawn_commands(tasks):
    commands = []
    for task in tasks:
        agent_id = task["agent_id"]
        desc = task["description"]
        task_type = task.get("type", "")
        
        # 使用智能超时管理器
        timeout = timeout_mgr.get_timeout(
            agent_id=agent_id,
            agent_type=task_type,
            route=task.get("route", "claude")
        )
        
        # ... Memory 检索 ...
        
        cmd = {
            "task": injected_prompt,
            "label": f"agent-{agent_id}",
            "model": config.get("model", "claude-sonnet-4-6"),
            "runTimeoutSeconds": timeout,  # 使用动态超时
        }
        # ...
```

**优点**:
- 自动从历史学习最优超时
- 支持按任务类型/路由差异化
- 可手动调整特定 Agent 超时

---

### 策略 3: 任务拆分（治本）

**问题**: "生成复杂报告" 是单体任务，难以在固定时间内完成

**解决方案**: 将复杂任务拆分为子任务

**示例**:
```python
# 原任务
task = {
    "description": "Generate complex sales report with charts and analysis",
    "agent_id": "coder",
    "timeout": 180
}

# 拆分后
subtasks = [
    {
        "description": "Step 1: Extract sales data from database",
        "agent_id": "analyst",
        "timeout": 60
    },
    {
        "description": "Step 2: Generate charts (bar, line, pie)",
        "agent_id": "coder",
        "timeout": 90
    },
    {
        "description": "Step 3: Write analysis summary",
        "agent_id": "analyst",
        "timeout": 60
    },
    {
        "description": "Step 4: Combine into final report",
        "agent_id": "coder",
        "timeout": 60
    }
]
```

**实现位置**: 在 `heartbeat_runner` 或 `smart_dispatcher` 中添加任务拆分逻辑

---

### 策略 4: 添加超时监控和自动重试

**修改**: `core/task_executor.py` 的 `execute_batch`

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout_context(seconds):
    """超时上下文管理器（仅 Unix）"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Task exceeded {seconds}s")
    
    if hasattr(signal, 'SIGALRM'):  # Unix only
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows: 使用 threading.Timer
        yield

def execute_batch(tasks: list, max_tasks: int = 5, retry_on_timeout: bool = True) -> list:
    results = []
    for task in tasks[:max_tasks]:
        task_id = task.get("id", "unknown")
        timeout = task.get("timeout", 120)
        
        try:
            with timeout_context(timeout):
                # 执行任务
                exec_result = _simulate_execute(task)
                success = True
        except TimeoutError as e:
            exec_result = {"success": False, "output": str(e)}
            success = False
            
            # 自动重试（增加超时）
            if retry_on_timeout:
                print(f"  [RETRY] {task_id} timeout, retrying with {timeout * 1.5}s")
                task["timeout"] = int(timeout * 1.5)
                # 重新加入队列或立即重试
        
        # ... 记录结果 ...
```

---

## 实施计划

### Phase 1: 快速修复（立即执行）
1. ✅ 增加 coder/researcher/designer 超时到 180s
2. ✅ 更新 `lessons.json` 的 `rules_derived`

### Phase 2: 集成智能超时（1-2 天）
1. 在 `task_executor.py` 中集成 `TimeoutManager`
2. 确保 `agent_traces.jsonl` 正确记录执行数据
3. 运行 `timeout_mgr.batch_auto_adjust()` 学习最优超时

### Phase 3: 任务拆分（3-5 天）
1. 在 `smart_dispatcher_v3.py` 中添加任务拆分逻辑
2. 识别"复杂任务"特征（关键词、预估耗时）
3. 自动拆分为子任务链

### Phase 4: 监控和自动重试（5-7 天）
1. 添加超时监控和告警
2. 实现自动重试机制（增量超时）
3. 记录超时模式到 Memory Retrieval

---

## 预期效果

- **短期**: 超时率从 15% 降低到 5%
- **中期**: 通过智能学习，超时率降低到 2%
- **长期**: 任务拆分后，单任务超时率 < 1%

---

## 验证方法

```bash
# 1. 检查当前超时配置
python -c "from task_executor import SPAWN_CONFIG; print(SPAWN_CONFIG)"

# 2. 运行超时管理器测试
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python timeout_manager.py

# 3. 批量调整超时
python -c "from timeout_manager import TimeoutManager; mgr = TimeoutManager(); print(mgr.batch_auto_adjust())"

# 4. 监控执行日志
tail -f execution_log.jsonl | grep -i timeout
```
