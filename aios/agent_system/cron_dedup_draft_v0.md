# Cron 去重清单草案 v0
> 生成时间：2026-03-07  
> 总任务数：52 条（含已禁用 5 条）  
> 原则：只分类，不删除。deprecated candidate 不立即动。

---

## 字段说明
| 字段 | 含义 |
|------|------|
| 任务名 | cron 任务名称 |
| 当前作用 | 实际做什么 |
| 输入源 | 读哪里的数据 |
| 输出产物 | 写/发什么 |
| 与谁重叠 | 功能重叠的任务 |
| 建议动作 | 保留 / 合并 / 废弃 / 待观察 |
| 风险等级 | 低 / 中 / 高 |

---

## 🟢 一、保留（唯一职责 / 核心主链路 / 唯一入口）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 与谁重叠 | 建议动作 | 风险等级 |
|--------|----------|--------|----------|----------|----------|----------|
| AIOS Heartbeat (Production) | 主心跳，处理 spawn_pending，驱动整个 AIOS 主循环 | HEARTBEAT.md / spawn_pending.jsonl | 任务执行 / HEARTBEAT_OK | 无 | **保留** | 高 |
| AIOS Alert Dispatcher | 唯一的 alerts.jsonl → Telegram 发送入口 | alerts.jsonl | Telegram 通知 | 无 | **保留** | 高 |
| API 端点故障恢复监控 | 每 5 分钟轮询 API 健康，唯一 api_monitor.py 执行入口 | api_monitor.py | api_monitor_notify.json | 无 | **保留** | 高 |
| AIOS Data Flush (21:59) | 每晚 21:59 刷写数据，是 Daily Observation 的前置依赖 | agent_system 数据 | 落盘 | 无 | **保留** | 高 |
| AIOS Daily Observation (22:00) | 每晚 22:00 生成 observation 行，追加 observation_log.md，发给珊瑚海 | daily_metrics.py | observation_log.md + Telegram | 无 | **保留** | 高 |
| AIOS Backup (Production) | 生产级备份，有完整验证逻辑，保留 30 天 | AIOS 配置/数据/记忆 | C:\Backups\AIOS\ | 每日数据备份、AIOS每日备份、Backup Agent 数据备份 | **保留**（主备份） | 高 |
| AIOS Cleanup (Production) | 生产级清理，有归档逻辑 | 旧日志/temp | 清理结果 | 每日自动清理电脑、每日电脑清理 | **保留**（主清理） | 高 |
| AIOS Learning (Production) | 统一学习入口，运行 GitHub 研究/架构分析/代码审查等 | GitHub / 代码库 | 学习报告 | AIOS学习Agent、AIOS每周学习、每晚学习总结 | **保留**（主学习） | 中 |
| AIOS Daily Report (Production) | 生产级日报，任务完成/Agent性能/成本/改进建议 | agent_system 数据 | 日报 Telegram | AIOS 每日简报+反思、AIOS Daily Report - 09:15、Analyst Agent 每日简报 | **保留**（主日报） | 中 |
| AIOS Health Check (Production) | 每 6 小时健康检查，health score < 60 告警 | 系统指标/Agent状态 | 健康报告 | AIOS系统健康检查、AIOS健康监控、AIOS Health Monitor | **保留**（主健康检查） | 中 |
| Self-Healing Agent 自愈修复 | 每 15 分钟，唯一自愈执行入口（进程崩溃/内存泄漏/磁盘满） | 系统进程/日志 | 修复操作 + self_healing.jsonl | 无 | **保留** | 中 |
| Reviewer 代码审查 | 每周五 17:00，唯一代码审查入口，git diff 7天 | git log | 审查报告 Telegram | 无 | **保留** | 低 |
| memory_eval_daily | 每日 09:00，唯一 memory retrieval 评估入口 | daily_eval.py | memory_eval 报告 Telegram | 无 | **保留** | 低 |
| Meta-Agent 自适应调整 | 每日 05:00，唯一 Meta-Agent 入口，自动调整其他 Agent 频率 | agents.jsonl / execution_log.jsonl | meta_adjustments.jsonl | 无 | **保留** | 中 |
| Experiment Agent 实验优化 | 每周日 02:00，唯一 A/B 实验入口 | 当前配置 | experiments.jsonl | 无 | **保留** | 低 |
| Knowledge Graph Agent 知识图谱 | 每日 06:00，唯一知识图谱构建入口 | lessons.json / MEMORY.md | knowledge_graph.json | 无 | **保留** | 低 |
| Prediction Agent 预测预警 | 每日 08:00，唯一预测入口（资源/错误/性能退化） | 历史指标 | 预警 Telegram | 无 | **保留** | 低 |
| 世界杯投注方案提醒 | 一次性提醒，2026-06-01 触发 | 无 | Telegram 提醒 | 无 | **保留** | 低 |
| AIOS 趋势对比（每日09:20） | 每日 09:20，baseline snapshot + 趋势对比，超阈值才推送 | baseline.py / trend.py | 趋势报告（条件推送） | 无 | **保留** | 低 |

