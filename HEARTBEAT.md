# AIOS 心跳机制 - 全自动任务处理 v6.0

**触发：** 每 6 小时执行一次（OpenClaw 主会话心跳）

**最新版本：** v6.0 - 全自动执行，无需人工提醒

---

## 🤖 全自动模式（v6.0 核心理念）

**一句话：** 除非你主动叫停，否则全自动运行，不需要你提醒。

### 自动执行清单

每次心跳自动执行以下任务（按优先级）：

#### 1. GitHub 监控（每天一次）
- **OpenClaw 本体** - 检查最新 Release 和 Changelog
- **核心参考项目** - DeerFlow、Mem0、Hive、Agents
- **行业观察** - MetaGPT、LangGraph、CrewAI
- **输出：** 如有重要更新 → 自动通知你
- **频率：** 每天 08:00 自动执行

#### 2. 任务队列处理（每次心跳）
- 自动检查 `task_queue.jsonl`
- 自动执行最多 5 个待处理任务
- 自动更新任务状态
- **输出：** 只在有任务失败时通知

#### 3. Agent 健康检查（每天一次）
- 自动检测"僵尸 Agent"（定义了但从未运行）
- 自动激活休眠的学习 Agent
- 自动应用低风险改进
- **输出：** 只在发现问题时通知
- **频率：** 每天 21:00 自动执行

#### 4. 系统维护（每天一次）
- 自动清理临时文件
- 自动归档旧日志（>7天）
- 自动备份关键数据
- **输出：** 静默执行，不通知

### 通知策略

**只在以下情况通知你：**
- ✅ 发现重要的 GitHub 更新（OpenClaw 新版本、核心项目重大变更）
- ✅ 任务执行失败需要人工介入
- ✅ Agent 连续失败 ≥3 次
- ✅ 系统健康度 < 60（CRITICAL）
- ✅ 发现新的可借鉴技术（类似 Macrohard 那种）

**静默执行（不通知）：**
- ❌ 任务正常完成
- ❌ Agent 正常运行
- ❌ 系统健康度 ≥ 80
- ❌ 日常维护任务
- ❌ GitHub 无重要更新

---

## ⚡ 心跳执行流程

### 1. 处理 spawn_pending.jsonl（最优先）

每次心跳，在运行其他任务之前，先检查：

```
C:\Users\A\.openclaw\workspace\aios\agent_system\data\spawn_pending.jsonl
```

如果文件非空，读取每一行，对每条记录调用真实的 `sessions_spawn` 工具，然后清空文件。

**这是生产级闭环的关键步骤，不可跳过。**

### 2. GitHub 监控（每天 08:00）

```python
def run_github_monitoring():
    # 检查 OpenClaw 最新 Release
    check_openclaw_updates()
    
    # 检查核心参考项目
    check_core_projects()  # DeerFlow, Mem0, Hive, Agents
    
    # 检查行业观察项目
    check_industry_projects()  # MetaGPT, LangGraph, CrewAI
    
    # 生成周报
    generate_weekly_report()
    
    # 智能通知（只在有重要更新时）
    notify_if_important_updates()
```

### 3. 任务队列处理（每次心跳）

```python
def process_task_queue():
    # 读取待处理任务
    tasks = load_pending_tasks()
    
    # 最多处理 5 个任务
    for task in tasks[:5]:
        # 根据类型路由到对应 Agent
        agent = route_to_agent(task.type)
        
        # 执行任务
        result = execute_task(agent, task)
        
        # 更新状态
        update_task_status(task, result)
    
    # 只在失败时通知
    notify_if_failures()
```

### 4. Agent 健康检查（每次心跳）

```python
def check_agent_health():
    # 检测僵尸 Agent
    zombies = find_zombie_agents()
    
    # 自动激活
    for agent in zombies:
        activate_agent(agent)
    
    # 检测连续失败
    failing = find_failing_agents()
    
    # 自动应用修复
    for agent in failing:
        apply_auto_fix(agent)
    
    # 只在发现问题时通知
    notify_if_issues()
```

### 5. 系统维护（每天 02:00）

```python
def run_system_maintenance():
    # 清理临时文件
    clean_temp_files()
    
    # 归档旧日志
    archive_old_logs()
    
    # 备份关键数据
    backup_critical_data()
    
    # 静默执行，不通知
```

---

## 🚀 使用方式

### 推荐方式（环境变量 + 参数双保险）

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v6.py
```

### 简化方式（仅参数）

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v6.py
```

---

## 📊 输出示例

### 正常情况（静默）

```
HEARTBEAT_OK (auto-mode, no alerts)
```

