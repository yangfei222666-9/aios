---
name: lesson-extractor
version: 1.0.0
description: 把失败事件、状态失真、恢复演练结果，沉淀成可复用 lesson。能把 1 个 incident 转成结构化 lesson 并写回 lessons.json。
---

# Lesson Extractor

## 目标

把失败事件、状态失真、恢复演练结果，沉淀成可复用 lesson。

没有它，失败不会沉淀成经验。

## 输入

- pattern_clusters.json（来自 pattern-detector）
- diagnosis.json（来自 aios-health-monitor）
- agent_scorecard.json（来自 agent-performance-analyzer）
- restore_drill_report.md（来自 backup-restore-manager）
- 人工总结（可选）

## 使用方式

```bash
cd C:\Users\A\.openclaw\workspace\skills\lesson-extractor
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 extractor.py
```

### 从 pattern-detector 结果提取

```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 extractor.py --source ..\pattern-detector\output\pattern_clusters.json
```

## 输出

| 文件 | 说明 |
|------|------|
| lessons_new.json | 新提取的 lesson 条目 |
| lesson_summary.md | 人类可读摘要 |

## Lesson 结构

```json
{
  "lesson_id": "les-20260311-001",
  "event_type": "timeout",
  "trigger": "coder-dispatcher 连续超时",
  "false_assumption": "默认 60s 超时足够所有任务",
  "correct_model": "复杂代码任务需要 120s+",
  "action_taken": "增加超时到 120s",
  "preventive_rule": "复杂任务自动使用 2x 超时",
  "confidence": "high"
}
```

## 验收标准

1. 能把 1 个 incident 转成结构化 lesson
2. lesson 至少包含"触发条件 / 误判点 / 正确判定 / 后续规则"
3. 能写回 lessons.json
4. 后续 health report / diagnosis 可引用 lesson
5. 避免生成空泛总结

---

**版本：** 1.0.0
**最后更新：** 2026-03-11