---

## 🟡 二、合并（逻辑相近，可统一）

### 合并组 A：备份类（3 → 1）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 建议动作 |
|--------|----------|--------|----------|----------|
| 每日数据备份 | 03:30 执行 daily_backup.ps1 | workspace | 备份文件 | **废弃**（被 Production 覆盖） |
| AIOS每日备份 | 09:00 "备份 AIOS 重要数据"（无具体逻辑） | 不明 | 不明 | **废弃**（空壳任务） |
| Backup Agent 数据备份 | 03:00 执行 security_auditor.py 路径的备份逻辑 | AIOS 配置/数据 | C:\Backups\AIOS\ | **废弃**（被 Production 覆盖） |

> 统一保留：**AIOS Backup (Production)**（03:00，isolated，有完整验证逻辑）

---

### 合并组 B：清理类（3 → 1）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 建议动作 |
|--------|----------|--------|----------|----------|
| 每日电脑清理（08:30） | 08:30 执行 scripts/daily_cleanup.py | workspace | 清理结果 | **废弃**（被 Production 覆盖） |
| 每日自动清理电脑 | 03:00 执行 aios/maintenance/daily_cleanup.py | workspace | 清理结果 | **废弃**（被 Production 覆盖） |

> 统一保留：**AIOS Cleanup (Production)**（02:00，isolated，有归档逻辑）

---

### 合并组 C：日报类（4 → 1）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 建议动作 |
|--------|----------|--------|----------|----------|
| AIOS 每日简报+反思 | 09:15，insight.py + reflect.py + 卦象分析，发 Telegram | 多个脚本 | Telegram 日报 | **废弃**（被 Production 覆盖，但卦象分析需确认是否并入） |
| AIOS Daily Report - 09:15 | 09:15，run_pattern_analysis.py --telegram | agent_system | Telegram 日报 | **废弃**（与上条同时间同产物） |
| Analyst Agent 每日简报 | 09:30，insight.py + trend.py + score，5 Phase 分析 | 多个脚本 | Telegram 日报 | **待观察**（Phase 4 触发 Debugger/Optimizer 是独有逻辑） |
| Agent 定时任务检查 | 09:00，auto_dispatcher.py cron 触发 | auto_dispatcher.py | 触发其他任务 | **待观察**（不确定是否是其他任务的触发器） |

> 统一保留：**AIOS Daily Report (Production)**（09:00）  
> 注意：卦象分析（run_pattern_analysis.py）需要并入 Production 日报的 prompt 中

---

### 合并组 D：健康检查类（4 → 1）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 建议动作 |
|--------|----------|--------|----------|----------|
| AIOS系统健康检查 | 每小时，DataCollector.get_system_health() | data_collector | 打印健康度 | **废弃**（无输出产物，被 Production 覆盖） |
| AIOS健康监控 | 每小时，health_monitor_agent.py | agent_system | 不明 | **废弃**（被 Production 覆盖） |
| AIOS Health Monitor | 每小时，agents/health_monitor.py | agent_system | 不明 | **废弃**（被 Production 覆盖） |
| AIOS 健康监控（cron 版） | 每 10 分钟，health_monitor_agent.py | agent_system | 不明 | **废弃**（被 Production 覆盖） |

> 统一保留：**AIOS Health Check (Production)**（每 6 小时，isolated，有告警逻辑）

---

### 合并组 E：学习类（4 → 1）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 建议动作 |
|--------|----------|--------|----------|----------|
| AIOS 学习 Agent | 04:00，learner_agent.py | agent_system | 不明 | **废弃**（被 Production 覆盖） |
| AIOS每周学习 | 每周一 09:00，"搜索 GitHub 最新 AIOS 相关项目"（无具体逻辑） | 不明 | 不明 | **废弃**（空壳任务，被 Production 覆盖） |
| 每晚学习总结 | 22:00，回顾知识点/更新 MEMORY.md | 当天学习内容 | MEMORY.md 更新 | **待观察**（更新 MEMORY.md 是独有产物，Production 不做这件事） |

