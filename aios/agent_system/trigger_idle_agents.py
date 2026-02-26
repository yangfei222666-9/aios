"""
触发所有从未运行的学习Agent
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from learning_agents import LEARNING_AGENTS

workspace = Path("C:/Users/A/.openclaw/workspace")
state_file = workspace / "memory" / "selflearn-state.json"
spawn_file = Path(__file__).parent / "spawn_requests.jsonl"

# 读取状态
state = {}
if state_file.exists():
    with open(state_file, encoding="utf-8") as f:
        state = json.load(f)

# 找出从未运行的Agent
never_run = []
for agent in LEARNING_AGENTS:
    name = agent["name"]
    last_run_key = f"last_{name.lower()}"
    if not state.get(last_run_key):
        never_run.append(agent)

print(f"从未运行的学习Agent: {len(never_run)} 个\n")

# 为每个Agent创建spawn请求
spawned = 0
for agent in never_run:
    task = f"""你是 {agent['role']}。

**目标：** {agent['goal']}

**背景：** {agent.get('backstory', '')}

**任务：**
{chr(10).join('- ' + t for t in agent.get('tasks', []))}

**要求：**
1. 记录学习内容到 memory/{datetime.now().strftime('%Y-%m-%d')}.md
2. 提取核心思路（不要只是罗列项目）
3. 对比我们的 AIOS（优势、缺口、可借鉴）
4. 给出具体的改进建议（可执行的）
"""

    request = {
        "agent_name": agent["name"],
        "task": task,
        "model": agent.get("model", "claude-sonnet-4-6"),
        "thinking": agent.get("thinking", "off"),
        "priority": agent.get("priority", "normal"),
        "created_at": datetime.now().isoformat()
    }

    with open(spawn_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(request, ensure_ascii=False) + "\n")

    # 更新状态
    state[f"last_{agent['name'].lower()}"] = datetime.now().isoformat()
    spawned += 1
    print(f"  {spawned}. {agent['name']} -> spawn 请求已创建")

# 保存状态
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print(f"\n✓ 已为 {spawned} 个Agent创建spawn请求")
print("等待心跳处理...")
