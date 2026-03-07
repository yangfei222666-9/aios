#!/usr/bin/env python3
"""
Test script for 5 Learning Agents

Creates minimal test data and runs all 5 learners.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

AIOS_ROOT = Path(__file__).resolve().parent.parent
data_dir = AIOS_ROOT / "data"
data_dir.mkdir(parents=True, exist_ok=True)

events_file = data_dir / "events.jsonl"

# Create test events
test_events = []

# 1. Provider events
for i in range(10):
    test_events.append({
        "type": "router_call",
        "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
        "provider": "claude" if i % 2 == 0 else "openai",
        "success": i % 3 != 0,
        "duration_ms": 1000 + i * 100,
        "error": "timeout" if i % 3 == 0 else ""
    })

# 2. Playbook events
for i in range(8):
    test_events.append({
        "type": "reactor_action",
        "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
        "playbook_id": f"playbook_{i % 3}",
        "success": i % 4 != 0,
        "fixed": i % 5 != 0,
        "error_type": "network_error" if i % 2 == 0 else "timeout"
    })

# 3. Error events
for i in range(5):
    test_events.append({
        "type": "error",
        "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
        "error_type": "connection_error" if i % 2 == 0 else "timeout",
        "error_message": f"Error {i}",
        "component": "agent" if i % 2 == 0 else "scheduler",
        "agent_id": f"agent-{i}"
    })

# 4. Optimization events
for i in range(6):
    test_events.append({
        "type": "optimization",
        "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
        "optimization_type": "cache" if i % 2 == 0 else "timeout",
        "target": f"component_{i}",
        "description": f"Optimization {i}",
        "risk": "low",
        "expected_improvement": "faster",
        "actual_improvement": "positive" if i % 3 != 0 else "negative"
    })

# Write events
with open(events_file, 'w', encoding='utf-8') as f:
    for event in test_events:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

print(f"Created {len(test_events)} test events in {events_file}")
print("\nNow run: python learning_orchestrator_simple.py")
