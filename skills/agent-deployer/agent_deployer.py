#!/usr/bin/env python3
"""
Agent Deployer - 将 Skill 配置转换为 AIOS Agent

核心功能：
1. 读取 skill.yaml 配置
2. 生成 Agent System Prompt
3. 注入到 agents.json
4. 一键挂载到 AIOS

Usage:
    python agent_deployer.py deploy <skill_dir>
    python agent_deployer.py list
    python agent_deployer.py remove <agent_name>
"""

import json
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 路径配置
WORKSPACE = Path(__file__).parent.parent.parent
AGENTS_JSON = WORKSPACE / "aios" / "agent_system" / "agents.json"
SKILLS_DIR = WORKSPACE / "skills"


def load_skill_config(skill_dir: Path) -> Dict[str, Any]:
    """加载 Skill 配置文件"""
    config_file = skill_dir / "skill.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_system_prompt(config: Dict[str, Any]) -> str:
    """根据 Skill 配置生成 Agent System Prompt"""
    name = config['name']
    description = config['description'].strip()
    parameters = config.get('parameters', [])
    examples = config.get('examples', [])
    
    # 构建参数说明
    params_doc = []
    for param in parameters:
        param_name = param['name']
        param_type = param['type']
        required = "必填" if param.get('required', False) else "可选"
        default = f"，默认值: {param['default']}" if 'default' in param else ""
        param_desc = param.get('description', '')
        
        params_doc.append(f"  - {param_name} ({param_type}, {required}{default}): {param_desc}")
    
    params_section = "\n".join(params_doc) if params_doc else "  无参数"
    
    # 构建示例说明
    examples_doc = []
    for i, example in enumerate(examples, 1):
        input_str = json.dumps(example['input'], ensure_ascii=False, indent=2)
        output_str = example['output']
        examples_doc.append(f"示例 {i}:\n输入: {input_str}\n输出: {output_str}")
    
    examples_section = "\n\n".join(examples_doc) if examples_doc else "暂无示例"
    
    # 生成完整 Prompt
    prompt = f"""你是 {name} Agent，专门负责以下任务：

{description}

## 参数说明
{params_section}

## 使用示例
{examples_section}

## 执行规则
1. 接收用户请求后，提取所需参数
2. 验证参数完整性和合法性
3. 调用底层脚本执行任务
4. 解析输出结果，返回给用户
5. 如果执行失败，分析错误原因并给出建议

## 输出格式
- 成功时：简洁描述结果 + 关键数据
- 失败时：错误原因 + 解决建议

始终保持专业、高效、友好的沟通风格。
"""
    return prompt


def generate_agent_config(config: Dict[str, Any], skill_dir: Path) -> Dict[str, Any]:
    """生成 Agent 配置（用于注入 agents.json）"""
    name = config['name']
    category = config.get('category', 'general')
    execution = config.get('execution', {})
    
    # 构建执行命令
    entry_file = skill_dir / execution.get('entry', 'main.py')
    command_template = execution.get('command', f"python {entry_file} {{params}}")
    
    agent_config = {
        "name": name,
        "type": category,
        "role": f"{name} Specialist",
        "goal": config['description'].strip().split('\n')[0],  # 取第一行作为 goal
        "backstory": f"专门负责 {name} 相关任务的 Agent，基于 Skill 自动生成。",
        "system_prompt": generate_system_prompt(config),
        "execution": {
            "type": execution.get('type', 'python'),
            "entry": str(entry_file),
            "command": command_template,
            "sandbox": execution.get('sandbox', {
                "network": True,
                "filesystem": "read-only",
                "timeout": 60
            })
        },
        "output": config.get('output', {
            "type": "text",
            "success_pattern": "^SUCCESS:",
            "error_pattern": "^ERROR:"
        }),
        "metadata": {
            "source": "skill",
            "skill_dir": str(skill_dir),
            "skill_version": config.get('version', '1.0.0'),  # 新增：Skill 版本
            "created": datetime.now().isoformat(),
            "last_synced": datetime.now().isoformat(),  # 新增：最后同步时间
            "version": config.get('version', '1.0.0'),
            "author": config.get('metadata', {}).get('author', 'unknown'),
            "tags": config.get('metadata', {}).get('tags', [])
        },
        "state": {
            "status": "active",
            "tasks_completed": 0,
            "tasks_failed": 0,
            "last_active": None
        }
    }
    
    return agent_config


