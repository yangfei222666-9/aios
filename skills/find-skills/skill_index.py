#!/usr/bin/env python3
"""
Skill Index Builder - 扫描本地 skills 并构建索引
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path(os.getenv("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
SKILLS_DIR = WORKSPACE / "skills"
INDEX_FILE = WORKSPACE / "skills" / "find-skills" / "skills_index.json"


def extract_skill_metadata(skill_path: Path) -> Optional[Dict]:
    """从 SKILL.md 提取元数据"""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None
    
    try:
        content = skill_md.read_text(encoding="utf-8")
        
        # 提取 frontmatter
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        name = skill_path.name
        description = ""
        
        if frontmatter_match:
            fm = frontmatter_match.group(1)
            name_match = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
            desc_match = re.search(r'^description:\s*(.+)$', fm, re.MULTILINE)
            
            if name_match:
                name = name_match.group(1).strip()
            if desc_match:
                description = desc_match.group(1).strip()
        
        # 提取第一个标题作为备用描述
        if not description:
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                description = title_match.group(1).strip()
        
        # 提取关键词（从描述中）
        keywords = extract_keywords(description + " " + content[:500])
        
        # 提取分类（基于关键词）
        category = categorize_skill(name, description, keywords)
        
        return {
            "name": name,
            "path": str(skill_path.relative_to(SKILLS_DIR)),
            "description": description,
            "keywords": keywords,
            "category": category,
            "usage_count": 0  # 初始使用次数
        }
    except Exception as e:
        print(f"⚠️  解析 {skill_path.name} 失败: {e}")
        return None


def extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词"""
    # 常见技术关键词
    tech_keywords = [
        "agent", "automation", "monitor", "backup", "cleanup", "health",
        "news", "search", "todoist", "telegram", "github", "docker",
        "server", "system", "resource", "cpu", "memory", "disk",
        "ui", "test", "screenshot", "windows", "web", "api",
        "file", "organize", "ripgrep", "grep", "search",
        "aios", "orchestration", "team", "workflow"
    ]
    
    text_lower = text.lower()
    found = []
    
    for kw in tech_keywords:
        if kw in text_lower:
            found.append(kw)
    
    return list(set(found))[:10]  # 最多10个关键词


def categorize_skill(name: str, description: str, keywords: List[str]) -> str:
    """自动分类 skill"""
    text = (name + " " + description).lower()
    
    # 分类规则
    if any(k in text for k in ["monitor", "health", "resource", "system", "server"]):
        return "monitoring"
    elif any(k in text for k in ["backup", "cleanup", "organize", "file"]):
        return "maintenance"
    elif any(k in text for k in ["news", "search", "web", "fetch"]):
        return "information"
    elif any(k in text for k in ["automation", "workflow", "orchestration", "team"]):
        return "automation"
    elif any(k in text for k in ["ui", "test", "screenshot", "windows"]):
        return "ui-tools"
    elif any(k in text for k in ["aios", "agent"]):
        return "aios"
    elif any(k in text for k in ["todoist", "task", "todo"]):
        return "productivity"
    else:
        return "other"


def build_index() -> Dict:
    """构建完整索引"""
    if not SKILLS_DIR.exists():
        print(f"❌ Skills 目录不存在: {SKILLS_DIR}")
        return {"skills": [], "categories": {}, "version": "2.0"}
    
    skills = []
    categories = {}
    
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith("."):
            continue
        
        metadata = extract_skill_metadata(skill_dir)
        if metadata:
            skills.append(metadata)
            
            # 分类统计
            cat = metadata["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(metadata["name"])
    
    return {
        "skills": skills,
        "categories": categories,
        "total": len(skills),
        "version": "2.0",
        "last_updated": None  # 会在保存时自动填充
    }


def save_index(index: Dict):
    """保存索引到文件"""
    from datetime import datetime
    index["last_updated"] = datetime.now().isoformat()
    
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ 索引已保存: {INDEX_FILE}")
    print(f"📊 总计 {index['total']} 个 skills，{len(index['categories'])} 个分类")


def load_index() -> Optional[Dict]:
    """加载索引"""
    if not INDEX_FILE.exists():
        return None
    
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️  加载索引失败: {e}")
        return None


if __name__ == "__main__":
    print("🔍 扫描本地 skills...")
    index = build_index()
    save_index(index)
    
    print("\n📋 分类统计:")
    for cat, skills in sorted(index["categories"].items()):
        print(f"  {cat}: {len(skills)} 个")
