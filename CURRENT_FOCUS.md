# CURRENT_FOCUS.md - 当前阶段执行焦点

> 对应里程碑：第一阶段 — 把 AIOS 做成可靠的个人系统

最后更新：2026-03-08

---

## 当前最该做的事

### P0：修复执行链路（让系统真正跑起来）

1. **task_executions.jsonl 字段规范化**
   - 现状：5 条记录，缺 agent_id / status / description 等关键字段
   - 目标：统一 schema，让 Lifecycle Engine 和所有下游模块能正确读取
   - 涉及：task_executor.py、heartbeat_v5.py

2. **Lifecycle Engine 接入 Heartbeat**
   - 现状：agent_lifecycle_engine.py 已写好，测试全通过，但未接入
   - 目标：每次心跳自动评估 Agent 三态，写回 agents.json
   - 涉及：heartbeat_v5.py 或 heartbeat_v6.py

3. **10 个 Active Agent 从未执行**
   - 现状：Bug_Hunter / Error_Analyzer / GitHub_Code_Reader 等 completed=0
   - 原因：注册了但没有任务触发它们
   - 目标：至少让每个 Active Agent 跑一次真实任务，产生真实数据

### P1：补齐核心能力

4. **任务提交入口**
   - 现状：task_queue.jsonl 为空，没有新任务进来
   - 目标：建立稳定的任务提交机制（手动 + 自动触发）

5. **统计同步**
   - 现状：agents.json 的 stats 与 task_executions.jsonl 不同步
   - 目标：sync_agent_stats.py 每次心跳自动跑

---

## 不做的事（本阶段）

- 不扩更多 Agent（先让现有的跑起来）
- 不做 Dashboard 美化
- 不做新的卦象/评分系统
- 不做纯文档工作

---

## 验收标准

本阶段完成的标志：
- [ ] task_executions.jsonl 有规范化的真实执行记录（≥20 条）
- [ ] Lifecycle Engine 在心跳中自动运行
- [ ] 所有 Active Agent 至少执行过 1 次
- [ ] agents.json 的 stats 与真实执行数据一致
- [ ] 任务队列有稳定的输入来源