def deploy_agent(skill_dir: Path) -> None:
    """部署 Agent 到 AIOS"""
    # 1. 加载 Skill 配置
    print(f"[DEPLOY] Loading Skill config: {skill_dir.name}")
    config = load_skill_config(skill_dir)
    
    # 2. 生成 Agent 配置
    print(f"[DEPLOY] Generating Agent config: {config['name']}")
    agent_config = generate_agent_config(config, skill_dir)
    
    # 3. 读取现有 agents.json
    if not AGENTS_JSON.exists():
        agents_data = {"agents": [], "metadata": {"last_updated": None}}
    else:
        with open(AGENTS_JSON, 'r', encoding='utf-8') as f:
            agents_data = json.load(f)
        
        # 确保 metadata 字段存在
        if 'metadata' not in agents_data:
            agents_data['metadata'] = {"last_updated": None}
    
    # 4. 检查是否已存在
    existing_names = [a['name'] for a in agents_data['agents']]
    if config['name'] in existing_names:
        print(f"[WARN] Agent '{config['name']}' already exists, will overwrite")
        agents_data['agents'] = [a for a in agents_data['agents'] if a['name'] != config['name']]
    
    # 5. 添加新 Agent
    agents_data['agents'].append(agent_config)
    agents_data['metadata']['last_updated'] = datetime.now().isoformat()
    
    # 6. 写回 agents.json
    with open(AGENTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(agents_data, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Agent '{config['name']}' deployed!")
    print(f"  Type: {agent_config['type']}")
    print(f"  Version: {agent_config['metadata']['version']}")
    print(f"  Config: {AGENTS_JSON}")


def list_deployed_agents() -> None:
    """列出所有已部署的 Skill-based Agents"""
    if not AGENTS_JSON.exists():
        print("[ERROR] agents.json not found")
        return
    
    with open(AGENTS_JSON, 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
    
    skill_agents = [a for a in agents_data['agents'] if a.get('metadata', {}).get('source') == 'skill']
    
    if not skill_agents:
        print("[INFO] No Skill-based Agents deployed")
        return
    
    print(f"[LIST] Deployed Skill-based Agents ({len(skill_agents)} total):\n")
    for agent in skill_agents:
        name = agent['name']
        agent_type = agent['type']
        version = agent['metadata']['version']
        status = agent['state']['status']
        tasks = agent['state']['tasks_completed']
        
        print(f"  - {name} (v{version})")
        print(f"    Type: {agent_type} | Status: {status} | Tasks: {tasks}")
        print()


def remove_agent(agent_name: str) -> None:
    """移除指定 Agent"""
    if not AGENTS_JSON.exists():
        print("[ERROR] agents.json not found")
        return
    
    with open(AGENTS_JSON, 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
    
    original_count = len(agents_data['agents'])
    agents_data['agents'] = [a for a in agents_data['agents'] if a['name'] != agent_name]
    
    if len(agents_data['agents']) == original_count:
        print(f"[ERROR] Agent '{agent_name}' not found")
        return
    
    agents_data['metadata']['last_updated'] = datetime.now().isoformat()
    
    with open(AGENTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(agents_data, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Agent '{agent_name}' removed")


def check_skill_updates() -> List[Dict[str, Any]]:
    """检查 Skill 是否有更新"""
    if not AGENTS_JSON.exists():
        print("[ERROR] agents.json not found")
        return []
    
    with open(AGENTS_JSON, 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
    
    updates_available = []
    
    for agent in agents_data['agents']:
        # 只检查来自 Skill 的 Agent
        if agent.get('metadata', {}).get('source') != 'skill':
            continue
        
        skill_dir = Path(agent['metadata']['skill_dir'])
        if not skill_dir.exists():
            continue
        
        # 读取 Skill 当前版本
        try:
            config = load_skill_config(skill_dir)
            current_version = config.get('version', '1.0.0')
            agent_version = agent['metadata'].get('skill_version', '0.0.0')
            
            # 比较版本（简单字符串比较）
            if current_version != agent_version:
                updates_available.append({
                    "agent_name": agent['name'],
                    "skill_dir": str(skill_dir),
                    "current_version": agent_version,
                    "new_version": current_version
                })
        except Exception as e:
            print(f"[WARN] Failed to check {agent['name']}: {e}")
    
    return updates_available


def sync_agent_with_skill(agent_name: str) -> None:
    """同步 Agent 与 Skill"""
    if not AGENTS_JSON.exists():
        print("[ERROR] agents.json not found")
        return
    
    with open(AGENTS_JSON, 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
    
    # 找到目标 Agent
    agent = None
    for a in agents_data['agents']:
        if a['name'] == agent_name:
            agent = a
            break
    
    if not agent:
        print(f"[ERROR] Agent '{agent_name}' not found")
        return
    
    # 检查是否来自 Skill
    if agent.get('metadata', {}).get('source') != 'skill':
        print(f"[ERROR] Agent '{agent_name}' is not from a Skill")
        return
    
    skill_dir = Path(agent['metadata']['skill_dir'])
    if not skill_dir.exists():
        print(f"[ERROR] Skill directory not found: {skill_dir}")
        return
    
    # 重新读取 Skill 配置
    print(f"[SYNC] Syncing {agent_name} with Skill...")
    config = load_skill_config(skill_dir)
    
    # 更新 Agent 配置
    agent['goal'] = config['description'].strip().split('\n')[0]
    agent['system_prompt'] = generate_system_prompt(config)
    agent['metadata']['skill_version'] = config.get('version', '1.0.0')
    agent['metadata']['last_synced'] = datetime.now().isoformat()
    
    # 保存
    agents_data['metadata']['last_updated'] = datetime.now().isoformat()
    with open(AGENTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(agents_data, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Agent '{agent_name}' synced to Skill v{agent['metadata']['skill_version']}")


def sync_all_agents() -> None:
    """同步所有 Agent 与 Skill"""
    updates = check_skill_updates()
    
    if not updates:
        print("[INFO] All Agents are up-to-date")
        return
    
    print(f"[SYNC] Found {len(updates)} Agents to sync:\n")
    for update in updates:
        print(f"  - {update['agent_name']}: {update['current_version']} → {update['new_version']}")
    
    print("\n[SYNC] Starting sync...")
    for update in updates:
        sync_agent_with_skill(update['agent_name'])
    
    print(f"\n[SUCCESS] Synced {len(updates)} Agents")


def batch_deploy(skills_dir: Path = SKILLS_DIR) -> Dict[str, Any]:
    """批量部署所有有 skill.yaml 的 Skill"""
    print(f"[BATCH] Scanning {skills_dir} for Skills...")
    
    deployed = []
    skipped = []
    errors = []
    
    # 扫描所有子目录
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        
        skill_name = skill_dir.name
        
        # 检查是否有 skill.yaml
        config_file = skill_dir / "skill.yaml"
        if not config_file.exists():
            skipped.append({"name": skill_name, "reason": "no skill.yaml"})
            continue
        
        # 尝试部署
        try:
            print(f"\n[{len(deployed) + 1}] Deploying {skill_name}...")
            config = load_skill_config(skill_dir)
            agent_config = generate_agent_config(config, skill_dir)
            
            # 读取现有 agents.json
            if not AGENTS_JSON.exists():
                agents_data = {"agents": [], "metadata": {"last_updated": None}}
            else:
                with open(AGENTS_JSON, 'r', encoding='utf-8') as f:
                    agents_data = json.load(f)
                
                if 'metadata' not in agents_data:
                    agents_data['metadata'] = {"last_updated": None}
            
            # 检查是否已存在（覆盖）
            existing_names = [a['name'] for a in agents_data['agents']]
            if config['name'] in existing_names:
                agents_data['agents'] = [a for a in agents_data['agents'] if a['name'] != config['name']]
                print(f"  [OVERWRITE] Existing Agent '{config['name']}'")
            
            # 添加新 Agent
            agents_data['agents'].append(agent_config)
            agents_data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # 写回 agents.json
            with open(AGENTS_JSON, 'w', encoding='utf-8') as f:
                json.dump(agents_data, f, indent=2, ensure_ascii=False)
            
            deployed.append({
                "name": config['name'],
                "skill_dir": skill_name,
                "version": agent_config['metadata']['version']
            })
            print(f"  [OK] {config['name']} v{agent_config['metadata']['version']}")
            
        except Exception as e:
            errors.append({"name": skill_name, "error": str(e)})
            print(f"  [FAIL] {skill_name}: {e}")
    
    # 统计报告
    print("\n" + "=" * 60)
    print(f"[BATCH] Deployment Complete")
    print("=" * 60)
    print(f"  Deployed: {len(deployed)}")
    print(f"  Skipped:  {len(skipped)}")
    print(f"  Errors:   {len(errors)}")
    
    if deployed:
        print("\n[DEPLOYED]")
        for item in deployed:
            print(f"  - {item['name']} (v{item['version']}) <- {item['skill_dir']}")
    
    if skipped:
        print("\n[SKIPPED]")
        for item in skipped:
            print(f"  - {item['name']}: {item['reason']}")
    
    if errors:
        print("\n[ERRORS]")
        for item in errors:
            print(f"  - {item['name']}: {item['error']}")
    
    return {
        "deployed": deployed,
        "skipped": skipped,
        "errors": errors
    }


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python agent_deployer.py deploy <skill_dir>")
        print("  python agent_deployer.py deploy --batch")
        print("  python agent_deployer.py list")
        print("  python agent_deployer.py remove <agent_name>")
        print("  python agent_deployer.py check-updates")
        print("  python agent_deployer.py sync <agent_name>")
        print("  python agent_deployer.py sync --all")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "deploy":
        # 检查是否是批量部署
        if len(sys.argv) >= 3 and sys.argv[2] == "--batch":
            batch_deploy()
        else:
            if len(sys.argv) < 3:
                print("[ERROR] Please specify Skill directory or use --batch")
                sys.exit(1)
            
            skill_dir = Path(sys.argv[2])
            if not skill_dir.is_absolute():
                skill_dir = SKILLS_DIR / skill_dir
            
            if not skill_dir.exists():
                print(f"[ERROR] Skill directory not found: {skill_dir}")
                sys.exit(1)
            
            deploy_agent(skill_dir)
    
    elif command == "list":
        list_deployed_agents()
    
    elif command == "remove":
        if len(sys.argv) < 3:
            print("[ERROR] Please specify Agent name")
            sys.exit(1)
        
        remove_agent(sys.argv[2])
    
    elif command == "check-updates":
        updates = check_skill_updates()
        if not updates:
            print("[INFO] All Agents are up-to-date")
        else:
            print(f"[UPDATES] Found {len(updates)} Agents with updates:\n")
            for update in updates:
                print(f"  - {update['agent_name']}")
                print(f"    Current: {update['current_version']}")
                print(f"    New:     {update['new_version']}")
                print()
    
    elif command == "sync":
        if len(sys.argv) < 3:
            print("[ERROR] Please specify Agent name or use --all")
            sys.exit(1)
        
        if sys.argv[2] == "--all":
            sync_all_agents()
        else:
            sync_agent_with_skill(sys.argv[2])
    
    else:
        print(f"[ERROR] Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
