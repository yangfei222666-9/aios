---
name: pattern-detector
version: 1.0.0
description: 从零散失败、重复现象、长期日志里识别"模式"，为 lesson 和 diagnosis 提供基础。把"零散问题"变成"重复模式"。
---

# Pattern Detector

## 目标

从零散失败、重复现象、长期日志里识别"模式"，为 lesson 和 diagnosis 提供基础。

这是学习闭环的核心：能把"零散问题"变成"重复模式"。

## 输入

| 参数 | 必需 | 说明 |
|------|------|------|
| `--source` | ❌ | 数据源目录（默认 `aios/agent_system/data/`） |
| `--window` | ❌ | 时间窗口：24h / 7d / 30d（默认 7d） |
| `--types` | ❌ | 模式类型过滤（默认 all） |
| `--output` | ❌ | 输出目录（默认 `output/`） |
| `--top` | ❌ | 输出 Top N 模式（默认 3） |

### 数据源

- `task_executions.jsonl` — 任务执行记录
- `alerts.jsonl` — 告警记录
- `heartbeat_stats.json` — 心跳统计
- `lessons.json` — 已有经验
- `agents.json` — Agent 状态

## 输出

| 文件 | 说明 |
|------|------|
| `pattern_clusters.json` | 聚类后的模式列表 |
| `top_patterns.md` | Top N 模式报告（人类可读） |
| `candidate_root_causes.json` | 候选根因分析 |

## 模式字段结构

```json
{
  "pattern_id": "pat-timeout-001",
  "pattern_type": "timeout",
  "affected_agents": ["coder-dispatcher"],
  "affected_skills": ["api-testing-skill"],
  "frequency": 12,
  "first_seen": "2026-03-01T10:00:00",
  "last_seen": "2026-03-10T15:30:00",
  "evidence": ["task-xxx failed: timeout after 60s", "task-yyy failed: timeout after 60s"],
  "impact_level": "high",
  "candidate_fix_direction": "增加超时时间或拆分任务"
}
```

## MVP 最小范围

第一版只识别 4 类模式：

| 类型 | 说明 | 识别方式 |
|------|------|----------|
| `timeout` | 超时失败 | error 包含 timeout / timed out |
| `network_error` | 网络错误 | error 包含 network / connection / ECONNREFUSED |
| `resource_exhausted` | 资源耗尽 | error 包含 memory / disk / resource |
| `agent_idle` | Agent 从未触发 | 无执行记录且非 shadow/disabled |

## 使用方式

### 命令行

```bash
cd C:\Users\A\.openclaw\workspace\skills\pattern-detector
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 detector.py
```

### 指定时间窗口

```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 detector.py --window 24h
```

### 在 OpenClaw 中使用

当用户说"检查最近有什么重复问题"或"分析失败模式"时：

1. 运行 detector.py 扫描数据源
2. 聚类识别重复模式
3. 输出 Top N 模式及优先级
4. 结果可供 lesson-extractor 直接消费

## 验收标准

1. ✅ 能从最近 N 条记录里聚类出重复模式
2. ✅ 每个模式有频次、影响范围、样本证据
3. ✅ 能区分"真故障"和"正常待命"
4. ✅ 能输出 Top 3 模式及优先级
5. ✅ 结果可供 lesson-extractor 直接消费

## 与其他技能的关系

```
github-repo-analyzer → pattern-detector → lesson-extractor
```

本技能是**学习闭环**的核心，上游接收执行数据，下游输出给 lesson-extractor。

---

**版本：** 1.0.0
**创建者：** 小九 + 珊瑚海
**最后更新：** 2026-03-11
