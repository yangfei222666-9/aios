# AIOS Quick Start Guide

Get AIOS running in 5 minutes.

## Prerequisites

- Python 3.12+
- Windows 10/11 or Linux
- 8GB+ RAM

## Installation

### 1. Clone or Download

```bash
git clone https://github.com/your-org/aios.git
cd aios
```

### 2. Install Dependencies

```bash
cd agent_system
pip install -r requirements.txt
```

That's it! No complex setup needed.

## First Run

### Option A: Quick Demo

Run a simple demo to verify everything works:

```bash
python demo_quick.py
```

You should see:
- System initializing
- Sample task submitted
- Agent processing
- Task completed

### Option B: Interactive Dashboard

Start the web dashboard:

```bash
cd dashboard/AIOS-Dashboard-v4.0
python server.py
```

Open http://127.0.0.1:8889 in your browser.

## Submit Your First Task

### Python API

```python
from task_queue import TaskQueue

# Initialize queue
queue = TaskQueue()

# Submit a task
task_id = queue.add_task(
    task_type="research",
    description="Search GitHub for AIOS projects",
    priority=1
)

print(f"Task submitted: {task_id}")

# Check status
status = queue.get_task_status(task_id)
print(f"Status: {status}")
```

### CLI

```bash
# Submit task
python cli.py submit --type research --desc "Search GitHub for AIOS"

# Check status
python cli.py status --task-id <task_id>

# List all tasks
python cli.py list-tasks
```

## What's Next?

### Enable Memory Server (Recommended)

Memory Server eliminates cold-start delays:

```bash
cd agent_system
python memory_server.py
```

Keep this running in the background.

### Explore Agents

List available agents:

```bash
python cli.py list-agents
```

View agent capabilities:

```bash
python cli.py agent-info --agent GitHub_Researcher
```

### Monitor System Health

```bash
python cli.py health-check
```

Output:
- Evolution Score
- Active agents
- Pending tasks
- System metrics

### Run Learning Loop

Enable self-improvement:

```bash
python cli.py trigger-learning
```

AIOS will analyze past failures and generate improvements.

## Common Tasks

### Research a GitHub Project

```python
queue.add_task(
    task_type="github_research",
    description="Analyze DeerFlow architecture",
    metadata={"repo": "deerflow/deerflow"}
)
```

### Code Review

```python
queue.add_task(
    task_type="code_review",
    description="Review scheduler.py changes",
    metadata={"file": "scheduler.py"}
)
```

### System Maintenance

```python
queue.add_task(
    task_type="maintenance",
    description="Clean old logs (>7 days)",
    metadata={"days": 7}
)
```

## Troubleshooting

### Task Stuck in Pending

**Solution**: Start the scheduler

```bash
python scheduler.py
```

### Agent Fails Immediately

**Solution**: Check agent logs

```bash
python cli.py agent-logs --agent <agent_id> --failed-only
```

### Memory Server Not Responding

**Solution**: Restart Memory Server

```bash
# Stop (Ctrl+C)
# Start again
python memory_server.py
```

## Configuration

### Customize Agents

Edit `agents.json`:

```json
{
  "agents": [
    {
      "id": "My_Custom_Agent",
      "name": "Custom Agent",
      "description": "Does custom things",
      "capabilities": ["custom"],
      "model": "claude-sonnet-4-6",
      "timeout": 120
    }
  ]
}
```

### Adjust Task Queue

Edit `config.yaml`:

```yaml
task_queue:
  max_retries: 3
  retry_delay: 60
  max_concurrent: 5
```

## Performance Tips

### 1. Use Memory Server
Eliminates 9s cold-start delay.

### 2. Optimize Storage
Run monthly:
```bash
python optimize_storage.py
```

### 3. Archive Old Events
Keep only recent data:
```bash
python cli.py archive-events --days 90
```

### 4. Monitor Performance
Track metrics:
```bash
python performance_monitor.py
```

## Next Steps

- Read [Architecture Guide](docs/ARCHITECTURE.md)
- Explore [Agent System](docs/AGENT_SYSTEM.md)
- Learn [Self-Improvement](docs/LEARNING_LOOP.md)
- Check [Performance Guide](docs/PERFORMANCE.md)

## Getting Help

- **Documentation**: `docs/`
- **Examples**: `examples/`
- **Issues**: GitHub Issues
- **Community**: Discord/Telegram

---

**Ready to build?** Start with `demo_quick.py` and explore from there.

**Questions?** Check `docs/FAQ.md` or open an issue.

**Want to contribute?** See `CONTRIBUTING.md`.

---

Last Updated: 2026-03-14
