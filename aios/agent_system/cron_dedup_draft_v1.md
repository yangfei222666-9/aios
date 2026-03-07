# Cron 去重清单草案 v1
> 生成时间：2026-03-07  
> 总任务数：52 条（含已禁用 5 条）  
> 原则：只分类，不删除。deprecated candidate 不立即动。

---

## ⚠️ 统计口径说明

**以下为标签式分类，不是互斥分桶；同一 cron 可同时属于待观察 / 合并候选 / 废弃候选。**

汇总表中的数字是"标签计数"，不是"任务总数"，加起来超过 52 是正常的。

---

## 🎯 总原则

**同类职责优先保留 Production 版，旧版默认降为合并候选或废弃候选。**

**判断主线：先判断它会不会影响系统行为，再判断它是不是重复。**

---

## 字段说明

| 字段 | 含义 |
|------|------|
| 任务名 | cron 任务名称 |
| 当前作用 | 实际做什么 |
| 输入源 | 读哪里的数据 |
| 输出产物 | 写/发什么 |
| 副作用 | 写文件/创建任务/发通知/改状态 |
| 唯一入口 | 是否是该职责的唯一调度入口 |
| 删除风险 | 低/中/高/极高 |
| 建议动作 | 保留/合并/废弃/待观察 |

---

## 🟢 一、保留（唯一职责 / 核心主链路 / 唯一入口）

| 任务名 | 当前作用 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| AIOS Heartbeat (Production) | 主心跳，处理 spawn_pending，驱动整个 AIOS 主循环 | 创建任务/改状态 | yes | 极高 | **保留** |
| AIOS Alert Dispatcher | 唯一的 alerts.jsonl → Telegram 发送入口 | 发通知 | yes | 高 | **保留** |
| API 端点故障恢复监控 | 每 5 分钟轮询 API 健康，唯一 api_monitor.py 执行入口 | 写文件 | yes | 高 | **保留** |
| AIOS Data Flush (21:59) | 每晚 21:59 刷写数据，是 Daily Observation 的前置依赖 | 写文件 | yes | 高 | **保留** |
| AIOS Daily Observation (22:00) | 每晚 22:00 生成 observation 行，追加 observation_log.md，发给珊瑚海 | 写文件/发通知 | yes | 高 | **保留** |
| AIOS Backup (Production) | 生产级备份，有完整验证逻辑，保留 30 天 | 写文件 | yes | 高 | **保留** |
| AIOS Cleanup (Production) | 生产级清理，有归档逻辑 | 写文件 | yes | 高 | **保留** |
| AIOS Learning (Production) | 统一学习入口，运行 GitHub 研究/架构分析/代码审查等 | 写文件 | yes | 中 | **保留** |
| AIOS Daily Report (Production) | 生产级日报，任务完成/Agent性能/成本/改进建议 | 写文件/发通知 | yes | 中 | **保留** |
| AIOS Health Check (Production) | 每 6 小时健康检查，health score < 60 告警 | 发通知 | yes | 中 | **保留** |
| Self-Healing Agent 自愈修复 | 每 15 分钟，唯一自愈执行入口（进程崩溃/内存泄漏/磁盘满） | 改状态/写文件 | yes | 中 | **保留** |
| Reviewer 代码审查 | 每周五 17:00，唯一代码审查入口，git diff 7天 | 发通知 | yes | 低 | **保留** |
| memory_eval_daily | 每日 09:00，唯一 memory retrieval 评估入口 | 发通知 | yes | 低 | **保留** |
| Meta-Agent 自适应调整 | 每日 05:00，唯一 Meta-Agent 入口，自动调整其他 Agent 频率 | 改状态 | yes | 中 | **保留** |
| Experiment Agent 实验优化 | 每周日 02:00，唯一 A/B 实验入口 | 写文件 | yes | 低 | **保留** |
| Knowledge Graph Agent 知识图谱 | 每日 06:00，唯一知识图谱构建入口 | 写文件 | yes | 低 | **保留** |
| Prediction Agent 预测预警 | 每日 08:00，唯一预测入口（资源/错误/性能退化） | 发通知 | yes | 低 | **保留** |
| 世界杯投注方案提醒 | 一次性提醒，2026-06-01 触发 | 发通知 | yes | 低 | **保留** |
| AIOS 趋势对比（每日09:20） | 每日 09:20，baseline snapshot + 趋势对比，超阈值才推送 | 条件发通知 | yes | 低 | **保留** |

