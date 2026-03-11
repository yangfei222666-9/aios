---
name: agent-performance-analyzer
version: 1.0.0
description: 从"Agent 在不在"升级到"Agent 是否有价值、是否退化、是否该保持待命"。输出运营判断和建议动作。
---

# Agent Performance Analyzer

## 目标

从"Agent 在不在"升级到"Agent 是否有价值、是否退化、是否该保持待命"。

## 五类判断

| 类型 | 说明 |
|------|------|
| active_routable | 活跃且可路由，正常工作 |
| schedulable_idle | 可调度但从未触发，待命中 |
| standby_emergency | 备用应急，低频但有价值 |
| shadow | 影子模式，不参与调度 |
| degraded | 退化，连续异常需关注 |

## 使用方式

```bash
cd C:\Users\A\.openclaw\workspace\skills\agent-performance-analyzer
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 analyzer.py
```

## 输出

| 文件 | 说明 |
|------|------|
| agent_performance_report.md | 完整性能报告 |
| agent_scorecard.json | 每个 Agent 的评分卡 |
| underused_agents.json | 高价值低使用 Agent |
| degraded_agents.json | 退化 Agent 列表 |

## 验收标准

1. 能区分"未触发待命"和"真退化"
2. 能识别高价值低使用 Agent
3. 能识别连续异常 Agent
4. 不把 standby/shadow 误判成故障
5. 能给出保留/激活/降级/禁用建议

---

**版本：** 1.0.0
**最后更新：** 2026-03-11
