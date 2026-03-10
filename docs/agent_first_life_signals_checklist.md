# Agent 首次生命迹象验收 Checklist

> 版本: v1.0 | 日期: 2026-03-08 | 验收日: 2026-03-09

## 验收标准

每个 Agent 必须满足以下 6 项，缺一不算通过：

| # | 检查项 | 说明 | 通过标准 |
|---|--------|------|----------|
| 1 | **Trigger** | 有明确的触发源 | 能说清"是什么触发了这次执行" |
| 2 | **Input** | 有真实输入 | 不是硬编码 mock 数据，是真实环境数据 |
| 3 | **Output** | 有可验证产出 | 产出内容可被人类阅读和判断质量 |
| 4 | **Duration** | 有执行时长记录 | start_time / end_time / duration_ms 三项齐全 |
| 5 | **Outcome** | 有明确结果状态 | success / partial / failed 三选一，不能是 unknown |
| 6 | **Writeback** | 有可追溯回写 | 结果写入了指定文件，可事后查证 |

## 验收的 3 个 Agent

| Agent | Trigger | Input | Expected Output | Writeback |
|-------|---------|-------|-----------------|-----------|
| **GitHub_Researcher** | 心跳/cron 定时触发 | GitHub API 搜索关键词: AIOS, Agent System, Multi-Agent, Self-Improving | 3-5 个值得关注的项目摘要（名称、Star、核心价值、与 AIOS 的关系） | `memory/github_research/YYYY-MM-DD.md` + `agent_execution_record.jsonl` |
| **Error_Analyzer** | 心跳/cron 定时触发 | `aios/agent_system/` 下的日志文件（heartbeat.log, lessons.json, task_executions.jsonl） | 错误分类统计 + Top 3 根因分析 + 修复建议 | `memory/error_analysis/YYYY-MM-DD.md` + `agent_execution_record.jsonl` |
| **Code_Reviewer** | 心跳/cron 定时触发 | `aios/agent_system/` 下的核心 .py 文件（首次选 3-5 个高频使用模块） | 代码质量评估 + 问题清单（bug/设计债/边界问题） + 改进建议 | `memory/code_review/YYYY-MM-DD.md` + `agent_execution_record.jsonl` |

## 判定规则

- 3 个 Agent 全部 6 项通过 → ✅ 验收成功，切 Phase B
- 2 个通过 + 1 个 partial → ⚠️ 修复后重跑
- 其他情况 → ❌ 排查问题，当天修复

## 不接受的"通过"

- ❌ 只改了文档没真实执行
- ❌ 输出是硬编码的模板文字
- ❌ duration 为 0 或缺失
- ❌ outcome 为 unknown
- ❌ writeback 目标文件不存在或为空
