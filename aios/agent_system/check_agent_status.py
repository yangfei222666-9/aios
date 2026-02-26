"""检查 Agent 状态"""
import json
from pathlib import Path
from datetime import datetime

workspace = Path(__file__).parent.parent.parent

# 检查 agents.jsonl
agents_file = workspace / "aios" / "agent_system" / "data" / "agents.jsonl"
print("=== Agent 列表 ===")
if agents_file.exists():
    agents = []
    with open(agents_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                agents.append(json.loads(line))
    
    if agents:
        for agent in agents:
            created = agent.get("created_at", "N/A")
            if created != "N/A":
                created = created[:19]
            print(f"{agent['id']}: {agent['status']} (type={agent.get('type', 'N/A')}, env={agent.get('env', 'N/A')}, created={created})")
    else:
        print("无 Agent 记录")
else:
    print("agents.jsonl 不存在")

print()

# 检查 agent_configs.json
config_file = workspace / "aios" / "agent_system" / "data" / "agent_configs.json"
print("=== Agent 配置 ===")
if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        agents = data.get('agents', {})
        for agent_id, config in agents.items():
            print(f"{agent_id}:")
            print(f"  Type: {config.get('type')}")
            print(f"  Env: {config.get('env')}")
            print(f"  Priority: {config.get('priority')}")
            print(f"  Timeout: {config.get('timeout')}s")
            print(f"  Role: {config.get('role', 'N/A')}")
            print()
else:
    print("agent_configs.json 不存在")

print()

# 检查任务队列
queue_file = workspace / "aios" / "agent_system" / "task_queue.jsonl"
print("=== 任务队列 ===")
if queue_file.exists():
    tasks = []
    with open(queue_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    
    if tasks:
        print(f"待处理任务: {len(tasks)}")
        for task in tasks[-5:]:  # 最近5个
            print(f"  {task.get('id')}: {task.get('type')} - {task.get('status', 'pending')}")
    else:
        print("队列为空")
else:
    print("task_queue.jsonl 不存在")

print()

# 检查 spawn_requests
spawn_file = workspace / "aios" / "agent_system" / "spawn_requests.jsonl"
print("=== Spawn 请求 ===")
if spawn_file.exists():
    requests = []
    with open(spawn_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))
    
    if requests:
        print(f"待处理请求: {len(requests)}")
        for req in requests[-3:]:  # 最近3个
            print(f"  {req.get('task_id')}: {req.get('label')} - {req.get('role', 'N/A')}")
    else:
        print("无待处理请求")
else:
    print("spawn_requests.jsonl 不存在")

print()

# 检查 loop_state.json
loop_state_file = workspace / "aios" / "agent_system" / "data" / "loop_state.json"
print("=== Self-Improving Loop 状态 ===")
if loop_state_file.exists():
    with open(loop_state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        last_improvement = state.get('last_improvement', {})
        if last_improvement:
            print("最近改进:")
            for agent_id, timestamp in last_improvement.items():
                print(f"  {agent_id}: {timestamp[:19]}")
        else:
            print("无改进记录")
else:
    print("loop_state.json 不存在")
