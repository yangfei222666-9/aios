import json
from pathlib import Path
from datetime import datetime, timedelta

base = Path('C:/Users/A/.openclaw/workspace/aios/agent_system')
today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

exec_file = base / TASK_EXECUTIONS
agents_file = base / 'agents.json'
lessons_file = base / 'lessons.json'
evolution_file = base / 'evolution_score.json'
hexagram_file = base / 'hexagram_state.json'
try:
    from paths import TASK_QUEUE as _TQ, SPAWN_REQUESTS as _SR
    queue_file = _TQ
    spawn_file = _SR
except ImportError:
    queue_file = base / 'data' / 'task_queue.jsonl'
    spawn_file = base / 'data' / 'spawn_requests.jsonl'

# Task executions (24h)
executions = []
if exec_file.exists():
    for line in exec_file.read_text(encoding='utf-8').splitlines():
        try:
            e = json.loads(line)
            ts = e.get('timestamp', '')
            if ts[:10] in [today, yesterday]:
                executions.append(e)
        except:
            pass

success = [e for e in executions if e.get('status') == 'completed']
failed = [e for e in executions if e.get('status') == 'failed']
print(f"exec_24h={len(executions)} success={len(success)} failed={len(failed)}")

# Agent stats
if agents_file.exists():
    agents = json.loads(agents_file.read_text(encoding='utf-8'))
    print(f"agents_total={len(agents)}")
    for a in agents:
        aid = a.get('id', 'unknown')
        s = a.get('stats', {})
        done = s.get('tasks_completed', 0)
        fail = s.get('tasks_failed', 0)
        print(f"agent|{aid}|done={done}|fail={fail}")

# Evolution score
if evolution_file.exists():
    ev = json.loads(evolution_file.read_text(encoding='utf-8'))
    print(f"evolution={json.dumps(ev)}")

# Hexagram
if hexagram_file.exists():
    hx = json.loads(hexagram_file.read_text(encoding='utf-8'))
    print(f"hexagram={json.dumps(hx)}")

# Lessons
if lessons_file.exists():
    lessons = []
    for line in lessons_file.read_text(encoding='utf-8').splitlines():
        try:
            lessons.append(json.loads(line))
        except:
            pass
    print(f"lessons_total={len(lessons)}")
    recent = [l for l in lessons if l.get('timestamp', '')[:10] in [today, yesterday]]
    print(f"lessons_recent={len(recent)}")

# Queue
if queue_file.exists():
    queue = []
    for line in queue_file.read_text(encoding='utf-8').splitlines():
        try:
            queue.append(json.loads(line))
        except:
            pass
    pending = [q for q in queue if q.get('status') == 'pending']
    completed = [q for q in queue if q.get('status') == 'completed']
    print(f"queue_total={len(queue)} queue_pending={len(pending)} queue_completed={len(completed)}")

# Spawn requests (24h)
if spawn_file.exists():
    spawns = []
    for line in spawn_file.read_text(encoding='utf-8').splitlines():
        try:
            s = json.loads(line)
            if s.get('timestamp', '')[:10] in [today, yesterday]:
                spawns.append(s)
        except:
            pass
    print(f"spawns_24h={len(spawns)}")


