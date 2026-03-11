"""Quick tech debt scanner for TaijiOS"""
import json, os, glob

DATA = "data"

def check_agents():
    path = os.path.join(DATA, "agents.json")
    if not os.path.exists(path):
        print("agents.json NOT FOUND")
        return
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Handle both list and dict formats
    if isinstance(raw, dict):
        agents = raw.get("agents", [])
        if isinstance(agents, dict):
            agents = list(agents.values())
    else:
        agents = raw
    total = len(agents)
    has_status = 0
    routable = 0
    for a in agents:
        if isinstance(a, dict):
            if "status" in a:
                has_status += 1
            if a.get("routable"):
                routable += 1
    print(f"=== Agents: {total} total ===")
    print(f"  has 'status' field: {has_status}/{total}")
    print(f"  routable: {routable}/{total}")
    # Check run scripts
    run_scripts = [f for f in os.listdir(".") if f.startswith("run_") and f.endswith(".py")]
    print(f"  run_*.py scripts: {len(run_scripts)}")
    for s in run_scripts:
        print(f"    - {s}")

def check_selflearn():
    for p in [os.path.join(DATA, "selflearn-state.json"), 
              os.path.join("..", "..", "memory", "selflearn-state.json")]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                sl = json.load(f)
            print(f"\n=== selflearn-state.json ({p}) ===")
            for k, v in sl.items():
                val_str = str(v)
                if len(val_str) > 80:
                    val_str = val_str[:80] + "..."
                print(f"  {k}: {val_str}")
            return
    print("\n=== selflearn-state.json: NOT FOUND ===")

def check_lessons():
    path = os.path.join(DATA, "lessons.json")
    if not os.path.exists(path):
        print("\n=== lessons.json: NOT FOUND ===")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, list):
        lessons = data
        rules = []
    elif isinstance(data, dict):
        lessons = data.get("lessons", [])
        rules = data.get("rules_derived", [])
    else:
        print("\nlessons.json: unexpected format")
        return
    
    print(f"\n=== lessons.json ===")
    print(f"  lessons: {len(lessons)}")
    statuses = {}
    empty_content = 0
    for l in lessons:
        s = l.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
        if not l.get("content") and not l.get("description") and not l.get("rule"):
            empty_content += 1
    for s, c in statuses.items():
        print(f"    {s}: {c}")
    print(f"  empty content: {empty_content}")
    print(f"  rules_derived: {len(rules)}")

def check_queue():
    path = os.path.join(DATA, "task_queue.jsonl")
    if not os.path.exists(path):
        print("\n=== task_queue.jsonl: NOT FOUND ===")
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    print(f"\n=== task_queue.jsonl: {len(lines)} entries ===")
    statuses = {}
    for line in lines:
        try:
            t = json.loads(line)
            s = t.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        except:
            pass
    for s, c in statuses.items():
        print(f"  {s}: {c}")

def check_execution_records():
    path = os.path.join(DATA, "agent_execution_record.jsonl")
    if not os.path.exists(path):
        print("\n=== execution_record: NOT FOUND ===")
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    print(f"\n=== execution_record: {len(lines)} entries ===")
    agents_seen = set()
    outcomes = {}
    for line in lines:
        try:
            r = json.loads(line)
            agents_seen.add(r.get("agent_id", "unknown"))
            o = r.get("outcome", "unknown")
            outcomes[o] = outcomes.get(o, 0) + 1
        except:
            pass
    print(f"  unique agents executed: {len(agents_seen)}")
    for o, c in outcomes.items():
        print(f"  {o}: {c}")

def check_key_files():
    print("\n=== Key Files ===")
    files = [
        "agent_status.py",
        "heartbeat_v5.py",
        "heartbeat_demo.py",
        "heartbeat_full.py",
        "memory_server.py",
        "notifier.py",
        "backup.py",
        "restore.py",
    ]
    for f in files:
        exists = os.path.exists(f)
        print(f"  {f}: {'YES' if exists else 'MISSING'}")

def check_spawn():
    path = os.path.join(DATA, "spawn_pending.jsonl")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"\n=== spawn_pending.jsonl: {len(lines)} pending ===")
    else:
        print("\n=== spawn_pending.jsonl: empty/not found ===")

    path2 = os.path.join(DATA, "spawn_results.jsonl")
    if os.path.exists(path2):
        with open(path2, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"=== spawn_results.jsonl: {len(lines)} results ===")

if __name__ == "__main__":
    check_agents()
    check_selflearn()
    check_lessons()
    check_queue()
    check_execution_records()
    check_spawn()
    check_key_files()
