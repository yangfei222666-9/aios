#!/usr/bin/env python3
"""激活所有学习 Agent 去学习"""
import json
from pathlib import Path
from datetime import datetime
from paths import AGENTS_STATE, SPAWN_REQUESTS

agents_file = AGENTS_STATE
spawn_file = SPAWN_REQUESTS

# 读取 agents
agents_data = json.loads(agents_file.read_text(encoding='utf-8'))
learning_agents = [a for a in agents_data['agents'] if a.get('type') == 'learning']

print(f"找到 {len(learning_agents)} 个学习 Agent")
print("=" * 60)

# 为每个学习 Agent 创建学习任务
tasks = {
    "Document_Agent": "学习最新的文档处理技术和 NLP 方法",
    "Skill_Creator": "学习如何从代码中提取模式并生成更好的 Skill 文档",
    "Aios_Health_Check": "学习系统监控最佳实践和健康度评估方法",
    "Knowledge_Base_Manager": "学习知识管理和索引优化技术",
    "Feedback_Collector": "学习用户反馈分析和情感分析方法",
    "Documentation_Generator": "学习自动文档生成和代码注释最佳实践",
    "Error_Pattern_Learner": "学习错误模式识别和自动修复策略"
}

spawned = 0
for agent in learning_agents:
    agent_name = agent['name'].replace(' Agent', '').replace('_', '_')
    task = tasks.get(agent_name, f"学习 {agent_name} 相关的最新技术和最佳实践")
    
    spawn_request = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent['id'],
        "agent_name": agent['name'],
        "task": task,
        "priority": "normal",
        "source": "manual_activation",
        "status": "pending"
    }
    
    # 追加到 spawn_requests.jsonl
    with open(spawn_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(spawn_request, ensure_ascii=False) + '\n')
    
    print(f"[OK] {agent['name']}")
    print(f"  Task: {task}")
    spawned += 1

print(f"\n已创建 {spawned} 个学习任务")
print(f"spawn_requests.jsonl 已更新")
