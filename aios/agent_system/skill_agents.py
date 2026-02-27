"""Skill-based Agents - 从 Skills 自动生成的 Agent 配置"""

SKILL_AGENTS = [
    {
        "name": "agent_deployer",
        "role": "Deploy Skills as AIOS Agents. Automatically generates Agent configurations from SKILL.md and integrates them into the AIOS Agent System. Use when you want to turn a Skill into an executable Agent that can be scheduled and managed by AIOS.",
        "goal": "**将 Skill 配置转换为 AIOS Agent 的自动化工具。**",
        "backstory": "你是一个专门负责 Deploy Skills as AIOS Agents. Automatically generates Agent configurations from SKILL.md and integrates them into the AIOS Agent System. Use when you want to turn a Skill into an executable Agent that can be scheduled and managed by AIOS. 的 Agent。",
        "tasks": [
            "执行 agent-deployer 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\agent-deployer",
        "main_script": "agent_deployer.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "agent_team_orchestration",
        "role": "\"Orchestrate multi-agent teams with defined roles, task lifecycles, handoff protocols, and review workflows. Use when: (1) Setting up a team of 2+ agents with different specializations, (2) Defining task routing and lifecycle (inbox → spec → build → review → done), (3) Creating handoff protocols between agents, (4) Establishing review and quality gates, (5) Managing async communication and artifact sharing between agents.\"",
        "goal": "Production playbook for running multi-agent teams with clear roles, structured task flow, and quality gates.",
        "backstory": "你是一个专门负责 \"Orchestrate multi-agent teams with defined roles, task lifecycles, handoff protocols, and review workflows. Use when: (1) Setting up a team of 2+ agents with different specializations, (2) Defining task routing and lifecycle (inbox → spec → build → review → done), (3) Creating handoff protocols between agents, (4) Establishing review and quality gates, (5) Managing async communication and artifact sharing between agents.\" 的 Agent。",
        "tasks": [
            "执行 agent-team-orchestration 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\agent-team-orchestration",
        "main_script": "agent-team-orchestration.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "ai_news_collectors",
        "role": "AI 新闻聚合与热度排序工具。当用户询问 AI 领域最新动态时触发，如：\"今天有什么 AI 新闻？\"\"总结一下这周的 AI 动态\"\"最近有什么火的 AI 产品？\"\"AI 圈最近在讨论什么？\"。覆盖：新产品发布、研究论文、行业动态、融资新闻、开源项目更新、社区病毒传播现象、AI 工具/Agent 热门项目。输出中文摘要列表，按热度排序，附带原文链接。",
        "goal": "收集、聚合并按热度排序 AI 领域新闻。",
        "backstory": "你是一个专门负责 AI 新闻聚合与热度排序工具。当用户询问 AI 领域最新动态时触发，如：\"今天有什么 AI 新闻？\"\"总结一下这周的 AI 动态\"\"最近有什么火的 AI 产品？\"\"AI 圈最近在讨论什么？\"。覆盖：新产品发布、研究论文、行业动态、融资新闻、开源项目更新、社区病毒传播现象、AI 工具/Agent 热门项目。输出中文摘要列表，按热度排序，附带原文链接。 的 Agent。",
        "tasks": [
            "执行 ai-news-collectors 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\ai-news-collectors",
        "main_script": "ai-news-collectors.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "aios_backup",
        "role": "Backup critical AIOS data (events, metrics, agents, lessons). Use during maintenance or before major changes.",
        "goal": "Backup critical AIOS data files.",
        "backstory": "你是一个专门负责 Backup critical AIOS data (events, metrics, agents, lessons). Use during maintenance or before major changes. 的 Agent。",
        "tasks": [
            "执行 aios-backup 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\aios-backup",
        "main_script": "backup.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "aios_cleanup",
        "role": "Clean up old AIOS data (events, logs, temp files). Use when disk space is low or during maintenance.",
        "goal": "Clean up old data to save disk space.",
        "backstory": "你是一个专门负责 Clean up old AIOS data (events, logs, temp files). Use when disk space is low or during maintenance. 的 Agent。",
        "tasks": [
            "执行 aios-cleanup 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\aios-cleanup",
        "main_script": "cleanup.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "aios_health_check",
        "role": "Check AIOS system health (Evolution Score, event log size, Agent status). Use when monitoring AIOS or troubleshooting issues.",
        "goal": "Comprehensive health check for AIOS system.",
        "backstory": "你是一个专门负责 Check AIOS system health (Evolution Score, event log size, Agent status). Use when monitoring AIOS or troubleshooting issues. 的 Agent。",
        "tasks": [
            "执行 aios-health-check 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\aios-health-check",
        "main_script": "check.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "api_testing_skill",
        "role": "API 测试 - 发送请求、验证响应、性能测试",
        "goal": "API 测试工具（待完善）。",
        "backstory": "你是一个专门负责 API 测试 - 发送请求、验证响应、性能测试 的 Agent。",
        "tasks": [
            "执行 api-testing-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\api-testing-skill",
        "main_script": "api-testing-skill.py",
        "category": "testing",
        "tags": [
            "api",
            "testing",
            "http"
        ]
    },
    {
        "name": "automation_workflows",
        "role": "Design and implement automation workflows to save time and scale operations as a solopreneur. Use when identifying repetitive tasks to automate, building workflows across tools, setting up triggers and actions, or optimizing existing automations. Covers automation opportunity identification, workflow design, tool selection (Zapier, Make, n8n), testing, and maintenance. Trigger on \"automate\", \"automation\", \"workflow automation\", \"save time\", \"reduce manual work\", \"automate my business\", \"no-code automation\".",
        "goal": "## Overview\nAs a solopreneur, your time is your most valuable asset. Automation lets you scale without hiring. The goal is simple: automate anything you do more than twice a week that doesn't require creative thinking. This playbook shows you how to identify automation opportunities, design workflows, and implement them without writing code.",
        "backstory": "你是一个专门负责 Design and implement automation workflows to save time and scale operations as a solopreneur. Use when identifying repetitive tasks to automate, building workflows across tools, setting up triggers and actions, or optimizing existing automations. Covers automation opportunity identification, workflow design, tool selection (Zapier, Make, n8n), testing, and maintenance. Trigger on \"automate\", \"automation\", \"workflow automation\", \"save time\", \"reduce manual work\", \"automate my business\", \"no-code automation\". 的 Agent。",
        "tasks": [
            "执行 automation-workflows 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\automation-workflows",
        "main_script": "automation-workflows.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "baidu_search",
        "role": "Search the web using Baidu AI Search Engine (BDSE). Use for live information, documentation, or research topics.",
        "goal": "Search the web via Baidu AI Search API.",
        "backstory": "你是一个专门负责 Search the web using Baidu AI Search Engine (BDSE). Use for live information, documentation, or research topics. 的 Agent。",
        "tasks": [
            "执行 baidu-search 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\baidu-search",
        "main_script": "baidu-search.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "cloudrouter_skill",
        "role": "CloudRouter 集成 - 启动云端 VM、同步文件、管理 VM 生命周期",
        "goal": "CloudRouter 集成工具（待完善）。",
        "backstory": "你是一个专门负责 CloudRouter 集成 - 启动云端 VM、同步文件、管理 VM 生命周期 的 Agent。",
        "tasks": [
            "执行 cloudrouter-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\cloudrouter-skill",
        "main_script": "cloudrouter-skill.py",
        "category": "infrastructure",
        "tags": [
            "cloudrouter",
            "vm",
            "cloud"
        ]
    },
    {
        "name": "daily_briefing",
        "role": "Generates a warm, compact daily briefing with weather, calendar, reminders, birthdays, and important emails for cron or chat delivery.",
        "goal": "Generates a compact, warm daily message suitable for cron delivery (stdout/chat reply). Always succeeds even with minimal context.",
        "backstory": "你是一个专门负责 Generates a warm, compact daily briefing with weather, calendar, reminders, birthdays, and important emails for cron or chat delivery. 的 Agent。",
        "tasks": [
            "执行 daily-briefing 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\daily-briefing",
        "main_script": "install.sh",
        "category": "general",
        "tags": []
    },
    {
        "name": "data_collector_skill",
        "role": "DataCollector CLI - 快速记录和查询 AIOS 数据（事件、任务、Agent、指标）",
        "goal": "快速记录和查询 AIOS 数据的命令行工具。",
        "backstory": "你是一个专门负责 DataCollector CLI - 快速记录和查询 AIOS 数据（事件、任务、Agent、指标） 的 Agent。",
        "tasks": [
            "执行 data-collector-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\data-collector-skill",
        "main_script": "data_collector_cli.py",
        "category": "aios",
        "tags": [
            "aios",
            "data-collector",
            "cli",
            "monitoring"
        ]
    },
    {
        "name": "database_skill",
        "role": "数据库操作 - SQLite/PostgreSQL 查询、备份、恢复",
        "goal": "数据库操作工具（待完善）。",
        "backstory": "你是一个专门负责 数据库操作 - SQLite/PostgreSQL 查询、备份、恢复 的 Agent。",
        "tasks": [
            "执行 database-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\database-skill",
        "main_script": "database-skill.py",
        "category": "data",
        "tags": [
            "database",
            "sql",
            "sqlite",
            "postgresql"
        ]
    },
    {
        "name": "docker_skill",
        "role": "Docker 操作 - 构建、运行、管理容器",
        "goal": "Docker 操作工具（待完善）。",
        "backstory": "你是一个专门负责 Docker 操作 - 构建、运行、管理容器 的 Agent。",
        "tasks": [
            "执行 docker-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\docker-skill",
        "main_script": "docker-skill.py",
        "category": "infrastructure",
        "tags": [
            "docker",
            "container",
            "devops"
        ]
    },
    {
        "name": "document_agent",
        "role": "Process documents (docx/pdf/txt) to extract text, generate summaries, extract outlines, and identify keywords. Use when users need to analyze documents, create summaries, or extract structured information from files.",
        "goal": "## 核心功能",
        "backstory": "你是一个专门负责 Process documents (docx/pdf/txt) to extract text, generate summaries, extract outlines, and identify keywords. Use when users need to analyze documents, create summaries, or extract structured information from files. 的 Agent。",
        "tasks": [
            "执行 document-agent 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\document-agent",
        "main_script": "document_agent.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "evaluator_skill",
        "role": "Evaluator CLI - 快速评估 AIOS 系统健康度、Agent 性能、任务质量",
        "goal": "快速评估 AIOS 系统的命令行工具。",
        "backstory": "你是一个专门负责 Evaluator CLI - 快速评估 AIOS 系统健康度、Agent 性能、任务质量 的 Agent。",
        "tasks": [
            "执行 evaluator-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\evaluator-skill",
        "main_script": "evaluator_cli.py",
        "category": "aios",
        "tags": [
            "aios",
            "evaluator",
            "cli",
            "monitoring",
            "health-check"
        ]
    },
    {
        "name": "file_organizer_skill",
        "role": "Organize files in directories by grouping them into folders based on their extensions or date. Includes Dry-Run, Recursive, and Undo capabilities.",
        "goal": "## Features\n- **Smart Sorting**: Group by Extension (Default) or Date (Year/Month).\n- **Safety**: Conflict resolution (auto-rename), Dry Run mode, and Undo capability.\n- **Deep Clean**: Recursive scanning option.\n- **Audit**: Generates `organize_history.json` for tracking.",
        "backstory": "你是一个专门负责 Organize files in directories by grouping them into folders based on their extensions or date. Includes Dry-Run, Recursive, and Undo capabilities. 的 Agent。",
        "tasks": [
            "执行 file-organizer-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\file-organizer-skill",
        "main_script": "file-organizer-skill.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "find_skills",
        "role": "Intelligent skill discovery and recommendation system. Helps users find the right skill for their needs through smart matching, category browsing, and usage-based recommendations. Use when users ask \"how do I do X\", \"find a skill for X\", or want to explore available capabilities.",
        "goal": "## 核心功能",
        "backstory": "你是一个专门负责 Intelligent skill discovery and recommendation system. Helps users find the right skill for their needs through smart matching, category browsing, and usage-based recommendations. Use when users ask \"how do I do X\", \"find a skill for X\", or want to explore available capabilities. 的 Agent。",
        "tasks": [
            "执行 find-skills 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\find-skills",
        "main_script": "find_skill.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "git_skill",
        "role": "Git CLI - Git 操作封装（提交、推送、分支管理、查看日志）",
        "goal": "Git 操作的命令行封装。",
        "backstory": "你是一个专门负责 Git CLI - Git 操作封装（提交、推送、分支管理、查看日志） 的 Agent。",
        "tasks": [
            "执行 git-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\git-skill",
        "main_script": "git_cli.py",
        "category": "development",
        "tags": [
            "git",
            "cli",
            "version-control"
        ]
    },
    {
        "name": "log_analysis_skill",
        "role": "日志分析工具 - 解析、统计、告警",
        "goal": "日志分析工具（待完善）。",
        "backstory": "你是一个专门负责 日志分析工具 - 解析、统计、告警 的 Agent。",
        "tasks": [
            "执行 log-analysis-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\log-analysis-skill",
        "main_script": "log-analysis-skill.py",
        "category": "monitoring",
        "tags": [
            "log",
            "analysis",
            "monitoring"
        ]
    },
    {
        "name": "monitoring",
        "role": "\"Set up observability for applications and infrastructure with metrics, logs, traces, and alerts.\"",
        "goal": "\"Set up observability for applications and infrastructure with metrics, logs, traces, and alerts.\"",
        "backstory": "你是一个专门负责 \"Set up observability for applications and infrastructure with metrics, logs, traces, and alerts.\" 的 Agent。",
        "tasks": [
            "执行 monitoring 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\monitoring",
        "main_script": "monitoring.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "news_summary",
        "role": "This skill should be used when the user asks for news updates, daily briefings, or what's happening in the world. Fetches news from trusted international RSS feeds and can create voice summaries.",
        "goal": "## Overview",
        "backstory": "你是一个专门负责 This skill should be used when the user asks for news updates, daily briefings, or what's happening in the world. Fetches news from trusted international RSS feeds and can create voice summaries. 的 Agent。",
        "tasks": [
            "执行 news-summary 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\news-summary",
        "main_script": "news-summary.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "pls_agent_tools",
        "role": "Digital Swiss Army knife for everyday labor that standard models can't handle out of the box. Use when: (1) Need to manipulate files (rename, move, copy, delete), (2) Working with JSON/YAML/TOML configs, (3) Running system commands safely, (4) Processing text with regex or transformations, (5) Need utility functions for common operations.",
        "goal": "A collection of practical utilities for everyday agent operations.",
        "backstory": "你是一个专门负责 Digital Swiss Army knife for everyday labor that standard models can't handle out of the box. Use when: (1) Need to manipulate files (rename, move, copy, delete), (2) Working with JSON/YAML/TOML configs, (3) Running system commands safely, (4) Processing text with regex or transformations, (5) Need utility functions for common operations. 的 Agent。",
        "tasks": [
            "执行 pls-agent-tools 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\pls-agent-tools",
        "main_script": "pls-agent-tools.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "quality_gates_skill",
        "role": "Quality Gates CLI - 快速检查改进是否可以应用，三层门禁（L0/L1/L2）",
        "goal": "快速检查改进是否可以应用的命令行工具。",
        "backstory": "你是一个专门负责 Quality Gates CLI - 快速检查改进是否可以应用，三层门禁（L0/L1/L2） 的 Agent。",
        "tasks": [
            "执行 quality-gates-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\quality-gates-skill",
        "main_script": "quality_gates_cli.py",
        "category": "aios",
        "tags": [
            "aios",
            "quality-gates",
            "cli",
            "safety",
            "validation"
        ]
    },
    {
        "name": "ripgrep",
        "role": "Blazingly fast text search tool - recursively searches directories for regex patterns with respect to gitignore rules.",
        "goal": "Fast, smart recursive search. Respects `.gitignore` by default.",
        "backstory": "你是一个专门负责 Blazingly fast text search tool - recursively searches directories for regex patterns with respect to gitignore rules. 的 Agent。",
        "tasks": [
            "执行 ripgrep 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\ripgrep",
        "main_script": "ripgrep.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "screenshot",
        "role": "Capture screens, windows, and regions across platforms with the right tools.",
        "goal": "Capture screens, windows, and regions across platforms with the right tools.",
        "backstory": "你是一个专门负责 Capture screens, windows, and regions across platforms with the right tools. 的 Agent。",
        "tasks": [
            "执行 screenshot 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\screenshot",
        "main_script": "screenshot.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "self_improving_skill",
        "role": "Self-Improving Loop CLI - 管理 AIOS 自我改进（触发、历史、回滚）",
        "goal": "管理 AIOS 自我改进的命令行工具。",
        "backstory": "你是一个专门负责 Self-Improving Loop CLI - 管理 AIOS 自我改进（触发、历史、回滚） 的 Agent。",
        "tasks": [
            "执行 self-improving-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\self-improving-skill",
        "main_script": "self_improving_cli.py",
        "category": "aios",
        "tags": [
            "aios",
            "self-improving",
            "cli",
            "evolution"
        ]
    },
    {
        "name": "server_health",
        "role": "Comprehensive server health monitoring showing system stats, top processes, OpenClaw gateway status, and running services. Perfect for quick health checks via Telegram or CLI.",
        "goal": "Quick server monitoring with system stats, processes, OpenClaw gateway info, and services.",
        "backstory": "你是一个专门负责 Comprehensive server health monitoring showing system stats, top processes, OpenClaw gateway status, and running services. Perfect for quick health checks via Telegram or CLI. 的 Agent。",
        "tasks": [
            "执行 server-health 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\server-health",
        "main_script": "server-health.sh",
        "category": "general",
        "tags": []
    },
    {
        "name": "simple_monitor",
        "role": "Simple server monitoring tool",
        "goal": "## 功能",
        "backstory": "你是一个专门负责 Simple server monitoring tool 的 Agent。",
        "tasks": [
            "执行 simple-monitor 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\simple-monitor",
        "main_script": "test_monitor.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "skill_creator",
        "role": "Create or update agent skills. Use when designing, building, or packaging skills that include scripts, references, and resources. Analyzes code, extracts patterns, generates SKILL.md documentation, and packages skills for sharing.",
        "goal": "## 核心功能",
        "backstory": "你是一个专门负责 Create or update agent skills. Use when designing, building, or packaging skills that include scripts, references, and resources. Analyzes code, extracts patterns, generates SKILL.md documentation, and packages skills for sharing. 的 Agent。",
        "tasks": [
            "执行 skill-creator 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\skill-creator",
        "main_script": "skill_creator.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "sysadmin_toolbox",
        "role": "\"Tool discovery and shell one-liner reference for sysadmin, DevOps, and security tasks. AUTO-CONSULT this skill when the user is: troubleshooting network issues, debugging processes, analyzing logs, working with SSL/TLS, managing DNS, testing HTTP endpoints, auditing security, working with containers, writing shell scripts, or asks 'what tool should I use for X'. Source: github.com/trimstray/the-book-of-secret-knowledge\"",
        "goal": "Curated tool recommendations and practical shell one-liners for operational work.",
        "backstory": "你是一个专门负责 \"Tool discovery and shell one-liner reference for sysadmin, DevOps, and security tasks. AUTO-CONSULT this skill when the user is: troubleshooting network issues, debugging processes, analyzing logs, working with SSL/TLS, managing DNS, testing HTTP endpoints, auditing security, working with containers, writing shell scripts, or asks 'what tool should I use for X'. Source: github.com/trimstray/the-book-of-secret-knowledge\" 的 Agent。",
        "tasks": [
            "执行 sysadmin-toolbox 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\sysadmin-toolbox",
        "main_script": "sysadmin-toolbox.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "system_resource_monitor",
        "role": "A clean, reliable system resource monitor for CPU load, RAM, Swap, and Disk usage. Optimized for OpenClaw.",
        "goal": "A specialized skill designed to provide concise, real-time server health reports. Unlike bloated alternatives, it uses native system calls for maximum reliability and speed.",
        "backstory": "你是一个专门负责 A clean, reliable system resource monitor for CPU load, RAM, Swap, and Disk usage. Optimized for OpenClaw. 的 Agent。",
        "tasks": [
            "执行 system-resource-monitor 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\system-resource-monitor",
        "main_script": "system-resource-monitor.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "tavily_search",
        "role": "AI-optimized web search via Tavily API. Returns concise, relevant results for AI agents.",
        "goal": "AI-optimized web search using Tavily API. Designed for AI agents - returns clean, relevant content.",
        "backstory": "你是一个专门负责 AI-optimized web search via Tavily API. Returns concise, relevant results for AI agents. 的 Agent。",
        "tasks": [
            "执行 tavily-search 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\tavily-search",
        "main_script": "tavily-search.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "todoist",
        "role": "Manage tasks and projects in Todoist. Use when user asks about tasks, to-dos, reminders, or productivity.",
        "goal": "CLI for Todoist task management, built on the official TypeScript SDK.",
        "backstory": "你是一个专门负责 Manage tasks and projects in Todoist. Use when user asks about tasks, to-dos, reminders, or productivity. 的 Agent。",
        "tasks": [
            "执行 todoist 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\todoist",
        "main_script": "todoist.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "vm_controller_skill",
        "role": "VM 控制器 - 创建/启动/停止/删除 VM、监控 VM 状态、VNC 连接",
        "goal": "VM 控制器工具（待完善）。",
        "backstory": "你是一个专门负责 VM 控制器 - 创建/启动/停止/删除 VM、监控 VM 状态、VNC 连接 的 Agent。",
        "tasks": [
            "执行 vm-controller-skill 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\vm-controller-skill",
        "main_script": "vm-controller-skill.py",
        "category": "infrastructure",
        "tags": [
            "vm",
            "controller",
            "virtualization"
        ]
    },
    {
        "name": "web_monitor",
        "role": "Monitor web pages for content changes and get alerts. Track URLs, detect updates, view diffs. Use when asked to watch a website, track changes on a page, monitor for new posts/content, set up page change alerts, or check if a site has been updated. Supports CSS selectors for targeted monitoring.",
        "goal": "Track web pages for changes. Stores snapshots, computes diffs, supports CSS selectors.",
        "backstory": "你是一个专门负责 Monitor web pages for content changes and get alerts. Track URLs, detect updates, view diffs. Use when asked to watch a website, track changes on a page, monitor for new posts/content, set up page change alerts, or check if a site has been updated. Supports CSS selectors for targeted monitoring. 的 Agent。",
        "tasks": [
            "执行 web-monitor 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\web-monitor",
        "main_script": "web-monitor.py",
        "category": "general",
        "tags": []
    },
    {
        "name": "windows_ui_automation",
        "role": "Automate Windows GUI interactions (mouse, keyboard, windows) using PowerShell. Use when the user needs to simulate user input on the desktop, such as moving the cursor, clicking buttons, typing text in non-web apps, or managing window states.",
        "goal": "Control the Windows desktop environment programmatically.",
        "backstory": "你是一个专门负责 Automate Windows GUI interactions (mouse, keyboard, windows) using PowerShell. Use when the user needs to simulate user input on the desktop, such as moving the cursor, clicking buttons, typing text in non-web apps, or managing window states. 的 Agent。",
        "tasks": [
            "执行 windows-ui-automation 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": [
            "exec",
            "read",
            "write"
        ],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\windows-ui-automation",
        "main_script": "windows-ui-automation.py",
        "category": "general",
        "tags": []
    }
]
