# 太极OS (AIOS) - Agent System

> 个人 AI Agent 操作系统，目标是让 Agent 能稳定跑任务、看见状态、处理异常、积累经验。

## 当前状态

**阶段：** 实验型系统，从"能跑"走向"可信"的过渡期。

主链路已存在（调度、心跳、记忆、队列、监控），但真相链尚未完全稳定。

## 已验证功能

以下功能经过真实运行验证：

- **Task Queue** — 任务入队 (`enqueue_task`)、状态流转 (`transition_status`)、按状态查询 (`list_tasks_by_status`)
- **Heartbeat v6** — 定时心跳，自动执行健康检查、任务队列处理、Agent 状态检测
- **Memory Server** — Embedding 模型热加载（端口 7788），消除冷启动延迟
- **Health Monitor** — Agent 存活性检测 + 退化检测，告警写入 `data/alerts.jsonl`
- **Notification Manager** — 读取告警并通过 Telegram 推送
- **Self-Improving Loop** — 7 步闭环（执行→记录→分析→生成→应用→验证→回滚）
- **状态词表** — 统一语义的 Agent 状态模型（active/idle/degraded/offline/never_run）
- **备份系统** — G 盘自动备份，每天 23:30 执行，保留 30 天
- **Dashboard v3.4 / v4.0** — Web 面板（端口 8888/8889），但数据源尚未接真实数据

## 未验证 / 已知问题

- **Dashboard 数据源** — v3.4 和 v4.0 均使用随机数，不是真实系统数据
- **GitHub_Researcher** — 已注册但从未真正自动运行（调度缺失）
- **Learning Loop 闭环** — 有记录失败，但未转成可复用规则
- **Scheduler 自动调度** — 依赖心跳触发，无独立调度进程
- **cli.py** — 不存在，QUICKSTART 中引用的命令无法使用
- **Evaluator.check_system_health()** — 方法不存在，Evaluator 只有 run_test/run_suite/compare_results/generate_report
- **events 回写链** — 9 天无新事件记录（截至 2026-03-12）
- **alerts 路径分裂** — 根目录 `alerts.jsonl` vs `data/alerts.jsonl`，已迁移但需持续观察

## 目录结构（关键部分）

```
agent_system/
├── agents/              # Agent 实现（health_monitor, resource_monitor, notification_manager 等）
├── agents.json          # Agent 注册表
├── core/                # 核心模块（task_executor, scheduler_enhancement, status_adapter）
├── data/                # 运行时数据（alerts, events, tasks, spawn 等）
├── memory/              # Agent 记忆存储
├── memory_server.py     # Embedding 服务（端口 7788）
├── task_queue.py        # 任务队列
├── heartbeat_v6.py      # 心跳主程序
├── self_improving_loop.py  # 自改进闭环
├── paths.py             # 路径常量（数据文件的 source of truth）
├── notifier.py          # 告警通知
└── evaluator.py         # 测试评估器
```

## 最小运行链

能稳定复现的端到端链路：

```
心跳触发 → health_monitor 检测 → 写入 alerts.jsonl → notification_manager 读取 → Telegram 推送
```

其他链路（task queue → agent 执行 → 结果回写 → learning loop）存在但未稳定验证。

## 运行

```powershell
# 启动 Memory Server
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; & "C:\Program Files\Python312\python.exe" -X utf8 memory_server.py

# 启动 Dashboard v4.0
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v4.0
& "C:\Program Files\Python312\python.exe" server.py

# 手动触发心跳
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v6.py
```

## 依赖

见 `requirements.txt`。核心依赖只有 `requests` 和 `Flask`。

## 下一步优先级

**P0 — 真链跑通：**
1. GitHub_Researcher 真正自动运行
2. Task Queue → Agent 执行 → 结果回写 端到端验证
3. Dashboard 接真实数据

**P1 — 闭环稳定：**
1. Learning Loop 从失败中提炼可复用规则
2. Scheduler 独立调度（不依赖心跳）
3. Events 回写链恢复

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-13
