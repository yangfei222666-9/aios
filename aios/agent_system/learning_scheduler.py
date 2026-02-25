#!/usr/bin/env python3
"""学习 Agent 调度器 - 自动调度学习任务"""
import json
import time
from pathlib import Path
from datetime import datetime
from learning_agents import LEARNING_AGENTS, get_agent_config

WORKSPACE = Path(__file__).parent.parent.parent
STATE_FILE = WORKSPACE / "memory" / "selflearn-state.json"
SPAWN_REQUESTS = Path(__file__).parent / "spawn_requests.jsonl"

def load_state():
    """加载状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def should_run_agent(agent_name, agent_config, state):
    """检查 Agent 是否需要运行"""
    last_run_key = f"last_{agent_name.lower()}"
    last_run = state.get(last_run_key)
    
    if not last_run:
        return True
    
    last_time = datetime.fromisoformat(last_run)
    now = datetime.now()
    delta = (now - last_time).total_seconds()
    
    # 使用 interval_hours 而不是 schedule
    interval_hours = agent_config.get('interval_hours', 24)
    interval_seconds = interval_hours * 3600
    
    return delta > interval_seconds

def spawn_agent(agent_config):
    """创建 Agent Spawn 请求"""
    task_description = f"""
你是 {agent_config['role']}。

**目标：** {agent_config['goal']}

**背景：** {agent_config['backstory']}

**任务：**
{chr(10).join(f"- {task}" for task in agent_config['tasks'])}

**要求：**
1. 记录学习内容到 memory/{datetime.now().strftime('%Y-%m-%d')}.md
2. 提取核心思路（不要只是罗列项目）
3. 对比我们的 AIOS（优势、缺口、可借鉴）
4. 给出具体的改进建议（可执行的）

**输出格式：**
```
## {agent_config['role']}学习报告（{datetime.now().strftime('%Y-%m-%d %H:%M')}）

### 发现
- ...

### 对比
- 优势：...
- 缺口：...

### 建议
- ...
```
"""
    
    request = {
        "agent_name": agent_config['name'],
        "task": task_description,
        "model": agent_config.get('model', 'claude-sonnet-4-6'),
        "thinking": agent_config.get('thinking', 'off'),
        "priority": agent_config.get('priority', 'normal'),
        "created_at": datetime.now().isoformat()
    }
    
    # 追加到 spawn_requests.jsonl
    SPAWN_REQUESTS.parent.mkdir(parents=True, exist_ok=True)
    with open(SPAWN_REQUESTS, 'a', encoding='utf-8') as f:
        f.write(json.dumps(request, ensure_ascii=False) + '\n')
    
    return request

def main():
    """主函数"""
    state = load_state()
    spawned = []
    
    # 检查每个 Agent 是否需要运行
    for agent_config in LEARNING_AGENTS:
        agent_name = agent_config['name']
        
        if should_run_agent(agent_name, agent_config, state):
            # 创建 Spawn 请求
            request = spawn_agent(agent_config)
            spawned.append(agent_name)
            
            # 更新状态
            last_run_key = f"last_{agent_name.lower()}"
            state[last_run_key] = datetime.now().isoformat()
    
    # 保存状态
    if spawned:
        save_state(state)
        print(f"LEARNING_AGENTS_SPAWNED:{len(spawned)}")
        print(f"已创建学习任务：{', '.join(spawned)}")
    else:
        print("LEARNING_AGENTS_OK")

if __name__ == '__main__':
    main()
