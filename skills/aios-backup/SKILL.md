---
name: aios-backup
description: Backup critical AIOS data (events, metrics, agents, lessons). Use during maintenance or before major changes.
---

# AIOS Backup

Backup critical AIOS data files.

## Usage

```bash
python backup.py
```

## Output

Standard Skill format:
```json
{
  "ok": true,
  "result": {
    "backup_dir": "C:/Users/A/.openclaw/workspace/aios/backups/2026-02-24",
    "backed_up_count": 4,
    "backed_up_files": [...]
  },
  "evidence": ["backups/2026-02-24/"],
  "next": []
}
```

## What It Backs Up

1. **events.jsonl** - All system events
2. **metrics_history.jsonl** - Evolution Score history
3. **agents.jsonl** - Agent states
4. **lessons.json** - Learned lessons

## Backup Location

`aios/backups/YYYY-MM-DD/`

## Integration

Called by Maintenance Agent during daily maintenance.
