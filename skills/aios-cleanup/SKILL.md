---
name: aios-cleanup
description: Clean up old AIOS data (events, logs, temp files). Use when disk space is low or during maintenance.
---

# AIOS Cleanup

Clean up old data to save disk space.

## Usage

```bash
# Clean data older than 7 days (default)
python cleanup.py

# Clean data older than 30 days
python cleanup.py --days 30
```

## Output

Standard Skill format:
```json
{
  "ok": true,
  "result": {
    "cleaned_count": 5,
    "cleaned_items": [...]
  },
  "evidence": ["events.jsonl", "memory/"],
  "next": []
}
```

## What It Cleans

1. **Event Logs** - Keep only last N days in events.jsonl
2. **Daily Logs** - Archive memory/*.md older than N days
3. **Temp Files** - Remove .bak, __pycache__, etc.

## Integration

Called by Maintenance Agent during daily maintenance.
