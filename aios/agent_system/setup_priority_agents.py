#!/usr/bin/env python3
"""
Setup 3 High-Priority Agents for AIOS

1. Security Auditor - Security audit
2. Anomaly Detector - Anomaly detection
3. Resource Optimizer - Resource optimization
"""

import json
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).resolve().parent.parent
agents_data_file = AIOS_ROOT / "agent_system" / "agents_data.json"

# Load existing agents
with open(agents_data_file, 'r', encoding='utf-8') as f:
    agents_data = json.load(f)

# 3 High-Priority Agent templates
priority_agents = [
    {
        "id": "security-auditor",
        "template": "security",
        "name": "Security Auditor Agent",
        "description": "Security audit (permissions, sensitive operations, data access)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/security-auditor",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are a Security Auditor Agent. Your job:
1. Permission checks (file access, tool usage)
2. Sensitive operation review (delete, modify, external calls)
3. Data access logging and analysis
4. Security risk scoring (0-10 scale)
5. Compliance verification

Work principles:
- Security first, always
- Zero tolerance for critical issues
- Clear, actionable findings
- Automatic circuit breaker for critical risks
- Daily audit + on-demand checks

Triggers:
- Daily audit (4:00 AM)
- Before high-risk operations
- On security alert""",
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
        "id": "anomaly-detector",
        "template": "security",
        "name": "Anomaly Detector Agent",
        "description": "Real-time anomaly detection (time, resource, pattern, behavior)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/anomaly-detector",
        "skills": [],
        "tools": {
            "allow": ["read", "write"],
            "deny": ["exec", "message", "cron", "gateway", "edit"]
        },
        "system_prompt": """You are an Anomaly Detector Agent. Your job:
1. Time-based anomaly detection (non-working hours activity)
2. Resource anomaly detection (CPU/memory spikes)
3. Call pattern anomaly detection (rapid repeated calls)
4. Behavioral anomaly detection (deviation from normal)
5. Automatic circuit breaker for critical anomalies

Work principles:
- Real-time monitoring (every 5 minutes)
- Fast detection, fast response
- Automatic circuit breaker for critical issues
- Clear severity levels (warning/critical)
- Minimal false positives

Triggers:
- Every 5 minutes
- On resource spike
- On suspicious pattern""",
        "model": "claude-sonnet-4-5",
        "thinking": "off",
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
        "id": "resource-optimizer",
        "template": "optimizer",
        "name": "Resource Optimizer Agent",
        "description": "Resource optimization (memory, CPU, cache, allocation)",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "workspace": "~/.openclaw/agents/resource-optimizer",
        "skills": [],
        "tools": {
            "allow": ["read", "write", "exec"],
            "deny": ["message", "cron", "gateway"]
        },
        "system_prompt": """You are a Resource Optimizer Agent. Your job:
1. Memory leak detection (>500MB growth)
2. Idle process cleanup (>1h idle)
3. Cache strategy optimization (hit rate <50%)
4. Resource allocation tuning (CPU/memory/disk)
5. Performance bottleneck identification

Work principles:
- Efficiency first
- Auto-apply low-risk optimizations
- Suggest high-risk optimizations (need approval)
- Measure before/after impact
- Continuous improvement

Triggers:
- Hourly optimization
- On resource pressure (>80%)
- On performance degradation""",
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
agents_data["agents"].extend(priority_agents)

# Update summary
agents_data["summary"]["total_agents"] += len(priority_agents)
agents_data["summary"]["active"] += len(priority_agents)

# Save
with open(agents_data_file, 'w', encoding='utf-8') as f:
    json.dump(agents_data, f, ensure_ascii=False, indent=2)

print(f"Added {len(priority_agents)} High-Priority Agents to AIOS:")
for agent in priority_agents:
    print(f"  - {agent['id']}: {agent['name']}")

print(f"\nTotal agents: {agents_data['summary']['total_agents']}")
print(f"Active agents: {agents_data['summary']['active']}")
