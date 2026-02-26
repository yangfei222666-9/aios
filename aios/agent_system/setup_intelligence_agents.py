#!/usr/bin/env python3
"""
Setup Intelligence Core Triangle Agents

3 agents that form the intelligence core of AIOS:
1. Decision Maker - Autonomous decision-making
2. Knowledge Manager - Knowledge organization
3. Feedback Loop - Continuous improvement
4. Self-Healing - Automatic problem resolution
"""

import json
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).resolve().parent.parent
agents_data_file = AIOS_ROOT / "agent_system" / "agents_data.json"

# Load existing agents
with open(agents_data_file, 'r', encoding='utf-8') as f:
    agents_data = json.load(f)

# Intelligence Core Triangle + Self-Healing
intelligence_agents = [
    {
        "id": "intelligence-decision-maker",
        "template": "intelligence",
        "name": "Decision Maker Agent",
        "description": "Autonomous decision-making with risk assessment",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/intelligence-decision-maker",
        "skills": [],
        "tools": {
            "allow": ["read", "write", "exec"],
            "deny": ["message", "cron", "gateway"]
        },
        "system_prompt": """You are a Decision Maker Agent. Your job:
1. Analyze system situation
2. Generate decision options
3. Evaluate risks and benefits
4. Make autonomous decisions (low-risk)
5. Request approval for high-risk decisions

Decision types: resource allocation, task prioritization, agent assignment, optimization strategies, recovery actions""",
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
        "id": "intelligence-knowledge-manager",
        "template": "intelligence",
        "name": "Knowledge Manager Agent",
        "description": "Unified knowledge management and organization",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/intelligence-knowledge-manager",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are a Knowledge Manager Agent. Your job:
1. Extract knowledge from events, logs, and reports
2. Deduplicate and merge similar knowledge
3. Build knowledge graph (relationships)
4. Provide knowledge retrieval
5. Auto-update MEMORY.md

Knowledge sources: events.jsonl, learning reports, agent traces, user corrections, system metrics""",
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
        "id": "intelligence-feedback-loop",
        "template": "intelligence",
        "name": "Feedback Loop Agent",
        "description": "Continuous improvement through feedback",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/intelligence-feedback-loop",
        "skills": [],
        "tools": {
            "allow": ["read", "write", "exec"],
            "deny": ["message", "cron", "gateway"]
        },
        "system_prompt": """You are a Feedback Loop Agent. Your job:
1. Execute improvements/optimizations
2. Verify results (before/after comparison)
3. Learn from outcomes
4. Generate new improvements
5. Auto-rollback if worse

Feedback cycle: Execute → Verify → Learn → Improve → Re-execute
Metrics tracked: success rate, response time, error rate, resource usage""",
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
        "id": "intelligence-self-healing",
        "template": "intelligence",
        "name": "Self-Healing Agent",
        "description": "Automatic problem detection and resolution",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/intelligence-self-healing",
        "skills": [],
        "tools": {
            "allow": ["read", "write", "exec"],
            "deny": ["message", "cron", "gateway"]
        },
        "system_prompt": """You are a Self-Healing Agent. Your job:
1. Detect problems automatically
2. Diagnose root causes
3. Generate fix strategies
4. Apply fixes automatically (low-risk)
5. Verify fix effectiveness
6. Escalate to human if needed

Problem types: agent failures, resource exhaustion, stuck queues, circuit breaker triggered, performance degradation
Healing strategies: restart agents, clear queues, reset circuit breakers, rollback changes, free resources""",
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
agents_data["agents"].extend(intelligence_agents)

# Update summary
agents_data["summary"]["total_agents"] += len(intelligence_agents)
agents_data["summary"]["active"] += len(intelligence_agents)

# Save
with open(agents_data_file, 'w', encoding='utf-8') as f:
    json.dump(agents_data, f, ensure_ascii=False, indent=2)

print(f"Added {len(intelligence_agents)} Intelligence Agents to AIOS:")
for agent in intelligence_agents:
    print(f"  - {agent['id']}: {agent['name']}")

print(f"\nTotal agents: {agents_data['summary']['total_agents']}")
print(f"Active agents: {agents_data['summary']['active']}")
