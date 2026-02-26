# 5 Learning Agents - Setup Complete

## Overview

5 specialized learning agents have been successfully integrated into AIOS to provide deep, focused learning across different dimensions.

## Architecture

```
Learning Orchestrator (learning_orchestrator_simple.py)
├── Provider Learner (learner_provider.py)
│   └── Learns: Provider performance, success rate, latency, errors
├── Playbook Learner (learner_playbook.py)
│   └── Learns: Playbook effectiveness, success rate, fix rate
├── Agent Behavior Learner (learner_agent_behavior.py)
│   └── Learns: Agent behavior, tool usage, duration, best practices
├── Error Pattern Learner (learner_error_pattern.py)
│   └── Learns: Error patterns, root causes, propagation chains
└── Optimization Learner (learner_optimization.py)
    └── Learns: Optimization effectiveness, trends, ROI
```

## Agents Registered

All 5 learning agents are now registered in `agents_data.json`:

1. **learner-provider** - Provider Learning Agent
2. **learner-playbook** - Playbook Learning Agent
3. **learner-agent-behavior** - Agent Behavior Learning Agent
4. **learner-error-pattern** - Error Pattern Learning Agent
5. **learner-optimization** - Optimization Learning Agent

## Execution

### Daily Schedule (4:00 AM)

```bash
& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\learning_orchestrator_simple.py
```

### Output Format

- `LEARNING_ORCHESTRATOR_OK` - No important findings
- `LEARNING_ORCHESTRATOR_SUGGESTIONS:N` - Generated N suggestions

### Reports

All learning reports are saved to:
```
aios/agent_system/data/learning/
├── provider_learning_YYYYMMDD_HHMMSS.json
├── playbook_learning_YYYYMMDD_HHMMSS.json
├── agent_behavior_YYYYMMDD_HHMMSS.json
├── error_pattern_YYYYMMDD_HHMMSS.json
├── optimization_learning_YYYYMMDD_HHMMSS.json
└── orchestrator_YYYYMMDD_HHMMSS.json (summary)
```

## Learning Dimensions

### 1. Provider Learner
- **Monitors:** All Provider calls (claude, openai, etc.)
- **Analyzes:** Success rate, latency, error types
- **Identifies:** Best and problematic Providers
- **Suggests:** Provider switching strategies

### 2. Playbook Learner
- **Monitors:** All Playbook executions
- **Analyzes:** Success rate, fix effectiveness
- **Identifies:** Effective and ineffective Playbooks
- **Suggests:** Playbook optimization strategies

### 3. Agent Behavior Learner
- **Monitors:** All Agent task executions
- **Analyzes:** Success rate, tool usage, duration
- **Identifies:** Best practices, effective tool combinations
- **Suggests:** Agent optimization strategies

### 4. Error Pattern Learner
- **Monitors:** All error events
- **Analyzes:** Repeat errors, root causes, propagation chains
- **Identifies:** Temporal patterns, error chains
- **Suggests:** Error prevention strategies

### 5. Optimization Learner
- **Monitors:** All optimization operations
- **Analyzes:** Effectiveness (before/after comparison)
- **Identifies:** Effective and ineffective optimizations
- **Suggests:** Optimization strategy improvements

## Integration with HEARTBEAT.md

Added to daily heartbeat tasks:

```markdown
### 每天：AIOS 学习 Agent（5 个专门学习维度）（新增 2026-02-24）
- 运行 learning_orchestrator_simple.py
- 5 个学习 Agent 按顺序执行
- 输出：LEARNING_ORCHESTRATOR_OK / LEARNING_ORCHESTRATOR_SUGGESTIONS:N
- 报告保存到 aios/agent_system/data/learning/
- 执行时间：每天凌晨 4:00
```

## Testing

Test script created: `test_learning_setup.py`

```bash
& "C:\Program Files\Python312\python.exe" C:\Users\A\.openclaw\workspace\aios\agent_system\test_learning_setup.py
```

This will:
1. Create test data (29 events)
2. Run the learning orchestrator
3. Verify agents registration

## Status

✅ 5 Learning Agents created
✅ Registered in agents_data.json
✅ Orchestrator implemented
✅ Test data generator created
✅ HEARTBEAT.md updated
✅ Test script verified

**Total agents in AIOS:** 14 (10 active, 4 archived)
**Learning agents:** 5 (all active)

## Next Steps

1. Accumulate real data (3-7 days)
2. Review learning reports
3. Apply high-priority suggestions
4. Iterate and improve learning algorithms

---

**Created:** 2026-02-24
**Status:** Production Ready
