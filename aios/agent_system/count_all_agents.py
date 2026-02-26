"""
统计所有 Agent 信息
"""
import json
from pathlib import Path

workspace = Path("C:/Users/A/.openclaw/workspace")

print("=" * 80)
print("所有 Agent 统计")
print("=" * 80)
print()

# 1. agents.json (运行时 Agent)
agents_file = workspace / "aios" / "agent_system" / "data" / "agents.json"
runtime_agents = []
if agents_file.exists():
    with open(agents_file, encoding="utf-8") as f:
        runtime_agents = json.load(f).get("agents", [])

print(f"1. 运行时 Agent (agents.json): {len(runtime_agents)} 个")
for agent in runtime_agents:
    print(f"   - {agent.get('id')}: {agent.get('type')} ({agent.get('status')})")
print()

# 2. agent_configs.json (配置)
configs_file = workspace / "aios" / "agent_system" / "data" / "agent_configs.json"
config_agents = {}
if configs_file.exists():
    with open(configs_file, encoding="utf-8") as f:
        data = json.load(f)
        config_agents = data.get("agents", {})

print(f"2. Agent 配置 (agent_configs.json): {len(config_agents)} 个")
for agent_id, config in config_agents.items():
    print(f"   - {agent_id}: {config.get('type')} ({config.get('env')})")
print()

# 3. 学习 Agent (spawn_requests 历史)
spawn_file = workspace / "aios" / "agent_system" / "spawn_requests.jsonl"
learning_agents = set()
if spawn_file.exists():
    with open(spawn_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    req = json.loads(line)
                    agent_name = req.get("agent_name")
                    if agent_name:
                        learning_agents.add(agent_name)
                except:
                    pass

print(f"3. 学习 Agent (spawn_requests 历史): {len(learning_agents)} 个")
for agent_name in sorted(learning_agents):
    print(f"   - {agent_name}")
print()

# 总计
total = len(runtime_agents) + len(config_agents) + len(learning_agents)
print("=" * 80)
print(f"总计: {total} 个 Agent 相关记录")
print(f"  - 运行时: {len(runtime_agents)}")
print(f"  - 配置: {len(config_agents)}")
print(f"  - 学习历史: {len(learning_agents)}")
print("=" * 80)
