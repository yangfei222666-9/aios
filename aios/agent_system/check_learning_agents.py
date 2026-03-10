#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 Learning Agents 状态"""

import json
from pathlib import Path

def check_learning_agents():
    agents_file = Path(__file__).parent / "agents.json"
    
    with open(agents_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    learning_agents = [a for a in data["agents"] if a["group"] == "learning"]
    active_learning = [a for a in learning_agents if a["enabled"] == True]
    
    print(f"Total Learning Agents: {len(learning_agents)}")
    print(f"Active Learning Agents: {len(active_learning)}")
    print()
    
    print("Active Learning Agents:")
    for agent in active_learning:
        stats = agent["stats"]
        print(f"  - {agent['name']}: {stats['tasks_total']} tasks (completed: {stats['tasks_completed']}, failed: {stats['tasks_failed']})")
    
    print()
    print("Shadow/Disabled Learning Agents:")
    inactive = [a for a in learning_agents if not a["enabled"]]
    for agent in inactive[:5]:
        print(f"  - {agent['name']}: mode={agent['mode']}")
    if len(inactive) > 5:
        print(f"  ... and {len(inactive) - 5} more")

if __name__ == "__main__":
    check_learning_agents()
