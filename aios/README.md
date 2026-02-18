# AIOS — 个人 AI 操作系统

> 事件驱动，自学习，人人可用

## 理念

一切皆事件。所有操作、纠正、错误、教训都流入 `events.jsonl`，这是唯一事实来源。学习层从事件流中自动分析模式、沉淀教训、生成建议。

## 结构

```
aios/
  config.yaml           # 配置
  events/
    events.jsonl         # 所有事件流水（唯一事实来源）
  learning/
    lessons.md           # 自动沉淀：错误→教训
    suggestions.json     # 机器建议（可人工审核）
    daily_report.md      # 每日学习报告
  scripts/
    log_event.py         # 追加事件
    analyze.py           # 分析并产出建议/报告
    apply_suggestions.py # 应用建议（建议先人工审）
```

## 快速开始

```bash
# 记录事件
python scripts/log_event.py match aram "搜索: 卡特 → 卡特琳娜"

# 记录纠正
python scripts/log_event.py correction aram "卡特→卡莎" --data '{"input":"卡特","correct_target":"卡莎"}'

# 生成每日报告
python scripts/analyze.py report

# 查看建议
python scripts/analyze.py suggestions

# 生成教训
python scripts/analyze.py lessons

# 审核建议
python scripts/apply_suggestions.py show

# 自动应用高置信度建议
python scripts/apply_suggestions.py auto
```

## 设计原则

1. **事件即真相** — events.jsonl 是唯一事实来源，其他文件都是派生
2. **人工优先** — 建议默认需人工审核，auto_apply 仅处理高置信度
3. **可追溯** — 每次应用都记录事件，可回溯
4. **模块化** — ARAM、autolearn 等模块通过事件流对接

## 版本

- v0.1.0 — 骨架：事件流 + 分析 + 建议 + 报告
