"""
agents.json 治理脚本
1. 备份原文件
2. 删除3个重复 Agent（保留已运行的 canonical 版本）
3. 标记4个 deprecated
4. 标记12个 standby
"""
import json
import shutil
from pathlib import Path

from paths import AGENTS_STATE

AGENTS_FILE = AGENTS_STATE
BACKUP_FILE = AGENTS_STATE.with_suffix('.json.backup')

# 删除（重复项，保留 canonical）
TO_REMOVE = {
    "Document_Agent Agent",
    "Skill_Creator Agent",
    "Aios_Health_Check Agent",
}

# 标记 deprecated（功能已被其他组件覆盖）
TO_DEPRECATED = {
    "Task_Queue_Processor",
    "Coder_Failure_Analyzer",
    "Auto_Fixer",
    "Error_Pattern_Learner",
}

# 标记 standby（有价值但未接入调度）
TO_STANDBY = {
    "Resource_Monitor",
    "Data_Pipeline",
    "Workflow_Designer",
    "Security_Auditor",
    "Feedback_Collector",
    "Documentation_Generator",
    "Experiment_Runner",
    "Task_Decomposer",
    "Context_Manager",
    "Visualization_Generator",
    "Health_Monitor",
    "Camera_Monitor",
}

# 备份
shutil.copy2(AGENTS_FILE, BACKUP_FILE)
print(f"[OK] 备份 → {BACKUP_FILE}")

with open(AGENTS_FILE, encoding="utf-8") as f:
    data = json.load(f)

agents = data.get("agents", data) if isinstance(data, dict) else data
is_dict = isinstance(data, dict)

removed, deprecated, standby = [], [], []
new_agents = []

for agent in agents:
    name = agent.get("name", agent.get("id", ""))
    if name in TO_REMOVE:
        removed.append(name)
        continue  # 删除
    if name in TO_DEPRECATED:
        agent["status"] = "deprecated"
        deprecated.append(name)
    elif name in TO_STANDBY:
        agent["status"] = "standby"
        standby.append(name)
    new_agents.append(agent)

if is_dict:
    data["agents"] = new_agents
    out = data
else:
    out = new_agents

with open(AGENTS_FILE, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"[OK] 删除重复项 ({len(removed)}): {removed}")
print(f"[OK] 标记 deprecated ({len(deprecated)}): {deprecated}")
print(f"[OK] 标记 standby ({len(standby)}): {standby}")
print(f"[OK] agents.json 已更新，共 {len(new_agents)} 个 Agent")