### 有重要 GitHub 更新时

```
🔔 GitHub 更新通知

OpenClaw v2.5.0 发布
- 新增 canvas 工具支持
- 优化 sessions_spawn 性能
- 修复 browser 工具的内存泄漏

建议：评估是否升级
详见：https://github.com/openclaw/openclaw/releases/tag/v2.5.0
```

### 有任务失败时

```
⚠️ 任务执行失败

任务：重构 scheduler.py
Agent：coder-dispatcher
失败原因：timeout (120s)
建议：任务可能过于复杂，需要拆分

详见：aios/agent_system/task_executions.jsonl
```

### 有 Agent 问题时

```
🔧 Agent 健康检查

发现问题：
- GitHub_Researcher 从未运行（僵尸 Agent）
- coder-dispatcher 连续失败 3 次

已自动处理：
✅ 激活 GitHub_Researcher
✅ 应用 coder-dispatcher 修复（调整超时 60s → 120s）

下次心跳将验证修复效果
```

---

## 🔕 告警去重规则

Skill 连续失败告警默认去重，**已发过的告警不重复通知**。

仅在以下情况重新通知：
- 连续失败次数继续增加
- 错误类型发生变化
- 等级升级（WARN → CRIT）
- 修复后再次复发

---

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

---

## ⛔ 命令格式硬约束（不可违反）

执行 shell 命令时必须严格遵守以下规则：

1. **禁止使用 `~\`** — 用绝对路径 `C:\Users\A\.openclaw\workspace\...` 或 `$HOME\.openclaw\workspace\...`
2. **禁止使用 `&&`** — PowerShell 用 `;` 分隔命令
3. **禁止简化或改写命令模板** — 复制粘贴上面的完整模板，只替换 `<script.py>` 部分
4. **工作目录切换** — 用 `cd C:\Users\A\.openclaw\workspace\aios\agent_system;` 不用 `Set-Location`
5. **命令必须原样复制执行** — 不允许改写分隔符、路径写法、引号或变量形式

违反以上规则会导致 PowerShell 解析失败。

---

## 📈 版本对比

| 版本 | 用途 | 特点 | 人工介入 |
|------|------|------|---------|
| v3.6 Demo | 开发测试 | 直接模拟执行，秒级反馈 | 每次手动触发 |
| v3.6 Full | 生产环境 | 创建 spawn 请求，真实执行 | 每次手动触发 |
| v4.0 | 生产环境 | 集成 Self-Improving Loop v2.0 | 每次手动触发 |
| v5.0 | 生产环境 | 集成 Task Queue，自动执行任务 | 每次手动触发 |
| **v6.0** | **生产环境（推荐）** | **全自动执行，智能通知** | **只在需要时通知** |

---

## 📅 自动执行时间表

| 任务 | 频率 | 时间 | 通知策略 |
|------|------|------|---------|
| GitHub 监控 | 每天 | 08:00 | 只在有重要更新时通知 |
| 任务队列处理 | 每 6 小时 | 心跳触发 | 只在失败时通知 |
| Agent 健康检查 | 每天 | 21:00 | 只在发现问题时通知 |
| 系统维护 | 每天 | 02:00 | 静默执行 |

---

## 🔍 故障排查

### 如果 GitHub 监控没有运行

1. 检查 `memory/github-watch-schedule.md` 的 `下次检查` 时间
2. 查看 `heartbeat.log` 的最近记录
3. 确认 OpenClaw 主会话心跳正常运行

### 如果任务不执行

1. 检查 `task_queue.jsonl` 是否有任务
2. 检查 `spawn_pending.jsonl` 是否生成
3. 查看 `heartbeat.log` 的错误信息

### 如果 Agent 一直失败

1. 查看 `agents.json` 的 `stats.tasks_failed`
2. 检查超时设置（默认60s）
3. 查看任务复杂度（是否需要拆分）

### 如果学习 Agent 不运行

1. 检查 `memory/selflearn-state.json` 的时间戳
2. 查看 `spawn_requests.jsonl` 是否有请求
3. 确认 OpenClaw 主会话正常运行

---

**版本：** v6.0  
**最后更新：** 2026-03-13  
**维护者：** 小九 + 珊瑚海

**变更日志：**
- v6.0 (2026-03-13) - 全自动模式，智能通知，GitHub 监控集成
- v5.0 (2026-02-26) - 集成 Task Queue，自动执行任务
- v4.0 (2026-02-26) - 集成 Self-Improving Loop v2.0
- v3.6 (2026-02-26) - 新增 Demo 模式，双版本并存