---

## 🟡 二、合并（逻辑相近，可统一）

### 合并组 A：备份类（3 → 1）

**唯一入口：AIOS Backup (Production)（03:00，isolated，有完整验证逻辑）**  
合并后：其他旧备份任务仅保留为实现参考，不再调度。

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| 每日数据备份 | 被 Production 覆盖，时间重叠，逻辑更弱 | 写文件 | no | 低 | **废弃** |
| AIOS每日备份 | 空壳任务，prompt 只有"备份 AIOS 重要数据"，无具体逻辑 | 无 | no | 低 | **废弃** |
| Backup Agent 数据备份 | 被 Production 覆盖 | 写文件 | no | 低 | **废弃** |

---

### 合并组 B：清理类（2 → 1）

**唯一入口：AIOS Cleanup (Production)（02:00，isolated，有归档逻辑）**  
合并后：其他旧清理任务仅保留为实现参考，不再调度。

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| 每日电脑清理（08:30） | 被 Production 覆盖 | 写文件 | no | 低 | **废弃** |
| 每日自动清理电脑 | 被 Production 覆盖 | 写文件 | no | 低 | **废弃** |

---

### 合并组 C：日报类（4 → 1）

**唯一入口：AIOS Daily Report (Production)（09:00）**  
合并后：
- run_pattern_analysis.py（卦象分析）作为 Production 日报的子步骤，不再独立调度
- 其他旧日报任务仅保留为实现参考，不再调度

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| AIOS 每日简报+反思 | 被 Production 覆盖；run_pattern_analysis.py 有 bigua_trigger 但只打印 ALERT，不 spawn/enqueue，可安全并入 | 写文件/发通知 | no | 低 | **废弃**（卦象分析并入 Production） |
| AIOS Daily Report - 09:15 | 与"AIOS 每日简报+反思"同时间同产物，且被 Production 覆盖 | 发通知 | no | 低 | **废弃** |

> 注意：Analyst Agent 每日简报 和 Agent 定时任务检查 已移入待观察，见下方高优先级确认项。

---

### 合并组 D：健康检查类（4 → 1）

**唯一入口：AIOS Health Check (Production)（每 6 小时，isolated，有告警逻辑）**  
合并后：其他旧健康检查任务仅保留为实现参考，不再调度。

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| AIOS系统健康检查 | 无输出产物，只打印，被 Production 覆盖 | 无 | no | 低 | **废弃** |
| AIOS健康监控 | 被 Production 覆盖 | 无 | no | 低 | **废弃** |
| AIOS Health Monitor | 被 Production 覆盖 | 无 | no | 低 | **废弃** |
| AIOS 健康监控（10分钟版） | 被 Production 覆盖，频率过高 | 无 | no | 低 | **废弃** |

---

### 合并组 E：学习类（3 → 1）

**唯一入口：AIOS Learning (Production)（08:50，isolated，有完整学习 Agent 列表）**  
合并后：其他旧学习任务仅保留为实现参考，不再调度。

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| AIOS 学习 Agent | 被 Production 覆盖 | 无 | no | 低 | **废弃** |
| AIOS每周学习 | 空壳任务，被 Production 覆盖 | 无 | no | 低 | **废弃** |
| 每晚学习总结 | 更新 MEMORY.md 是独有产物，但 Production 学习 Agent 可承接 | 写文件 | no | 中 | **待观察**（确认 Production 是否已覆盖 MEMORY.md 更新） |

---

### 合并组 F：优化类（2 → 1）

**唯一入口：Optimizer Agent 资源优化（每 2 小时，resource_optimizer.py）**

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| AIOS 优化 Agent | 被 Optimizer Agent 资源优化覆盖 | 无 | no | 低 | **废弃** |
| AIOS Performance Optimizer (Weekly) | 周级别优化 vs 每 2 小时，粒度不同，可能互补 | 写文件 | no | 低 | **待观察** |

