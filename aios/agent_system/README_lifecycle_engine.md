# Agent Lifecycle Engine

**Core module for AIOS Agent Lifecycle Management**

The Agent Lifecycle Engine implements the Hexagram Three-State Model, automatically managing agent availability based on execution performance.

## 🎯 Purpose

Prevent failing agents from consuming resources while allowing healthy agents to recover automatically. This creates a self-healing agent ecosystem.

## 📊 Three-State Model

```
┌─────────┐
│ Active  │ ← Healthy agents, routable
└────┬────┘
     │ failure_rate ≥ 0.7 OR streak ≥ 5
     ↓
┌─────────┐
│ Shadow  │ ← Degraded agents, not routable
└────┬────┘
     │ failure_rate ≥ 0.7 (after cooldown)
     ↓
┌──────────┐
│ Disabled │ ← Failed agents, manual recovery only
└──────────┘
```

### State Transitions

| From | To | Condition | Cooldown |
|------|-----|-----------|----------|
| Active | Shadow | failure_rate ≥ 0.7 OR failure_streak ≥ 5 | 24 hours |
| Shadow | Disabled | failure_rate ≥ 0.7 (after cooldown) | 72 hours |
| Shadow | Active | failure_rate < 0.5 (recovery) | None |
| Disabled | - | Manual recovery only | - |

## 🚀 Usage

### As a Module

```python
from agent_lifecycle_engine import calculate_lifecycle_score, run_lifecycle_engine

# Calculate score for a single agent
score = calculate_lifecycle_score(
    agent_id="data-collector",
    current_state="active",
    cooldown_until=None,
    enabled=True,
    mode="active"
)

print(f"State: {score['lifecycle_state']}")
print(f"Routable: {score['routable']}")
print(f"Failure rate: {score['last_failure_rate']:.2%}")

# Run full lifecycle engine (updates all agents)
result = run_lifecycle_engine()
print(f"Updated {result['updated_agents']} agents")
```

### As a CLI

```bash
python agent_lifecycle_engine.py
```

Output:
```
Agent Lifecycle Engine - Hexagram Three-State System
============================================================
Total agents: 15
Updated: 15
State distribution: {'active': 10, 'shadow': 3, 'disabled': 2}
```

## 📁 Data Sources

- **Input:** `task_executions_v2.jsonl` - Agent execution history
- **State:** `agents.json` - Agent configuration and lifecycle state
- **Output:** Updates `agents.json` with new lifecycle states

## 🔧 Configuration

Edit constants at the top of the module:

```python
WINDOW_SIZE = 10              # Sliding window for execution history
FAILURE_THRESHOLD = 0.7       # Failure rate threshold for degradation
RECOVERY_THRESHOLD = 0.5      # Failure rate threshold for recovery
FAILURE_STREAK_THRESHOLD = 5  # Consecutive failures before shadow

COOLDOWN_PERIODS = {
    "active_to_shadow": timedelta(hours=24),
    "shadow_to_disabled": timedelta(hours=72),
}
```

## 🧪 Testing

Run the test suite:

```bash
pytest test_agent_lifecycle_engine.py -v
```

Test coverage:
- ✅ Failure rate calculation
- ✅ Failure streak calculation
- ✅ State transition logic
- ✅ Availability gates
- ✅ JSONL parsing and error handling
- ✅ Full lifecycle score integration

## 🛡️ Availability Gates

Agents can be blocked from routing by:

1. **enabled=false** - Agent is administratively disabled
2. **mode="shadow"** - Agent is in shadow mode
3. **mode="disabled"** - Agent is disabled

When blocked, the agent's `routable` flag is set to `false` and `availability_gate` is set to `"blocked_by_enabled_or_mode"`.

## 📈 Metrics

Each lifecycle score includes:

| Field | Type | Description |
|-------|------|-------------|
| `lifecycle_state` | str | Current state (active/shadow/disabled) |
| `last_failure_rate` | float | Recent failure rate (0.0-1.0) |
| `last_failure_streak` | int | Consecutive failures |
| `cooldown_until` | str | ISO timestamp of cooldown end |
| `timeout` | int | Execution timeout in seconds |
| `priority` | str | Routing priority (normal/low/none) |
| `window_size` | int | Number of executions analyzed |
| `routable` | bool | Whether agent can receive tasks |
| `availability_gate` | str | Gate status |

## 🔄 Integration

The lifecycle engine is typically called by:
- **Scheduler** - Periodic lifecycle updates
- **Task Router** - Pre-routing availability checks
- **Health Monitor** - System health dashboards

## 📝 Example Workflow

1. Agent executes 10 tasks, 8 fail → failure_rate = 0.8
2. Engine detects failure_rate ≥ 0.7 → transitions to shadow
3. Agent enters 24-hour cooldown, not routable
4. After cooldown, if failure_rate < 0.5 → recovers to active
5. If failure_rate still ≥ 0.7 → transitions to disabled

## 🐛 Troubleshooting

**Agent stuck in shadow:**
- Check `cooldown_until` timestamp
- Verify execution history in `task_executions_v2.jsonl`
- Manually set `mode="active"` in `agents.json` to force recovery

**No state transitions:**
- Ensure `task_executions_v2.jsonl` exists and has recent records
- Check agent_id matches between files
- Verify `enabled=true` and `mode="active"` in `agents.json`

## 📚 Related Modules

- `agent_router.py` - Uses lifecycle scores for routing decisions
- `agent_health_probe.py` - Monitors agent health metrics
- `task_executor.py` - Writes execution records

## 🤝 Contributing

When modifying this module:
1. Update docstrings for any changed functions
2. Add tests for new logic
3. Run `pytest` to ensure all tests pass
4. Update this README if behavior changes

## 📄 License

MIT License - Part of the AIOS project
