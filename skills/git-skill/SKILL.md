---
name: git-skill
description: Git CLI - Git 操作封装（提交、推送、分支管理、查看日志）
version: 1.0.0
author: 小九
tags: [git, cli, version-control]
category: development
---

# Git Skill

Git 操作的命令行封装。

## 功能

- 查看状态（status）
- 添加文件（add）
- 提交（commit）
- 推送（push）
- 拉取（pull）
- 分支管理（branch）
- 查看日志（log）
- 查看差异（diff）

## 使用方法

### 查看状态

```bash
python git_cli.py status
```

### 添加文件

```bash
python git_cli.py add file1.py file2.py
python git_cli.py add  # 添加所有文件
```

### 提交

```bash
python git_cli.py commit --message "feat: 新功能"
```

### 推送

```bash
python git_cli.py push
python git_cli.py push --remote origin --branch main
```

### 拉取

```bash
python git_cli.py pull
```

### 分支管理

```bash
python git_cli.py branch  # 列出分支
python git_cli.py branch --name feature/new-feature  # 创建并切换分支
```

### 查看日志

```bash
python git_cli.py log --limit 10
```

### 查看差异

```bash
python git_cli.py diff
```

## 依赖

- Git

## 触发词

- "git 提交"
- "git 推送"
- "创建分支"
- "查看 git 状态"
