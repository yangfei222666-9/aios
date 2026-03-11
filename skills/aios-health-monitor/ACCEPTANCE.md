# aios-health-monitor — Acceptance Report

**验收时间：** 2026-03-11 07:39
**版本：** v1.0.0

## 真实输入样本

```
默认参数，自动读取 DATA_DIR 下所有数据源
```

数据量：30 个 Agent、211 条执行记录、167 条告警。

## 真实输出样本

| 文件 | 大小 | 内容摘要 |
|------|------|----------|
| health_report.md | 完整 | 四层报告（L1-L4） |
| runtime.json | 完整 | Agent 分桶 + 队列状态 |
| incidents.json | 完整 | 1 个失败事件 + 告警列表 |
| trends.json | 完整 | 24h/7d/30d 成功率趋势 |
| diagnosis.json | 完整 | 诊断结论 + 健康分数 |

### 关键输出

健康分数：100/100 (GOOD)

Agent 分桶（关键验证点）：
- active_routable: 4（coder-dispatcher, analyst-dispatcher, monitor-dispatcher, Documentation_Writer）
- shadow: 14（正确识别，未误报为 Active）
- disabled: 3（正确识别，未误报为 Active）
- idle_never_triggered: 9（正确区分为"待命"）

可调度 Agent 计算：13（排除 shadow + disabled）
活跃率：30.8%（4/13，只按可调度计算）

诊断结论：
- 当前最弱链路：未发现明显弱链路
- 最该优先修复：当前无需紧急修复
- 修完后预期改善：系统运行正常

## 验收结论

| 验收项 | 结果 |
|--------|------|
| 1. Shadow/Disabled 不再误报为 Active/Sleeping | ✅ 通过（14 shadow + 3 disabled 正确分桶） |
| 2. Active 比例只按可调度 Agent 计算 | ✅ 通过（4/13 = 30.8%） |
| 3. 报告能自动产出诊断三句话 | ✅ 通过 |
| 4. 同一 Agent 的状态、分桶、建议三者一致 | ✅ 通过 |
| 5. 输出可直接用于运维决策 | ✅ 通过（JSON + MD 双格式） |

**总结：** 全部 5 项验收标准通过。可用于生产。