---

### 合并组 G：通知管理类（2 → 1）

**唯一入口：Notification Manager Agent 通知管理（逻辑更完整）**

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 | 建议动作 |
|--------|----------|--------|----------|----------|----------|
| Notification Manager (Hourly) | 被 Notification Manager Agent 覆盖，且无具体逻辑描述 | 无 | no | 低 | **废弃** |

---

## 🔴 三、废弃候选

### A. 可直接废弃候选
满足任一条：已禁用 / 一次性且已过期 / 空壳任务无逻辑 / 被 Production 完全覆盖且无独立输入输出

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 |
|--------|----------|--------|----------|----------|
| ClawdHub install retry | 已禁用，已完成，无需保留 | 无 | no | 低 |
| Superpowers Claude Handler | 已禁用，轮询 flag 文件，1秒一次，设计有问题 | 无 | no | 低 |
| Agent 论文研究 | 已禁用，被 AIOS Learning (Production) 覆盖 | 无 | no | 低 |
| install proactive-agent and gog | 一次性安装任务，已过期（2026-03-02 13:43），从未执行 | 无 | no | 低 |
| Day3 Observation Report | 一次性任务（2026-03-05 14:00 UTC），已过期 | 无 | no | 低 |
| AIOS每日备份 | 空壳任务，prompt 只有"备份 AIOS 重要数据"，无具体逻辑 | 无 | no | 低 |
| AIOS每周学习 | 空壳任务，被 Production 覆盖 | 无 | no | 低 |
| AIOS系统健康检查 | 无输出产物，只打印，被 Production 覆盖 | 无 | no | 低 |
| Notification Manager (Hourly) | 被 Notification Manager Agent 覆盖，且无具体逻辑描述 | 无 | no | 低 |

### B. 观察后废弃候选
旧版本，可能仍有依赖 / 可能承担兼容职责 / 可能仍在写下游文件

| 任务名 | 废弃原因 | 副作用 | 唯一入口 | 删除风险 |
|--------|----------|--------|----------|----------|
| 每日数据备份 | 被 Production 覆盖，但需确认无下游依赖 | 写文件 | no | 低 |
| Backup Agent 数据备份 | 被 Production 覆盖，但需确认无下游依赖 | 写文件 | no | 低 |
| 每日电脑清理（08:30） | 被 Production 覆盖，但需确认无下游依赖 | 写文件 | no | 低 |
| 每日自动清理电脑 | 被 Production 覆盖，但需确认无下游依赖 | 写文件 | no | 低 |
| AIOS Daily Report - 09:15 | 与 Production 同产物，但需确认无独立触发逻辑 | 发通知 | no | 低 |
| AIOS健康监控（卦象） | 每小时跑 test_with_real_data.py，需确认无独立产物 | 无 | no | 低 |
| AIOS Health Monitor | 被 Production 覆盖，需确认无独立产物 | 无 | no | 低 |
| AIOS 健康监控（10分钟版） | 被 Production 覆盖，需确认无独立产物 | 无 | no | 低 |
| AIOS 学习 Agent | 被 Production 覆盖，需确认无独立产物 | 无 | no | 低 |
| AIOS 优化 Agent | 被 Optimizer 覆盖，需确认无独立产物 | 无 | no | 低 |
| Security Agent 安全审计 | 与 AIOS 安全守护（每小时）重叠，但需确认频率差异是否有意义 | 写文件 | no | 中 |

---

## 🔵 四、待观察（先挂观察标签，不动）

### 第一优先级：会创建/分发任务（最危险）

| 任务名 | 待观察原因 | 副作用 | 唯一入口 | 删除风险 |
|--------|------------|--------|----------|----------|
| Agent 定时任务检查（auto_dispatcher.py） | **会 enqueue_task + 写 spawn_requests.jsonl**，是任务创建入口，不是报告任务 | 创建任务/写文件 | 待确认 | 极高 |
| Task Scheduler Agent | **会写 spawn_requests.jsonl**，与 Heartbeat spawn_pending 有潜在重叠，需确认边界 | 创建任务/写文件 | 待确认 | 极高 |

