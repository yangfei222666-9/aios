#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 3 个 Agent 的配置"""

from learning_agents import LEARNING_AGENTS

agents = [a for a in LEARNING_AGENTS if a['name'] in ['GitHub_Researcher', 'Error_Analyzer', 'Code_Reviewer']]

print("=== 3 个 Agent 配置检查 ===\n")

for a in agents:
    print(f"{a['name']}:")
    print(f"  schedule: {a.get('schedule')}")
    print(f"  interval_hours: {a.get('interval_hours')}")
    print(f"  priority: {a.get('priority')}")
    print(f"  tools: {a.get('tools')}")
    print(f"  model: {a.get('model')}")
    print()

print("\n=== 写回路径检查 ===\n")

import os
from pathlib import Path

paths = [
    "memory/github_research",
    "memory/error_analysis",
    "memory/code_review",
    "agent_execution_record.jsonl"
]

for p in paths:
    full_path = Path(__file__).parent / p
    exists = full_path.exists()
    status = "[OK]" if exists else "[MISSING]"
    print(f"{status} {p}: {full_path}")
