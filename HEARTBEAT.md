# AIOS 心跳机制 - 自动任务处理 v5.1

**触发：** 每 6 小时执行一次（OpenClaw 主会话心跳）

**最新版本：** v5.1 - 真实 sessions_spawn 执行

## 🔕 告警去重规则（2026-03-08 珊瑚海确认）

Skill 连续失败告警默认去重，**已发过的告警不重复通知**。

仅在以下情况重新通知：
- 连续失败次数继续增加
- 错误类型发生变化
- 等级升级（WARN → CRIT）
- 修复后再次复发

当前已抑制的旧告警（2026-03-06，已发送）：
- `api-testing-skill v1.0.0` - CRIT (network_error)
- `docker-skill v0.9.0` - CRIT (resource_exhausted)
- `pdf-skill v2.1.0` - WARN (timeout)

---

## ⚡ 心跳必做：处理 spawn_pending.jsonl

每次心跳，在运行 heartbeat_v5.py 之前，先检查：

```
C:\Users\A\.openclaw\workspace\aios\agent_system\data\spawn_pending.jsonl
```

如果文件非空，读取每一行，对每条记录调用真实的 sessions_spawn 工具，然后清空文件。

**这是生产级闭环的关键步骤，不可跳过。**

### 执行步骤

1. **读取 spawn_pending.jsonl**
2. **对每条记录调用 sessions_spawn**（使用记录中的 agent_id, task, label, cleanup, runTimeoutSeconds）
3. **清空 spawn_pending.jsonl**
4. **运行自动改进检查**（`run_self_improving.py --dry-run`）
5. **继续执行 heartbeat_v5.py**

## 🔧 自动改进（Self-Improving Loop）

每次心跳自动检查所有 Agent 的健康状况，并在必要时应用改进。

### 执行命令

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 run_self_improving.py --dry-run
```

### 改进触发条件

- 成功率 < 70%
- 至少有 3 次任务记录
- 不在冷却期（6 小时）

### 改进机制

1. **自动检测失败模式** - 分析最近 24 小时的任务执行记录
2. **生成改进建议** - 基于失败模式生成具体改进方案
3. **自动应用低风险改进** - 只自动应用 `risk=low` 的改进
4. **自动回滚** - 如果改进后效果变差，自动回滚到改进前状态
5. **冷却期保护** - 每次改进后 6 小时内不再触发改进

### 输出示例

```
============================================================
Self-Improving Loop - 自动改进
============================================================
时间: 2026-03-12 00:09:10
模式: Dry-Run（只分析）

📊 检查 8 个 Agent...

✅ agent_coder_001
   任务数: 3 | 成功率: 100.0%

⚠️ coder-dispatcher
   任务数: 3 | 成功率: 0.0%
   🔧 需要改进

============================================================
汇总统计
============================================================
✅ 健康: 6
⚠️ 不健康: 2
🔧 需要改进: 2

📈 总改进次数: 3
📋 已改进 Agent: 3
```

## 🔧 编码配置（重要）

为避免 Windows/PowerShell 编码问题，所有 Python 命令统一使用：

**环境变量（推荐）：**
- `PYTHONUTF8=1` - Python 3.7+ 全局 UTF-8 模式
- `PYTHONIOENCODING=utf-8` - 标准输入输出编码

**命令行参数：**
- `-X utf8` - 强制 UTF-8 模式

**完整命令模板：**
```powershell
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 <script.py>
```

## ⛔ 命令格式硬约束（不可违反）

执行 shell 命令时必须严格遵守以下规则：

1. **禁止使用 `~\`** — 用绝对路径 `C:\Users\A\.openclaw\workspace\...` 或 `$HOME\.openclaw\workspace\...`
2. **禁止使用 `&&`** — PowerShell 用 `;` 分隔命令
3. **禁止简化或改写命令模板** — 复制粘贴上面的完整模板，只替换 `<script.py>` 部分
4. **工作目录切换** — 用 `cd C:\Users\A\.openclaw\workspace\aios\agent_system;` 不用 `Set-Location`
5. **命令必须原样复制执行** — 不允许改写分隔符、路径写法、引号或变量形式
6. **命令示例统一放在反引号代码块或行内代码中**，避免被当成普通文本后再“智能改写”

违反以上规则会导致 PowerShell 解析失败（已发生过：`cd ~\.openclaw\... && ...` 在字符 53 处报错）。

---

## 版本对比

| 版本 | 用途 | 特点 |
|------|------|------|
| v3.6 Demo | 开发测试 | 直接模拟执行，秒级反馈 |
| v3.6 Full | 生产环境 | 创建 spawn 请求，真实执行 |
| v4.0 | 生产环境 | 集成 Self-Improving Loop v2.0，自动监控和改进 |
| **v5.0** | **生产环境（推荐）** | **集成 Task Queue，自动执行待处理任务** |

---

## 🚀 Heartbeat v5.0（推荐）

### 新增功能

1. **自动处理任务队列**
   - 每次心跳检查待处理任务
   - 自动执行最多 5 个任务
   - 根据任务类型路由到对应 Agent
   - 更新任务状态（completed/failed）

2. **系统健康度评估**
   - 基于任务成功率计算健康分数（0-100）
   - 健康度 >= 80：GOOD
   - 健康度 60-79：WARNING
   - 健康度 < 60：CRITICAL

3. **完整工作流**
   - 用户提交任务 → 进入队列
   - Heartbeat 自动检测 → 执行任务
   - 更新状态 → 记录结果

### 使用方式

**推荐方式（环境变量 + 参数双保险）：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py
```