### 第二优先级：会写共享状态/共享文件

| 任务名 | 待观察原因 | 副作用 | 唯一入口 | 删除风险 |
|--------|------------|--------|----------|----------|
| Analyst Agent 每日简报 | analyst_agent.py 无 spawn/trigger 行为，但需确认 Phase 4 触发逻辑是否在其他入口 | 写文件/发通知 | 待确认 | 中 |
| 意识观察日志自动追踪 | consciousness_tracker.py 写 memory/consciousness_log.md，是独立产物 | 写文件 | 待确认 | 中 |
| meta_meta_observation_2359 | meta_meta_observation_recorder.py 读取 consciousness 数据做 meta 分析，与上条有串联关系（情况B） | 写文件 | 待确认 | 中 |
| AIOS 每日简报+反思 | run_pattern_analysis.py 的 bigua_trigger 只打印 ALERT，不 spawn/enqueue，**倾向：并入 Production 日报** | 写文件/发通知 | no | 低 |

### 其余待观察

| 任务名 | 待观察原因 | 副作用 | 唯一入口 | 删除风险 |
|--------|------------|--------|----------|----------|
| 每晚学习总结 | 更新 MEMORY.md 是独有产物，需确认 Production 是否已覆盖 | 写文件 | 待确认 | 中 |
| AIOS 安全守护（每小时） | 与 Security Agent 安全审计（每日 04:00）重叠，但频率不同 | 写文件 | 待确认 | 中 |
| Anomaly Detector 异常检测 | 每 10 分钟，有自动熔断逻辑，不确定是否独立职责 | 改状态 | 待确认 | 中 |
| feedback_monitor_real | 每 30 分钟，不确定是否与 Feedback Collector (Daily) 重叠 | 写文件 | 待确认 | 中 |
| AIOS Performance Optimizer (Weekly) | 周级别优化 vs 每 2 小时，粒度不同，可能互补 | 写文件 | 待确认 | 低 |
| 每周健康周报 | 周报 vs 6小时检查，粒度不同，可能互补 | 发通知 | 待确认 | 低 |
| AIOS Cost Guardian (Daily) | 不确定是否与 Production Daily Report 的成本摘要重叠 | 写文件 | 待确认 | 低 |
| Data Pipeline (Daily) | 不确定具体职责，可能是数据流水线的唯一入口 | 写文件 | 待确认 | 中 |
| Feedback Collector (Daily) | 不确定是否与 feedback_monitor_real 重叠 | 写文件 | 待确认 | 中 |
| Resource Monitor (Hourly) | 与 Optimizer Agent（每 2 小时）和 Self-Healing Agent（每 15 分钟）有重叠嫌疑 | 写文件 | 待确认 | 中 |
| Notification Manager Agent 通知管理 | 逻辑更完整，但与 Hourly 版本重叠，需确认是否为唯一入口 | 发通知 | 待确认 | 中 |
| AIOS 产品化打磨 | 与"周末 AIOS 大版本开发"和"AIOS 功能开发+测试"有重叠 | 写文件 | 待确认 | 中 |
| AIOS 性能优化 + 文档 | 与 Optimizer Agent 和 Reviewer 有重叠 | 写文件 | 待确认 | 中 |
| AIOS 功能开发 + 测试 | 与"AIOS 产品化打磨"重叠 | 写文件 | 待确认 | 中 |
| AIOS 竞品分析 + 差异化 | 与 AIOS Learning (Production) 有重叠 | 写文件 | 待确认 | 低 |
| Agent 最佳实践 | 与 AIOS Learning (Production) 有重叠 | 写文件 | 待确认 | 低 |
| 周末 AIOS 大版本开发 | 与"AIOS 产品化打磨"和"AIOS 功能开发+测试"有重叠 | 写文件 | 待确认 | 中 |

---

## ⚠️ 五、高优先级确认项（动手前必须补全）

### 1. Agent 定时任务检查（auto_dispatcher.py）

