import json

# 读取所有 Agent
agents = []
with open(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\agents.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            agents.append(json.loads(line))

# 过滤掉 coder-030524
agents = [a for a in agents if a["id"] != "coder-030524"]

# 写回文件
with open(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\agents.jsonl", "w", encoding="utf-8") as f:
    for agent in agents:
        f.write(json.dumps(agent, ensure_ascii=False) + "\n")

print(f"已删除 coder-030524，剩余 {len(agents)} 个 Agent")
