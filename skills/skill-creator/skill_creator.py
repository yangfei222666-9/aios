#!/usr/bin/env python3
"""
Skill Creator - 把工作流转化成可复用的 Skill
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

WORKSPACE = Path(os.getenv("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
SKILLS_DIR = WORKSPACE / "skills"


def analyze_script(script_path: Path) -> Dict:
    """分析脚本，提取核心信息"""
    if not script_path.exists():
        raise FileNotFoundError(f"脚本不存在: {script_path}")
    
    content = script_path.read_text(encoding="utf-8")
    
    # 提取文档字符串
    docstring = extract_docstring(content)
    
    # 提取函数和类
    functions = extract_functions(content)
    classes = extract_classes(content)
    
    # 提取依赖
    dependencies = extract_dependencies(content)
    
    # 推断用途
    purpose = infer_purpose(script_path.name, docstring, functions, classes)
    
    # 提取关键词
    keywords = extract_keywords_from_code(content, functions, classes)
    
    return {
        "name": script_path.stem,
        "path": str(script_path),
        "docstring": docstring,
        "functions": functions,
        "classes": classes,
        "dependencies": dependencies,
        "purpose": purpose,
        "keywords": keywords
    }


def extract_docstring(content: str) -> str:
    """提取文档字符串"""
    # Python docstring
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 注释块
    match = re.search(r'^#\s*(.+?)(?:\n\n|\n#\s*$)', content, re.MULTILINE | re.DOTALL)
    if match:
        lines = match.group(1).split('\n')
        return '\n'.join(line.lstrip('# ').strip() for line in lines)
    
    return ""


def extract_functions(content: str) -> List[str]:
    """提取函数名"""
    return re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)


def extract_classes(content: str) -> List[str]:
    """提取类名"""
    return re.findall(r'^class\s+(\w+)\s*[:\(]', content, re.MULTILINE)


def extract_dependencies(content: str) -> List[str]:
    """提取依赖"""
    imports = re.findall(r'^(?:import|from)\s+([\w.]+)', content, re.MULTILINE)
    
    # 过滤标准库
    stdlib = {'os', 'sys', 're', 'json', 'pathlib', 'datetime', 'typing', 'subprocess'}
    return [imp for imp in set(imports) if imp.split('.')[0] not in stdlib]


def infer_purpose(filename: str, docstring: str, functions: List[str], classes: List[str]) -> str:
    """推断脚本用途"""
    text = (filename + " " + docstring + " " + " ".join(functions + classes)).lower()
    
    if any(k in text for k in ["monitor", "health", "check", "status"]):
        return "monitoring"
    elif any(k in text for k in ["backup", "cleanup", "organize"]):
        return "maintenance"
    elif any(k in text for k in ["search", "fetch", "scrape", "crawl"]):
        return "information"
    elif any(k in text for k in ["automate", "workflow", "task"]):
        return "automation"
    elif any(k in text for k in ["test", "ui", "screenshot"]):
        return "testing"
    elif any(k in text for k in ["agent", "aios", "orchestrat"]):
        return "aios"
    else:
        return "utility"


def extract_keywords_from_code(content: str, functions: List[str], classes: List[str]) -> List[str]:
    """从代码中提取关键词"""
    # 技术关键词
    tech_keywords = [
        "api", "http", "web", "server", "client", "database", "sql",
        "file", "json", "xml", "csv", "log", "config",
        "monitor", "health", "backup", "cleanup", "test", "automation",
        "agent", "task", "workflow", "schedule", "cron"
    ]
    
    text = content.lower()
    found = []
    
    for kw in tech_keywords:
        if kw in text:
            found.append(kw)
    
    # 从函数名提取
    for func in functions:
        words = re.findall(r'[a-z]+', func.lower())
        found.extend(words[:2])  # 前2个词
    
    return list(set(found))[:10]


def generate_skill_md(analysis: Dict, skill_name: str, description: str = None) -> str:
    """生成 SKILL.md"""
    if not description:
        description = analysis.get("docstring") or f"A skill for {analysis['purpose']}"
    
    # Frontmatter
    frontmatter = f"""---
name: {skill_name}
description: {description}
---

# {skill_name.replace('-', ' ').title()}

## 功能

{description}

## 使用方式

### 命令行

```bash
python {analysis['name']}.py [参数]
```

### 在 OpenClaw 中使用

当用户询问相关需求时，运行：

```bash
cd C:\\Users\\A\\.openclaw\\workspace\\skills\\{skill_name}
python {analysis['name']}.py
```

