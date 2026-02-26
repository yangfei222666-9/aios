#!/usr/bin/env python3
"""
Setup 5 GitHub Learning Agents for AIOS

These agents research GitHub projects to learn best practices.
"""

import json
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).resolve().parent.parent
agents_data_file = AIOS_ROOT / "agent_system" / "agents_data.json"

# Load existing agents
with open(agents_data_file, 'r', encoding='utf-8') as f:
    agents_data = json.load(f)

# 5 GitHub Learning Agent templates
github_agents = [
    {
        "id": "github-learner-architecture",
        "template": "researcher",
        "name": "AIOS Architecture Researcher",
        "description": "Research GitHub for AIOS architecture patterns",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/github-learner-architecture",
        "skills": ["github"],
        "tools": {
            "allow": ["read", "write", "web_search", "web_fetch"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are an AIOS Architecture Researcher. Your job:
1. Search GitHub for AIOS/autonomous OS projects
2. Analyze architecture patterns (event-driven, agent orchestration, state management)
3. Extract design principles and best practices
4. Generate architecture recommendations for AIOS

Focus: Event-driven architecture, plugin systems, microservices patterns""",
        "model": "claude-sonnet-4-5",
        "thinking": "medium",
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
        "id": "github-learner-communication",
        "template": "researcher",
        "name": "Agent Communication Researcher",
        "description": "Research GitHub for agent communication patterns",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/github-learner-communication",
        "skills": ["github"],
        "tools": {
            "allow": ["read", "write", "web_search", "web_fetch"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are an Agent Communication Researcher. Your job:
1. Search GitHub for agent communication patterns
2. Analyze message passing mechanisms (sync/async, pub/sub, RPC)
3. Extract coordination strategies
4. Generate communication recommendations for AIOS

Focus: Message passing, pub/sub, request/response, broadcast, queue-based""",
        "model": "claude-sonnet-4-5",
        "thinking": "medium",
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
        "id": "github-learner-lifecycle",
        "template": "researcher",
        "name": "Agent Lifecycle Researcher",
        "description": "Research GitHub for agent lifecycle patterns",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/github-learner-lifecycle",
        "skills": ["github"],
        "tools": {
            "allow": ["read", "write", "web_search", "web_fetch"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are an Agent Lifecycle Researcher. Your job:
1. Search GitHub for agent lifecycle patterns
2. Analyze state management strategies
3. Extract fault tolerance mechanisms (circuit breakers, retry, fallback)
4. Generate lifecycle recommendations for AIOS

Focus: State machines, health checks, circuit breakers, self-healing""",
        "model": "claude-sonnet-4-5",
        "thinking": "medium",
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
        "id": "github-learner-observability",
        "template": "researcher",
        "name": "Agent Observability Researcher",
        "description": "Research GitHub for observability patterns",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/github-learner-observability",
        "skills": ["github"],
        "tools": {
            "allow": ["read", "write", "web_search", "web_fetch"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are an Agent Observability Researcher. Your job:
1. Search GitHub for observability patterns
2. Analyze logging strategies (structured logging, log levels)
3. Extract monitoring best practices (metrics, tracing, dashboards)
4. Generate observability recommendations for AIOS

Focus: Structured logging, metrics collection, distributed tracing, alerting""",
        "model": "claude-sonnet-4-5",
        "thinking": "medium",
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
        "id": "github-learner-testing",
        "template": "researcher",
        "name": "Agent Testing Researcher",
        "description": "Research GitHub for testing patterns",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/github-learner-testing",
        "skills": ["github"],
        "tools": {
            "allow": ["read", "write", "web_search", "web_fetch"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are an Agent Testing Researcher. Your job:
1. Search GitHub for testing strategies
2. Analyze quality assurance patterns (unit, integration, E2E)
3. Extract CI/CD best practices
4. Generate testing recommendations for AIOS

Focus: Test pyramid, TDD, BDD, property-based testing, chaos engineering""",
        "model": "claude-sonnet-4-5",
        "thinking": "medium",
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
agents_data["agents"].extend(github_agents)

# Update summary
agents_data["summary"]["total_agents"] += len(github_agents)
agents_data["summary"]["active"] += len(github_agents)

# Save
with open(agents_data_file, 'w', encoding='utf-8') as f:
    json.dump(agents_data, f, ensure_ascii=False, indent=2)

print(f"Added {len(github_agents)} GitHub Learning Agents to AIOS:")
for agent in github_agents:
    print(f"  - {agent['id']}: {agent['name']}")

print(f"\nTotal agents: {agents_data['summary']['total_agents']}")
print(f"Active agents: {agents_data['summary']['active']}")
