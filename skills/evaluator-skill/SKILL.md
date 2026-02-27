---
name: evaluator-skill
description: Evaluator CLI - 快速评估 AIOS 系统健康度、Agent 性能、任务质量
version: 1.0.0
author: 小九
tags: [aios, evaluator, cli, monitoring, health-check]
category: aios
---

# Evaluator Skill

快速评估 AIOS 系统的命令行工具。

## 功能

- 评估任务质量（tasks）
- 评估 Agent 性能（agent, agents）
- 评估系统健康度（system）
- 评估改进效果（improvement）
- 生成评估报告（report）

## 使用方法

### 评估任务

```bash
python evaluator_cli.py tasks --time-window 24
```

### 评估 Agent

```bash
python evaluator_cli.py agent --agent-id coder
```

### 评估所有 Agent

```bash
python evaluator_cli.py agents
```

### 评估系统健康度

```bash
python evaluator_cli.py system --time-window 24
```

### 评估改进效果

```bash
python evaluator_cli.py improvement --agent-id coder
```

### 生成评估报告

```bash
python evaluator_cli.py report --time-window 24
```

## 依赖

- AIOS Evaluator 模块
- AIOS DataCollector 模块

## 触发词

- "评估任务"
- "评估 Agent"
- "评估系统"
- "系统健康度"
- "生成报告"
