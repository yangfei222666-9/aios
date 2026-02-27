---
name: self-improving-skill
description: Self-Improving Loop CLI - 管理 AIOS 自我改进（触发、历史、回滚）
version: 1.0.0
author: 小九
tags: [aios, self-improving, cli, evolution]
category: aios
---

# Self-Improving Skill

管理 AIOS 自我改进的命令行工具。

## 功能

- 触发改进（trigger）
- 查看改进历史（history）
- 回滚改进（rollback）
- 显示统计（stats）

## 使用方法

### 触发改进

```bash
python self_improving_cli.py trigger --agent-id coder --type prompt --description "优化提示词"
```

### 查看改进历史

```bash
python self_improving_cli.py history --limit 10
```

### 回滚改进

```bash
python self_improving_cli.py rollback --change-id change_20260227_001234
```

### 显示统计

```bash
python self_improving_cli.py stats
```

## 依赖

- AIOS Self-Improving Loop 模块

## 触发词

- "触发改进"
- "查看改进历史"
- "回滚改进"
- "自我进化"
