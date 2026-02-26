---
name: aios-health-check
description: Check AIOS system health (Evolution Score, event log size, Agent status). Use when monitoring AIOS or troubleshooting issues.
---

# AIOS Health Check

Comprehensive health check for AIOS system.

## Usage

```bash
python check.py
```

## Output

Standard Skill format:
```json
{
  "ok": true/false,
  "result": {
    "total_issues": 0,
    "issues": [...]
  },
  "evidence": ["events.jsonl", "metrics_history.jsonl", "agents.jsonl"],
  "next": ["fix_issues"] or []
}
```

## Checks

1. **Event Log Size** - Warns if events.jsonl > 10MB
2. **Evolution Score** - Critical if score < 0.4
3. **Agent Status** - Warns if any Agent is degraded

## Integration

Called by Maintenance Agent during daily maintenance.