> 统一保留：**AIOS Learning (Production)**（08:50，isolated，有完整学习 Agent 列表）

---

### 合并组 F：优化类（3 → 1）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 建议动作 |
|--------|----------|--------|----------|----------|
| AIOS 优化 Agent | 02:00，optimizer_agent.py | agent_system | 不明 | **废弃**（被 Optimizer Agent 资源优化覆盖） |
| AIOS Performance Optimizer (Weekly) | 每周，performance_optimizer.py | agent_system | 不明 | **待观察**（周级别优化 vs 每 2 小时优化，粒度不同） |
| Optimizer Agent 资源优化 | 每 2 小时，resource_optimizer.py，内存/缓存/CPU | 系统资源 | 优化操作 Telegram | **保留**（主优化入口） |

---

### 合并组 G：通知管理类（2 → 1）

| 任务名 | 当前作用 | 输入源 | 输出产物 | 建议动作 |
|--------|----------|--------|----------|----------|
| Notification Manager Agent 通知管理 | 每小时，聚合通知/优先级分级/免打扰 | Agent 输出 | Telegram 汇总 | **待观察**（逻辑更完整，但与 Hourly 版本重叠） |
| Notification Manager (Hourly) | 每小时，agents/notification_manager.py | agent_system | 不明 | **废弃**（被上条覆盖，且无具体逻辑描述） |

---

## 🔴 三、废弃候选（deprecated candidate，不立即删）

以下任务标记为 `deprecated candidate`，等待确认后再删：

| 任务名 | 废弃原因 | 风险等级 |
|--------|----------|----------|
| 每日数据备份 | 被 AIOS Backup (Production) 覆盖，时间重叠，逻辑更弱 | 低 |
| AIOS每日备份 | 空壳任务，prompt 只有"备份 AIOS 重要数据"，无具体逻辑 | 低 |
| Backup Agent 数据备份 | 被 AIOS Backup (Production) 覆盖 | 低 |
| 每日电脑清理（08:30） | 被 AIOS Cleanup (Production) 覆盖 | 低 |
| 每日自动清理电脑 | 被 AIOS Cleanup (Production) 覆盖 | 低 |
| AIOS Daily Report - 09:15 | 与"AIOS 每日简报+反思"同时间同产物，且被 Production 覆盖 | 低 |
| AIOS系统健康检查 | 无输出产物，只打印，被 Production 覆盖 | 低 |
| AIOS健康监控（卦象） | 每小时跑 test_with_real_data.py，无产物，被 Production 覆盖 | 低 |
| AIOS Health Monitor | 被 Production 覆盖 | 低 |
| AIOS 健康监控（10分钟版） | 被 Production 覆盖，频率过高 | 低 |
| AIOS 学习 Agent | 被 AIOS Learning (Production) 覆盖 | 低 |
| AIOS每周学习 | 空壳任务，被 Production 覆盖 | 低 |
| AIOS 优化 Agent | 被 Optimizer Agent 资源优化覆盖 | 低 |
| Notification Manager (Hourly) | 被 Notification Manager Agent 覆盖 | 低 |
| Security Agent 安全审计 | 与 AIOS 安全守护（每小时）重叠，读同一源，产同类结果 | 中 |
| install proactive-agent and gog | 一次性安装任务，已过期（2026-03-02 13:43），从未执行 | 低 |
| Day3 Observation Report | 一次性任务（2026-03-05 14:00 UTC），已过期 | 低 |
| ClawdHub install retry | 已禁用，已完成，无需保留 | 低 |
| Superpowers Claude Handler | 已禁用，轮询 flag 文件，1秒一次，设计有问题 | 低 |
| Agent 论文研究 | 已禁用，被 AIOS Learning (Production) 覆盖 | 低 |

---

## 🔵 四、待观察（先挂 24h 观察标签，不动）

