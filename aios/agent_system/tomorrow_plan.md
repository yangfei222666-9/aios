# 明天执行计划 - 3 Agent 首次真实闭环

**日期：** 2026-03-09
**目标：** 让 3 个 Agent 真正留下第一批可信执行样本

---

## 执行顺序（写死）

1. **GitHub_Researcher** → 2. **Bug_Hunter** → 3. **Error_Analyzer**

逐个跑，一个跑完验收通过再跑下一个。不并行。

---

## 验收模板

### GitHub_Researcher
- [ ] 被触发（sessions_spawn 成功调用）
- [ ] 真执行（sub-agent 实际运行，有 web_search/web_fetch 调用）
- [ ] task_executions_v2.jsonl 有记录（含 timestamp, task_id, result）
- [ ] agents.json stats 增长（tasks_total +1, tasks_completed +1）
- [ ] Lifecycle 变化（production_ready: false → 有首次执行记录）

### Bug_Hunter
- [ ] 被触发（sessions_spawn 成功调用）
- [ ] 真执行（sub-agent 实际运行，有 exec/read 调用）
- [ ] task_executions_v2.jsonl 有记录（含 timestamp, task_id, result）
- [ ] agents.json stats 增长（tasks_total +1, tasks_completed +1）
- [ ] Lifecycle 变化（production_ready: false → 有首次执行记录）

### Error_Analyzer
- [ ] 被触发（sessions_spawn 成功调用）
- [ ] 真执行（sub-agent 实际运行，有 read/exec 调用）
- [ ] task_executions_v2.jsonl 有记录（含 timestamp, task_id, result）
- [ ] agents.json stats 增长（tasks_total +1, tasks_completed +1）
- [ ] Lifecycle 变化（production_ready: false → 有首次执行记录）

---

## 当前状态快照（2026-03-08 14:27）

### agents.json
| Agent | tasks_total | tasks_completed | tasks_failed | production_ready |
|-------|-------------|-----------------|--------------|------------------|
| GitHub_Researcher | 0 | 0 | 0 | false |
| Bug_Hunter | 0 | 0 | 0 | false |
| Error_Analyzer | 0 | 0 | 0 | false |

### 触发条件
| Agent | schedule | interval | model | tools |
|-------|----------|----------|-------|-------|
| GitHub_Researcher | daily | 24h | claude-sonnet-4-6 | web_search, web_fetch |
| Bug_Hunter | daily | 24h | claude-sonnet-4-6 | exec, read, write |
| Error_Analyzer | daily | 24h | claude-sonnet-4-6 | read, exec |

### 执行账本
- `task_executions.jsonl`：有历史记录（旧格式），最后一条 2026-03-08 09:00
- `task_executions_v2.jsonl`：**不存在**（明天首次创建）
- `lifecycle_state.json`：**不存在**（明天首次创建）
- `heartbeat_stats.json`：**不存在**

### selflearn-state.json
- 上次激活：2026-03-03
- 已激活过：GitHub_Researcher, Architecture_Analyst, Code_Reviewer
- 但 stats 全为 0 → 说明激活了但没有真实执行闭环

---

## 注意事项

1. task_executions_v2.jsonl 需要在执行时创建（新格式）
2. 执行后必须回写 agents.json 的 stats
3. 每个 Agent 跑完后立刻对照验收模板逐项检查
4. 不改 Lifecycle 规则，不开 Judge，不做 Hands
