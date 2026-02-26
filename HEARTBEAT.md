# AIOS 心跳机制 - 自动任务处理 v3.6

**触发：** 每 30 秒执行一次（OpenClaw 主会话心跳）

## 心跳模式

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
python heartbeat_demo.py
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
python heartbeat_full.py
```

**或在 OpenClaw 主会话心跳中调用：**
```bash
& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\heartbeat_full.py
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
