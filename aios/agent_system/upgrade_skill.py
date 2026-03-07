#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速升级 Skill 为 Agent

Usage:
    python upgrade_skill.py aios-backup
    python upgrade_skill.py aios-cleanup
"""

import json
import re
import sys
import io
from pathlib import Path
from datetime import datetime

# 修复 Windows 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

AIOS_DIR = Path(__file__).parent
WORKSPACE = AIOS_DIR.parent.parent
AGENTS_FILE = AIOS_DIR / "agents.json"
SKILLS_DIR = WORKSPACE / "skills"


def upgrade_skill(skill_name):
    """升级 Skill 为 Agent"""
    skill_dir = SKILLS_DIR / skill_name
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        print(f"❌ SKILL.md 不存在: {skill_md}")
        return False
    
    # 读取 SKILL.md 提取 description
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'description:\s*(.+)', content)
        description = match.group(1).strip() if match else f"{skill_name} Agent"
    
    # 读取 agents.json
    if not AGENTS_FILE.exists():
        print(f"❌ agents.json 不存在: {AGENTS_FILE}")
        return False
    
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查是否已存在
    for agent in data.get('agents', []):
        if agent.get('name') == skill_name:
            print(f"⚠️  {skill_name} 已经是 Agent 了")
            return False
    
    # 创建新 Agent 配置
    new_agent = {
        "name": skill_name,
        "role": description,
        "goal": f"Execute {skill_name} skill tasks",
        "system_prompt": f"You are {skill_name} Agent. {description}",
        "type": "skill-based",
        "state": {
            "status": "active",
            "last_active": datetime.now().isoformat()
        },
        "stats": {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 100.0
        }
    }
    
    # 添加到 agents 列表
    data.setdefault('agents', []).append(new_agent)
    
    # 写回文件
    with open(AGENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {skill_name} 已成功升级为 Agent")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upgrade_skill.py <skill_name>")
        print("\nExample:")
        print("  python upgrade_skill.py aios-backup")
        sys.exit(1)
    
    skill_name = sys.argv[1]
    success = upgrade_skill(skill_name)
    sys.exit(0 if success else 1)
