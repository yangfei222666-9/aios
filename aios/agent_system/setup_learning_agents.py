#!/usr/bin/env python3
"""
Setup 5 Learning Agents for AIOS

Creates 5 specialized learning agents and registers them in the system.
"""

import json
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).resolve().parent.parent
agents_data_file = AIOS_ROOT / "agent_system" / "agents_data.json"

# Load existing agents
with open(agents_data_file, 'r', encoding='utf-8') as f:
    agents_data = json.load(f)

# 5 Learning Agent templates
learning_agents = [
    {
        "id": "learner-provider",
        "template": "learner",
        "name": "Provider Learning Agent",
        "description": "Learn Provider performance (success rate, latency, errors)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/learner-provider",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway"]
        },
        "system_prompt": """You are a Provider Learning Agent. Your job:
1. Monitor all Provider calls (claude, openai, etc.)
2. Analyze success rate, latency, error types
3. Identify best and problematic Providers
4. Generate Provider switching suggestions
5. Track performance trends over time

Work principles:
- Data-driven decisions
- Statistical significance (min 5 calls)
- Clear, actionable suggestions
- Focus on high-impact improvements""",
        "model": "claude-sonnet-4-5",
        "thinking": "low",
        "stats": {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 0.0,
            "avg_duration_sec": 0,
            "total_duration_sec": 0,
            "last_active": None
        },
        "task_description": None
    },
    {
        "id": "learner-playbook",
        "template": "learner",
        "name": "Playbook Learning Agent",
        "description": "Learn Playbook effectiveness (success rate, fix rate)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/learner-playbook",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway"]
        },
        "system_prompt": """You are a Playbook Learning Agent. Your job:
1. Monitor all Playbook executions
2. Analyze success rate and fix effectiveness
3. Identify effective and ineffective Playbooks
4. Generate Playbook optimization suggestions
5. Track effectiveness trends over time

Work principles:
- Distinguish execution success from actual fix
- Statistical significance (min 3 executions)
- Clear, actionable suggestions
- Focus on high-impact improvements""",
        "model": "claude-sonnet-4-5",
        "thinking": "low",
        "stats": {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 0.0,
            "avg_duration_sec": 0,
            "total_duration_sec": 0,
            "last_active": None
        },
        "task_description": None
    },
    {
        "id": "learner-agent-behavior",
        "template": "learner",
        "name": "Agent Behavior Learning Agent",
        "description": "Learn Agent behavior (success rate, tool usage, duration)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/learner-agent-behavior",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway"]
        },
        "system_prompt": """You are an Agent Behavior Learning Agent. Your job:
1. Monitor all Agent task executions
2. Analyze success rate, tool usage, duration
3. Identify best practices and effective tool combinations
4. Generate Agent optimization suggestions
5. Track behavior trends over time

Work principles:
- Learn from successful Agents
- Identify effective tool sequences
- Statistical significance (min 5 tasks)
- Clear, actionable suggestions
- Focus on high-impact improvements""",
        "model": "claude-sonnet-4-5",
        "thinking": "low",
        "stats": {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 0.0,
            "avg_duration_sec": 0,
            "total_duration_sec": 0,
            "last_active": None
        },
        "task_description": None
    },
    {
        "id": "learner-error-pattern",
        "template": "learner",
        "name": "Error Pattern Learning Agent",
        "description": "Learn error patterns (repeat errors, root causes, propagation)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/learner-error-pattern",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway"]
        },
        "system_prompt": """You are an Error Pattern Learning Agent. Your job:
1. Monitor all error events
2. Identify repeat error patterns (≥3 occurrences)
3. Analyze root causes and error propagation chains
4. Generate error prevention suggestions
5. Track temporal patterns (peak hours)

Work principles:
- Focus on repeat errors (≥3 times)
- Identify error chains (5min window)
- Statistical significance
- Clear, actionable suggestions
- Focus on high-impact improvements""",
        "model": "claude-sonnet-4-5",
        "thinking": "low",
        "stats": {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 0.0,
            "avg_duration_sec": 0,
            "total_duration_sec": 0,
            "last_active": None
        },
        "task_description": None
    },
    {
        "id": "learner-optimization",
        "template": "learner",
        "name": "Optimization Learning Agent",
        "description": "Learn optimization effectiveness (success rate, trends)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/learner-optimization",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway"]
        },
        "system_prompt": """You are an Optimization Learning Agent. Your job:
1. Monitor all optimization operations
2. Analyze effectiveness (before/after comparison)
3. Identify effective and ineffective optimizations
4. Generate optimization strategy suggestions
5. Track effectiveness trends over time

Work principles:
- Compare expected vs actual improvement
- Identify declining effectiveness trends
- Statistical significance
- Clear, actionable suggestions
- Focus on high-impact improvements""",
        "model": "claude-sonnet-4-5",
        "thinking": "low",
        "stats": {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 0.0,
            "avg_duration_sec": 0,
            "total_duration_sec": 0,
            "last_active": None
        },
        "task_description": None
    }
]

# Add to agents list
agents_data["agents"].extend(learning_agents)

# Update summary
agents_data["summary"]["total_agents"] += len(learning_agents)
agents_data["summary"]["active"] += len(learning_agents)

# Save
with open(agents_data_file, 'w', encoding='utf-8') as f:
    json.dump(agents_data, f, ensure_ascii=False, indent=2)

print(f"Added {len(learning_agents)} Learning Agents to AIOS:")
for agent in learning_agents:
    print(f"  - {agent['id']}: {agent['name']}")

print(f"\nTotal agents: {agents_data['summary']['total_agents']}")
print(f"Active agents: {agents_data['summary']['active']}")
