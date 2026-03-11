# pattern-detector — Acceptance Report

**验收时间：** 2026-03-11 07:39
**版本：** v1.0.0

## 真实输入样本

```
--window 30d --source C:\Users\A\.openclaw\workspace\aios\agent_system\data
```

数据量：211 条执行记录、167 条告警、30 个 Agent。

## 真实输出样本

| 文件 | 大小 | 内容摘要 |
|------|------|----------|
| pattern_clusters.json | 完整 | 4 个模式聚类 |
| top_patterns.md | 完整 | Top 3 模式报告 |
| candidate_root_causes.json | 完整 | 3 个候选根因 |

### 发现的 4 个模式

| 模式 | 频次 | 影响 | 涉及 Agent |
|------|------|------|------------|
| resource_exhausted | 63 | critical | analyst, coder, monitor |
| timeout | 16 | critical | analyst, coder |
| network_error | 9 | high | analyst, coder, monitor |
| agent_idle | 9 | low | 9 个从未触发的 Agent |

### idle Agent 列表

Bug_Hunter, Error_Analyzer, GitHub_Code_Reader, GitHub_Researcher, Code_Reviewer, Architecture_Analyst, GitHub_Issue_Tracker, Competitor_Tracker, Quick_Win_Hunter

均为 learning 组，enabled=true, routable=true，但 tasks_total=0。正确区分为"待命"而非"故障"。

## 验收结论

| 验收项 | 结果 |
|--------|------|
| 1. 能从最近 N 条记录里聚类出重复模式 | ✅ 通过（4 个模式） |
| 2. 每个模式有频次、影响范围、样本证据 | ✅ 通过 |
| 3. 能区分"真故障"和"正常待命" | ✅ 通过（idle ≠ 故障） |
| 4. 能输出 Top 3 模式及优先级 | ✅ 通过 |
| 5. 结果可供 lesson-extractor 直接消费 | ✅ 通过（JSON 结构化输出） |

**总结：** 全部 5 项验收标准通过。可用于生产。
