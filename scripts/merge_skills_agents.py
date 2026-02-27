#!/usr/bin/env python3
"""
Skill → Agent 融合工具

自动将所有 Skill 转换为可调度的 AIOS Agent
"""

import os
import json
import re
from pathlib import Path


def parse_skill_md(skill_path: Path) -> dict:
    """解析 SKILL.md 文件"""
    skill_md = skill_path / "SKILL.md"
    
    if not skill_md.exists():
        return None
    
    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取 frontmatter
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return None
    
    frontmatter = frontmatter_match.group(1)
    
    # 解析字段
    skill_info = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # 处理数组
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip() for v in value[1:-1].split(',')]
            
            skill_info[key] = value
    
    # 提取描述（frontmatter 后的第一段）
    description_match = re.search(r'---\n\n# .*?\n\n(.*?)\n\n', content, re.DOTALL)
    if description_match:
        skill_info['long_description'] = description_match.group(1).strip()
    
    return skill_info


def skill_to_agent(skill_name: str, skill_info: dict, skill_path: Path) -> dict:
    """将 Skill 转换为 Agent 配置"""
    
    # 查找主脚本
    main_script = None
    for ext in ['.py', '.sh', '.js']:
        candidates = list(skill_path.glob(f"*{ext}"))
        if candidates:
            main_script = candidates[0].name
            break
    
    if not main_script:
        main_script = f"{skill_name}.py"
    
    # 生成 Agent 配置
    agent = {
        "name": skill_name.replace('-', '_'),
        "role": skill_info.get('description', f"{skill_name} Agent"),
        "goal": skill_info.get('long_description', skill_info.get('description', '')),
        "backstory": f"你是一个专门负责 {skill_info.get('description', skill_name)} 的 Agent。",
        "tasks": [
            f"执行 {skill_name} 的核心功能",
            "根据用户请求调用相应的命令",
            "返回执行结果"
        ],
        "tools": ["exec", "read", "write"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "on-demand",
        "skill_path": str(skill_path),
        "main_script": main_script,
        "category": skill_info.get('category', 'general'),
        "tags": skill_info.get('tags', [])
    }
    
    return agent


def generate_agents_from_skills(skills_dir: Path, output_file: Path):
    """从所有 Skill 生成 Agent 配置"""
    
    agents = []
    
    # 遍历所有 Skill
    for skill_path in sorted(skills_dir.iterdir()):
        if not skill_path.is_dir():
            continue
        
        skill_name = skill_path.name
        
        # 解析 SKILL.md
        skill_info = parse_skill_md(skill_path)
        if not skill_info:
            print(f"⚠️  跳过 {skill_name}（没有 SKILL.md）")
            continue
        
        # 转换为 Agent
        agent = skill_to_agent(skill_name, skill_info, skill_path)
        agents.append(agent)
        
        print(f"✅ {skill_name} → {agent['name']}")
    
    # 保存到文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('"""Skill-based Agents - 从 Skills 自动生成的 Agent 配置"""\n\n')
        f.write(f"SKILL_AGENTS = {json.dumps(agents, indent=4, ensure_ascii=False)}\n")
    
    print(f"\n📄 已生成 {len(agents)} 个 Agent 配置 → {output_file}")
    
    return agents


def merge_with_learning_agents(skill_agents_file: Path, learning_agents_file: Path, output_file: Path):
    """合并 Skill Agents 和 Learning Agents"""
    
    # 读取 Skill Agents
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_agents", skill_agents_file)
    skill_agents_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(skill_agents_module)
    skill_agents = skill_agents_module.SKILL_AGENTS
    
    # 读取 Learning Agents
    spec = importlib.util.spec_from_file_location("learning_agents", learning_agents_file)
    learning_agents_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(learning_agents_module)
    learning_agents = learning_agents_module.LEARNING_AGENTS
    
    # 合并
    all_agents = {
        "learning_agents": learning_agents,
        "skill_agents": skill_agents
    }
    
    # 保存
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('"""All AIOS Agents - Learning Agents + Skill Agents"""\n\n')
        f.write(f"ALL_AGENTS = {json.dumps(all_agents, indent=4, ensure_ascii=False)}\n")
    
    print(f"\n📄 已合并 {len(learning_agents)} 个 Learning Agents + {len(skill_agents)} 个 Skill Agents")
    print(f"   → {output_file}")
    
    return all_agents


def main():
    """主函数"""
    workspace = Path(__file__).parent.parent
    skills_dir = workspace / "skills"
    agent_system_dir = workspace / "aios" / "agent_system"
    
    print("🚀 开始融合 Skills 和 Agents...\n")
    
    # Step 1: 从 Skills 生成 Agents
    skill_agents_file = agent_system_dir / "skill_agents.py"
    skill_agents = generate_agents_from_skills(skills_dir, skill_agents_file)
    
    # Step 2: 合并 Learning Agents 和 Skill Agents
    learning_agents_file = agent_system_dir / "learning_agents.py"
    all_agents_file = agent_system_dir / "all_agents.py"
    all_agents = merge_with_learning_agents(skill_agents_file, learning_agents_file, all_agents_file)
    
    print("\n🎉 融合完成！")
    print(f"\n📊 统计:")
    print(f"   Learning Agents: {len(all_agents['learning_agents'])}")
    print(f"   Skill Agents: {len(all_agents['skill_agents'])}")
    print(f"   总计: {len(all_agents['learning_agents']) + len(all_agents['skill_agents'])}")


if __name__ == "__main__":
    main()
