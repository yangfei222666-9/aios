---
name: quality-gates-skill
description: Quality Gates CLI - 快速检查改进是否可以应用，三层门禁（L0/L1/L2）
version: 1.0.0
author: 小九
tags: [aios, quality-gates, cli, safety, validation]
category: aios
---

# Quality Gates Skill

快速检查改进是否可以应用的命令行工具。

## 功能

- 检查门禁（check）- L0/L1/L2 三层门禁
- 检查改进（improvement）- 根据风险级别自动选择门禁
- 查看门禁历史（history）
- 列出所有门禁（list）

## 使用方法

### 检查 L0 门禁

```bash
python quality_gates_cli.py check --level L0 --agent-id coder
```

### 检查改进（低风险）

```bash
python quality_gates_cli.py improvement --agent-id coder --change-type config --risk-level low
```

### 检查改进（高风险）

```bash
python quality_gates_cli.py improvement --agent-id coder --change-type code --risk-level high
```

### 查看门禁历史

```bash
python quality_gates_cli.py history --limit 10
```

### 列出所有门禁

```bash
python quality_gates_cli.py list
```

## 门禁级别

- **L0（自动测试）** - 语法检查、单元测试、导入检查
- **L1（回归测试）** - 成功率、耗时、固定测试集
- **L2（人工审核）** - 关键改进需要人工确认

## 风险分级

- **低风险（config）** - L0 + L1
- **中风险（prompt）** - L0 + L1
- **高风险（code）** - L0 + L1 + L2

## 依赖

- AIOS Quality Gates 模块
- AIOS Evaluator 模块
- AIOS DataCollector 模块

## 触发词

- "检查门禁"
- "检查改进"
- "质量门禁"
- "安全检查"