## 核心功能

"""
    
    # 函数列表
    if analysis.get("functions"):
        frontmatter += "### 主要函数\n\n"
        for func in analysis["functions"][:5]:
            frontmatter += f"- `{func}()` - {func.replace('_', ' ').title()}\n"
        frontmatter += "\n"
    
    # 依赖
    if analysis.get("dependencies"):
        frontmatter += "## 依赖\n\n"
        for dep in analysis["dependencies"]:
            frontmatter += f"- {dep}\n"
        frontmatter += "\n"
    
    # 分类和关键词
    frontmatter += f"""## 元数据

- **分类:** {analysis['purpose']}
- **关键词:** {', '.join(analysis['keywords'])}
- **创建时间:** {datetime.now().strftime('%Y-%m-%d')}

## 维护

如需修改此 skill，编辑 `{analysis['name']}.py` 并更新本文档。

---

**版本:** 1.0  
**创建者:** skill-creator  
**最后更新:** {datetime.now().strftime('%Y-%m-%d')}
"""
    
    return frontmatter


def create_skill(script_path: Path, skill_name: str = None, description: str = None) -> Path:
    """创建 skill"""
    # 分析脚本
    analysis = analyze_script(script_path)
    
    # 生成 skill 名称
    if not skill_name:
        skill_name = analysis["name"].replace("_", "-")
    
    # 创建 skill 目录
    skill_dir = SKILLS_DIR / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制脚本
    import shutil
    target_script = skill_dir / script_path.name
    shutil.copy2(script_path, target_script)
    
    # 生成 SKILL.md
    skill_md = generate_skill_md(analysis, skill_name, description)
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    
    # 生成 README.md（可选）
    readme = f"""# {skill_name}

{description or analysis.get('docstring', 'A useful skill')}

See [SKILL.md](SKILL.md) for details.
"""
    (skill_dir / "README.md").write_text(readme, encoding="utf-8")
    
    print(f"[OK] Skill created: {skill_dir}")
    print(f"[FILE] SKILL.md: {skill_dir / 'SKILL.md'}")
    print(f"[SCRIPT] {target_script}")
    
    return skill_dir


def interactive_create():
    """交互式创建 skill"""
    print("🎨 Skill Creator - 交互式创建\n")
    
    # 1. 选择脚本
    script_path = input("📂 脚本路径: ").strip()
    if not script_path:
        print("❌ 脚本路径不能为空")
        return
    
    script_path = Path(script_path)
    if not script_path.exists():
        print(f"❌ 脚本不存在: {script_path}")
        return
    
    # 2. 分析脚本
    print("\n🔍 分析脚本...")
    analysis = analyze_script(script_path)
    
    print(f"\n📊 分析结果:")
    print(f"   名称: {analysis['name']}")
    print(f"   用途: {analysis['purpose']}")
    print(f"   函数: {len(analysis['functions'])} 个")
    print(f"   类: {len(analysis['classes'])} 个")
    print(f"   依赖: {', '.join(analysis['dependencies']) if analysis['dependencies'] else '无'}")
    print(f"   关键词: {', '.join(analysis['keywords'])}")
    
    # 3. 输入元数据
    print("\n📝 输入元数据:")
    skill_name = input(f"   Skill 名称 [{analysis['name']}]: ").strip() or analysis['name']
    skill_name = skill_name.replace("_", "-")
    
    description = input(f"   描述 [{analysis.get('docstring', '...')[:50]}]: ").strip()
    if not description:
        description = analysis.get('docstring') or f"A skill for {analysis['purpose']}"
    
    # 4. 确认
    print(f"\n✅ 即将创建 skill: {skill_name}")
    confirm = input("   继续? [Y/n]: ").strip().lower()
    if confirm and confirm != 'y':
        print("❌ 已取消")
        return
    
    # 5. 创建
    skill_dir = create_skill(script_path, skill_name, description)
    
    print(f"\n🎉 完成！")
    print(f"\n下一步:")
    print(f"   1. 编辑 {skill_dir / 'SKILL.md'} 完善文档")
    print(f"   2. 测试 skill: cd {skill_dir} && python {script_path.name}")
    print(f"   3. 重建索引: cd ../find-skills && python find_skill.py rebuild")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # 交互式模式
        interactive_create()
    else:
        # 命令行模式
        script_path = Path(sys.argv[1])
        skill_name = sys.argv[2] if len(sys.argv) > 2 else None
        description = sys.argv[3] if len(sys.argv) > 3 else None
        
        create_skill(script_path, skill_name, description)
