"""
AIOS Agent 执行器 - 处理 spawn 请求
读取 spawn_requests.jsonl，通过 sessions_spawn 真正执行
"""
import json
from pathlib import Path
from datetime import datetime

SPAWN_REQUESTS = Path(__file__).parent / "spawn_requests.jsonl"
SPAWN_RESULTS = Path(__file__).parent / "spawn_results.jsonl"
AGENTS_FILE = Path(__file__).parent / "agents.json"

def load_agents():
    """加载 Agent 配置"""
    if not AGENTS_FILE.exists():
        return {}
    
    with open(AGENTS_FILE, encoding="utf-8") as f:
        data = json.load(f)
        agents = {}
        for agent in data.get("agents", []):
            agents[agent["name"]] = agent
        return agents

def load_spawn_requests():
    """加载 spawn 请求"""
    if not SPAWN_REQUESTS.exists():
        return []
    
    with open(SPAWN_REQUESTS, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def execute_spawn_request(request, agent_config):
    """
    执行 spawn 请求
    
    返回：sessions_spawn 命令字符串
    """
    agent_name = request["agent_id"]
    description = request["description"]
    
    # 构建任务提示
    if agent_config:
        system_prompt = agent_config.get("system_prompt", "")
        task = f"""{system_prompt}

**任务描述：** {description}

**要求：**
1. 按照 system_prompt 中的规则执行
2. 返回结构化结果（JSON 或文本）
3. 如果失败，给出错误原因和建议
"""
    else:
        task = description
    
    # 返回 sessions_spawn 命令
    return {
        "agentId": agent_name,
        "task": task,
        "label": f"aios-{request['task_id']}",
        "cleanup": "keep"
    }

def main():
    """主函数"""
    print("=" * 60)
    print("AIOS Agent 执行器")
    print("=" * 60)
    
    # 加载配置
    agents = load_agents()
    print(f"✅ 加载了 {len(agents)} 个 Agent")
    
    # 加载 spawn 请求
    requests = load_spawn_requests()
    if not requests:
        print("⏭️  没有待执行的 spawn 请求")
        return
    
    print(f"📋 发现 {len(requests)} 个 spawn 请求")
    
    # 生成执行命令
    commands = []
    for i, request in enumerate(requests, 1):
        agent_id = request["agent_id"]
        agent_config = agents.get(agent_id)
        
        if not agent_config:
            print(f"⚠️  [{i}] Agent '{agent_id}' 不存在，跳过")
            continue
        
        cmd = execute_spawn_request(request, agent_config)
        commands.append(cmd)
        
        print(f"✅ [{i}] {agent_id}: {request['description'][:50]}...")
    
    # 输出执行命令（JSON 格式，供 OpenClaw 调用）
    print("\n" + "=" * 60)
    print("执行命令（复制到 OpenClaw）：")
    print("=" * 60)
    
    for cmd in commands:
        print(json.dumps(cmd, ensure_ascii=False, indent=2))
        print()
    
    # 保存到文件
    output_file = Path(__file__).parent / "spawn_commands.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(commands, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 命令已保存到：{output_file}")
    print("\n使用方式：")
    print("在 OpenClaw 中调用 sessions_spawn，传入上述参数")

if __name__ == "__main__":
    main()