**简化方式（仅参数）：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py
```

### 输出示例

**有任务处理：**
```
AIOS Heartbeat v5.0 Started

[QUEUE] Processing 3 pending tasks...
[1/3] Executing task: task-xxx
  Type: code
  Description: 重构 scheduler.py
  ✓ Completed in 21.2s
[2/3] Executing task: task-yyy
  Type: analysis
  Description: 分析错误日志
  ✓ Completed in 22.0s
[3/3] Executing task: task-zzz
  Type: monitor
  Description: 监控资源使用率
  ✓ Completed in 24.9s

[QUEUE] Processed 3 tasks
  Success: 3
  Failed: 0

[HEALTH] Checking system health...
   Health Score: 85.71/100
   Total Tasks: 7
   Completed: 6
   Failed: 1
   Pending: 0
   Status: GOOD

HEARTBEAT_OK (processed=3, health=86)

Heartbeat Completed
```

**无任务时：**
```
AIOS Heartbeat v5.0 Started

[QUEUE] No pending tasks

[HEALTH] Checking system health...
   Health Score: 74.29/100
   Total Tasks: 7
   Completed: 5
   Failed: 2
   Pending: 0
   Status: WARNING

HEARTBEAT_OK (no_tasks, health=74)

Heartbeat Completed
```

---

## 完整工作流

```
1. 用户提交任务
   python aios.py submit --desc "重构 scheduler.py" --type code --priority high

2. 任务进入队列
   task_queue.jsonl

3. Heartbeat 自动检测（每 6 小时）
   heartbeat_v5.py

4. 执行任务
   TaskExecutor → sessions_spawn（未来集成）

5. 更新状态
   task_queue.jsonl (status: completed/failed)

6. 记录结果
   task_executions.jsonl
```

---

## 心跳模式（v3.6）

AIOS 提供两种心跳模式，适用于不同场景：

### 🎯 Demo 模式 (`heartbeat_demo.py`)
- **用途：** 开发测试、快速验证、演示展示
- **特点：** 直接模拟执行，秒级反馈
- **执行：** `python heartbeat_demo.py`
- **输出：** 清晰的任务执行日志
- **适合：** 日常开发、功能测试、给别人演示

### 🚀 Full 模式 (`heartbeat_full.py`)
- **用途：** 生产环境、真实任务执行
- **特点：** 创建 spawn 请求，通过 OpenClaw 执行真实 Agent
- **执行：** `python heartbeat_full.py`
- **输出：** spawn 请求记录
- **适合：** 生产部署、真实工作流

**建议：** 开发时用 Demo 模式快速测试，部署时用 Full 模式真实执行。

## 1. 心跳主流程

```python
def heartbeat():
    log("🚀 AIOS Heartbeat Started @ " + now())
    
    # 1. 处理任务队列（最优先）
    process_task_queue()  # 核心！
    
    # 2. 检查并启动从未运行的学习Agent
    activate_sleeping_learning_agents()
    
    # 3. 处理 Coder 连续失败问题
    handle_coder_failure()
    
    # 4. Self-Improving Loop 检查
    check_self_improving_loop()
    
    # 5. 清理 & 记录
    clean_temp_files()
    
    log("✅ Heartbeat Completed")