```
任务名：Agent 定时任务检查（auto_dispatcher.py）
是否创建任务：✅ 是 — enqueue_task() + 写 spawn_requests.jsonl
是否写共享状态/共享文件：✅ 是 — 写 task_queue.jsonl / spawn_requests.jsonl / agent_dispatch_state.json
是否被其他 cron 依赖：待确认
当前判断：高风险，继续待观察。它是任务创建入口，不是报告任务。
下一步动作：确认是否有其他 cron 依赖它生成的 task_queue.jsonl；确认与 Heartbeat 的 spawn_pending 处理是否重叠
```

---

### 2. Task Scheduler Agent

```
任务名：Task Scheduler Agent
是否创建任务：✅ 是 — 写 spawn_requests.jsonl，直接触发 Agent 执行
是否写共享状态/共享文件：✅ 是 — 写 spawn_requests.jsonl / task_queue.jsonl
是否被其他 cron 依赖：待确认
当前判断：高风险，继续待观察。与 auto_dispatcher 有功能重叠，需画清边界。
下一步动作：确认 Heartbeat vs Task Scheduler 的职责边界（Heartbeat=观察+触发条件判断 / Task Scheduler=排程+延迟执行+时间型分发）；确认两者是否都在写同一个 spawn_requests.jsonl
```

---

### 3. Analyst Agent 每日简报

```
任务名：Analyst Agent 每日简报
是否创建任务：❌ 否 — analyst_agent.py 无 spawn/enqueue/dispatch 行为
是否写共享状态/共享文件：✅ 是 — 写日报文件 + 发 Telegram
是否被其他 cron 依赖：待确认
当前判断：中风险。Phase 4 触发 Debugger/Optimizer 的逻辑未在 analyst_agent.py 中找到，需确认是否在其他入口。
下一步动作：确认 Phase 4 触发逻辑是否存在；如果只是生成文本简报 → 可并入 Production；如果有触发逻辑 → 先保功能，再并表现
```

---

### 4. AIOS 每日简报+反思

```
任务名：AIOS 每日简报+反思（run_pattern_analysis.py）
是否创建任务：❌ 否 — bigua_trigger 只打印 ALERT，不 spawn/enqueue
是否写共享状态/共享文件：✅ 是 — 写 pattern_history.jsonl + 发 Telegram
是否被其他 cron 依赖：待确认
当前判断：倾向并入 Production 日报，不保留独立 cron。bigua_trigger 作为 Production 日报的一个 section。
下一步动作：确认 Production 日报是否已调用 run_pattern_analysis.py；如未调用，将其作为子步骤并入
```

---

### 5. 意识观察日志 + meta_meta_observation_2359

```
任务名：意识观察日志自动追踪（consciousness_tracker.py）
是否创建任务：❌ 否
是否写共享状态/共享文件：✅ 是 — 写 memory/consciousness_log.md
是否被其他 cron 依赖：✅ 是 — meta_meta_observation_recorder.py 读取 consciousness 数据

任务名：meta_meta_observation_2359（meta_meta_observation_recorder.py）
是否创建任务：❌ 否
是否写共享状态/共享文件：✅ 是 — 写 meta_meta 观察记录
是否被其他 cron 依赖：待确认
当前判断：情况B — 串联关系，不是纯重复。consciousness_tracker 先产原料，meta_meta 在其基础上做 meta 分析。不能删前者。
下一步动作：确认 meta_meta_observation_recorder.py 具体读取哪个文件；确认时序依赖是否成立；两者都继续待观察
```

---

## 📊 汇总统计（标签计数）

| 标签 | 数量 | 说明 |
|------|------|------|
| 保留 | 19 | 唯一职责/核心主链路 |
| 合并后废弃（A类可直接废弃） | 9 | 已禁用/过期/空壳/完全覆盖 |
| 合并后废弃（B类观察后废弃） | 11 | 旧版本，需确认无依赖 |
| 待观察 | 22 | 先挂标签，不动 |
| **实际任务总数** | **52** | 含已禁用 5 条 |

> 标签计数加起来超过 52 是正常的，因为同一任务可同时带多个标签。

---

*草案 v1 - 只分类，不删除*  
*下一步：珊瑚海确认 5 条高优先级结果后，执行合并/废弃操作*