| 任务名 | 待观察原因 | 风险等级 |
|--------|------------|----------|
| Analyst Agent 每日简报 | Phase 4 有独有逻辑：触发 Debugger/Optimizer Agent，不确定 Production 日报是否覆盖这个行为 | 中 |
| 每晚学习总结 | 更新 MEMORY.md 是独有产物，Production 学习 Agent 不做这件事；但 22:00 与 Daily Observation 同时间，需确认是否冲突 | 中 |
| Agent 定时任务检查 | auto_dispatcher.py cron 触发，不确定是否是其他任务的触发器，误删可能影响 dispatcher 主流程 | 高 |
| AIOS 安全守护（每小时） | 与 Security Agent 安全审计（每日 04:00）重叠，但频率不同；安全类任务不确定是否需要高频 | 中 |
| Anomaly Detector 异常检测 | 每 10 分钟，与 Self-Healing Agent（每 15 分钟）功能接近，但 Anomaly 有自动熔断逻辑，不确定是否独立职责 | 中 |
| Task Scheduler Agent 任务调度 | 每 30 分钟，负载均衡/任务去重/依赖管理，与 Heartbeat 的 spawn_pending 处理有潜在重叠，需确认边界 | 高 |
| feedback_monitor_real | 每 30 分钟，feedback_monitor.py real 模式，不确定是否与 Feedback Collector (Daily) 重叠 | 中 |
| AIOS Performance Optimizer (Weekly) | 周级别优化 vs Optimizer Agent 每 2 小时，粒度不同，可能是互补而非重叠 | 低 |
| 每周健康周报 | 每周一 09:30，weekly_health.py，与 AIOS Health Check (Production) 不同粒度（周报 vs 6小时检查），可能互补 | 低 |
| AIOS Cost Guardian (Daily) | 每日，cost_guardian.py，不确定是否与 Production Daily Report 的成本摘要重叠 | 低 |
| Data Pipeline (Daily) | 每日，data_pipeline.py，不确定具体职责，可能是数据流水线的唯一入口 | 中 |
| Feedback Collector (Daily) | 每日，feedback_collector.py，不确定是否与 feedback_monitor_real 重叠 | 中 |
| Resource Monitor (Hourly) | 每小时，resource_monitor.py，与 Optimizer Agent（每 2 小时）和 Self-Healing Agent（每 15 分钟）有重叠嫌疑 | 中 |
| AIOS Cost Guardian (Daily) | 每日，cost_guardian.py，不确定是否与 Production Daily Report 的成本摘要重叠 | 低 |
| 意识观察日志自动追踪 | 23:59，aios.py monitor track consciousness，不确定是否是独立职责还是与 Daily Observation 重叠 | 中 |
| meta_meta_observation_2359 | 23:59，meta_meta_observation_recorder.py，与"意识观察日志"同时间，不确定是否重叠 | 中 |
| AIOS 产品化打磨 | 每日 10:00，开源标准审视代码，与"周末 AIOS 大版本开发"和"AIOS 功能开发+测试"有重叠 | 中 |
| AIOS 性能优化 + 文档 | 每日 14:00，性能分析+文档，与 Optimizer Agent 和 Reviewer 有重叠 | 中 |
| AIOS 功能开发 + 测试 | 每日 16:00，功能开发+测试，与"AIOS 产品化打磨"重叠 | 中 |
| AIOS 竞品分析 + 差异化 | 每日 20:00，竞品分析，与 AIOS Learning (Production) 有重叠 | 低 |
| Agent 最佳实践 | 每日 11:00，最佳实践学习，与 AIOS Learning (Production) 有重叠 | 低 |
| 周末 AIOS 大版本开发 | 每周六 10:00，大版本开发，与"AIOS 产品化打磨"和"AIOS 功能开发+测试"有重叠 | 中 |

---

## 📊 汇总统计

| 分类 | 数量 |
|------|------|
| 保留 | 19 |
| 合并后废弃 | 14 |
| 废弃候选（deprecated candidate） | 20 |
| 待观察（24h） | 22 |
| **总计** | **52（含已禁用 5 条）** |

---

## ⚠️ 高优先级确认项（动手前必须确认）

1. **Agent 定时任务检查**（auto_dispatcher.py）：是否是其他任务的触发器？误删风险高。
2. **Task Scheduler Agent**：与 Heartbeat spawn_pending 的边界在哪里？
3. **Analyst Agent 每日简报**：Phase 4 触发 Debugger/Optimizer 的逻辑，Production 日报有没有？
4. **AIOS 每日简报+反思**：卦象分析（run_pattern_analysis.py）是否已并入 Production 日报？
5. **意识观察日志 + meta_meta_observation_2359**：23:59 两个任务同时跑，是否互相依赖？

---

*草案 v0 - 只分类，不删除*  
*下一步：珊瑚海确认后，执行合并/废弃操作*
