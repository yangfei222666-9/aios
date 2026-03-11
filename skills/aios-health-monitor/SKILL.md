---
name: aios-health-monitor
version: 1.0.0
description: 太极OS 健康监控 + 可观测性报告。不仅看状态，还能给诊断和行动建议。把"看一眼"升级为"看完能诊断"。
---

# AIOS Health Monitor

## 目标

把 health-monitor 和 observability-report 合一：不仅看状态，还能给诊断和行动建议。

不是缺"看一眼"，是缺"看完能诊断"。

## 输入

| 参数 | 必需 | 说明 |
|------|------|------|
| `--level` | ❌ | 报告层级：L1 / L2 / L3 / L4 / all（默认 all） |
| `--format` | ❌ | 输出格式：md / json / both（默认 both） |
| `--output` | ❌ | 输出目录（默认 `output/`） |
| `--quiet` | ❌ | 静默模式，只输出诊断结论 |

### 数据源（自动读取）

- `agents.json` — Agent 注册信息和状态
- `task_queue.jsonl` — 任务队列
- `task_executions.jsonl` — 任务执行历史
- `heartbeat_stats.json` — 心跳统计
- `alerts.jsonl` — 告警记录
- `backup_metadata.json` — 备份元数据

## 输出

| 文件 | 说明 |
|------|------|
| `health_report.md` | 完整健康报告（人类可读） |
| `runtime.json` | L1 运行时状态 |
| `incidents.json` | L2 事件记录 |
| `trends.json` | L3 趋势分析 |
| `diagnosis.json` | L4 诊断结论 |

## 四层报告模型

### L1 Runtime — 当前运行状态

- Agent 总数 / 可调度数 / 活跃数
- Shadow / Disabled 正确标记（不误报为 Active）
- 任务队列深度（pending / running / completed / failed）
- 最近心跳时间和状态
- 备份最近时间和状态

### L2 Incident — 事件记录

- 最近 N 个失败事件
- 告警列表（按严重程度排序）
- 连续失败的 Agent / Skill

### L3 Trend — 趋势分析

- 任务成功率趋势（24h / 7d / 30d）
- Agent 活跃率变化
- 错误类型分布变化
- 队列积压趋势

### L4 Diagnosis — 诊断结论

固定诊断句式：

```
当前最弱链路：[具体模块/Agent/链路]
最该优先修复：[具体问题]
修完后预期改善：[预期效果]
```

## 关键约束

1. Shadow/Disabled 不再误报为 Active/Sleeping
2. Active 比例只按可调度 Agent 计算
3. 同一 Agent 的状态、分桶、建议三者一致

## 使用方式

### 命令行

```bash
cd C:\Users\A\.openclaw\workspace\skills\aios-health-monitor
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 monitor.py
```

### 只看诊断结论

```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 monitor.py --quiet
```

### 在 OpenClaw 中使用

当用户说"系统状态怎么样"或"健康检查"时：

1. 运行 monitor.py 收集所有数据源
2. 生成四层报告
3. 输出诊断结论和行动建议

## MVP 最小范围

先实现四层报告：L1 Runtime、L2 Incident、L3 Trend、L4 Diagnosis。先不做 dashboard。

## 验收标准

1. Shadow/Disabled 不再误报为 Active/Sleeping
2. Active 比例只按可调度 Agent 计算
3. 报告能自动产出"当前最弱链路 / 最优先修复项 / 预期改善"
4. 同一 Agent 的状态、分桶、建议三者一致
5. 输出可直接用于运维决策

## 与其他技能的关系

```
aios-health-monitor → agent-performance-analyzer
backup-restore-manager ↔ aios-health-monitor
```

本技能是**运营主链**的起点，诊断结果可供 agent-performance-analyzer 深入分析。

---

**版本：** 1.0.0
**创建者：** 小九 + 珊瑚海
**最后更新：** 2026-03-11
