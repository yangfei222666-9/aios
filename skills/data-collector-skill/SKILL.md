---
name: data-collector-skill
description: DataCollector CLI - 快速记录和查询 AIOS 数据（事件、任务、Agent、指标）
version: 1.0.0
author: 小九
tags: [aios, data-collector, cli, monitoring]
category: aios
---

# DataCollector Skill

快速记录和查询 AIOS 数据的命令行工具。

## 功能

- 记录事件（log-event）
- 创建/更新/完成任务（create-task, update-task, complete-task）
- 查询任务和事件（query-tasks, query-events）
- 更新/获取 Agent 状态（update-agent, get-agent）
- 记录指标（record-metric）

## 使用方法

### 记录事件

```bash
python data_collector_cli.py log-event --type task_started --task-id task_123 --agent-id coder
```

### 创建任务

```bash
python data_collector_cli.py create-task --title "实现功能" --type code --priority high
```

### 查询任务

```bash
python data_collector_cli.py query-tasks --status success --limit 10
```

### 更新 Agent

```bash
python data_collector_cli.py update-agent --agent-id coder --status busy
```

### 记录指标

```bash
python data_collector_cli.py record-metric --name task_duration_ms --value 5000 --tags '{"task_type":"code"}'
```

## 依赖

- AIOS DataCollector 模块

## 触发词

- "记录事件"
- "创建任务"
- "查询任务"
- "更新 Agent"
- "记录指标"