```

## 2. 核心函数说明

### process_task_queue()
- 读取 `task_queue.jsonl`
- 每次最多处理 5 个任务
- 根据 type 自动路由：
  - `code` → coder-dispatcher
  - `analysis` → analyst-dispatcher
  - `monitor` → monitor-dispatcher
- 通过 `sessions_spawn` 执行
- 成功 → 记录到 `spawn_results.jsonl`
- 失败 → 重试最多 3 次，失败后进入 `lessons.json`
- 更新队列状态（已处理的任务移走）

### activate_sleeping_learning_agents()
- 扫描 `learning_agents.py` 中的所有 Agent
- 找出从未运行的 Agent（state 中没有 `last_xxx` 记录）
- 为它们创建 spawn 请求
- 输出：
  - `LEARNING_AGENTS_OK` - 所有 Agent 都运行过
  - `LEARNING_AGENTS_ACTIVATED:N` - 激活了 N 个休眠 Agent

### handle_coder_failure()
- 检查 coder-dispatcher 的失败次数
- 如果失败 ≥3 次：
  - 分析失败原因（超时、模型错误、任务复杂度）
  - 自动应用修复：
    - 调整超时（60s → 120s）
    - 切换模型（opus → sonnet）
    - 简化任务（拆分为子任务）
- 输出：
  - `CODER_OK` - Coder 正常
  - `CODER_FIXED` - 已应用修复
  - `CODER_NEEDS_ATTENTION` - 需要人工介入

### check_self_improving_loop()
- 检查所有 Agent 的自动改进统计
- 如果有新的改进应用，主动通知
- 每天报告一次全局统计

### clean_temp_files()
- 清理临时文件（.bak、__pycache__）
- 归档旧日志（>7天）
- 记录心跳统计

## 3. 日志记录

所有心跳活动记录到：
- `aios/agent_system/heartbeat.log` - 详细日志
- `aios/agent_system/heartbeat_stats.json` - 统计数据

## 4. 执行方式

### Demo 模式（快速测试）
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_demo.py
```

**输出示例：**
```
🚀 AIOS Heartbeat Started
📋 处理任务队列...
  本次处理 3 个任务
  [1/3] 执行 code 任务 (优先级: high)
      ✅ Coder Agent 完成代码任务: 重构 scheduler.py
  [2/3] 执行 analysis 任务 (优先级: normal)
      ✅ Analyst Agent 完成分析任务: 分析失败事件
  [3/3] 执行 monitor 任务 (优先级: low)
      ✅ Monitor Agent 完成监控任务: 检查磁盘使用率
✅ Heartbeat Completed
```

### Full 模式（生产环境）
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_full.py
```

**或在 OpenClaw 主会话心跳中调用：**
```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\heartbeat_full.py
```

## 5. 输出格式

**正常情况（静默）：**
```
HEARTBEAT_OK (3 tasks processed, 0 agents activated)
```

**有任务处理：**
```
QUEUE_PROCESSED:3 (coder:1, analyst:1, monitor:1)
```

**有Agent激活：**
```
LEARNING_AGENTS_ACTIVATED:5 (GitHub_Code_Reader, Bug_Hunter, ...)
```

**有失败需要关注：**
```
CODER_NEEDS_ATTENTION (3 consecutive failures, last: timeout)
```

## 6. 故障排查

**如果任务不执行：**
1. 检查 `task_queue.jsonl` 是否有任务
2. 检查 `spawn_requests.jsonl` 是否生成
3. 查看 `heartbeat.log` 的错误信息

**如果 Coder 一直失败：**
1. 查看 `agents.json` 的 stats.tasks_failed
2. 检查超时设置（默认60s）
3. 查看任务复杂度（是否需要拆分）

**如果学习Agent不运行：**
1. 检查 `memory/selflearn-state.json` 的时间戳
2. 查看 `spawn_requests.jsonl` 是否有请求
3. 确认 OpenClaw 主会话正常运行

---

**版本：** v3.6  
**最后更新：** 2026-02-26  
**维护者：** 小九 + 珊瑚海

**变更日志：**
- v3.6 (2026-02-26) - 新增 Demo 模式，双版本并存
- v3.5 (2026-02-26) - 完整的任务队列处理
