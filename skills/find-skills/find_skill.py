#!/usr/bin/env python3
"""
Find Skill - 智能 Skill 推荐系统 v2.0
"""
import sys
import json
from pathlib import Path
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from skill_index import build_index, save_index, load_index as load_idx
from skill_matcher import recommend_skill, search_skills, get_category_skills, increment_usage

WORKSPACE = Path(os.getenv("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
INDEX_FILE = WORKSPACE / "skills" / "find-skills" / "skills_index.json"


def format_skill_card(skill: dict, score: float = None) -> str:
    """格式化 skill 卡片"""
    lines = [
        f"📦 **{skill['name']}**",
        f"   {skill['description']}",
        f"   📂 分类: {skill['category']}",
    ]
    
    if skill.get("keywords"):
        lines.append(f"   🏷️  关键词: {', '.join(skill['keywords'][:5])}")
    
    if score is not None:
        lines.append(f"   🎯 匹配度: {score:.0%}")
    
    if skill.get("usage_count", 0) > 0:
        lines.append(f"   📊 使用次数: {skill['usage_count']}")
    
    return "\n".join(lines)


def cmd_search(query: str):
    """搜索命令"""
    print(f"🔍 搜索: {query}\n")
    
    result = recommend_skill(query)
    
    if not result["found"]:
        print(f"❌ {result['message']}")
        print("\n💡 建议:")
        for suggestion in result["suggestions"]:
            print(f"   • {suggestion}")
        return
    
    # 单个推荐
    if "recommended" in result:
        print("✅ 推荐:")
        print(format_skill_card(result["recommended"], result["confidence"]))
        
        if result.get("alternatives"):
            print("\n🔄 其他选择:")
            for alt in result["alternatives"]:
                print(f"   • {alt['name']} - {alt['description'][:50]}...")
    
    # 多个匹配
    elif result.get("multiple_matches"):
        print(f"找到 {len(result['results'])} 个相关 skill:\n")
        
        for i, item in enumerate(result["results"], 1):
            print(f"{i}. {format_skill_card(item['skill'], item['score'])}\n")
        
        # 对比
        if result.get("comparison"):
            comp = result["comparison"]
            print("📊 对比分析:")
            print(f"   共同点: {', '.join(comp['common_keywords']) if comp['common_keywords'] else '无'}")
            print("\n   独特特性:")
            for name, features in comp["unique_features"].items():
                if features:
                    print(f"      • {name}: {', '.join(features)}")


def cmd_list_categories():
    """列出所有分类"""
    index = load_idx()
    
    if not index:
        print("❌ 索引不存在，请先运行: python find_skill.py rebuild")
        return
    
    print("📋 Skill 分类:\n")
    
    for cat, skills in sorted(index["categories"].items()):
        print(f"📂 {cat} ({len(skills)} 个)")
        for skill_name in sorted(skills)[:3]:  # 只显示前3个
            skill = next((s for s in index["skills"] if s["name"] == skill_name), None)
            if skill:
                print(f"   • {skill_name} - {skill['description'][:40]}...")
        if len(skills) > 3:
            print(f"   ... 还有 {len(skills) - 3} 个")
        print()


def cmd_show_category(category: str):
    """显示某个分类的所有 skills"""
    skills = get_category_skills(category)
    
    if not skills:
        print(f"❌ 分类 '{category}' 不存在或为空")
        return
    
    print(f"📂 {category} ({len(skills)} 个):\n")
    
    for skill in skills:
        print(format_skill_card(skill))
        print()


def cmd_rebuild():
    """重建索引"""
    print("🔄 重建索引...")
    index = build_index()
    save_index(index)


def cmd_stats():
    """显示统计信息"""
    index = load_idx()
    
    if not index:
        print("❌ 索引不存在")
        return
    
    print("📊 统计信息:\n")
    print(f"总 Skills: {index['total']}")
    print(f"分类数: {len(index['categories'])}")
    print(f"最后更新: {index.get('last_updated', '未知')}")
    
    # Top 使用
    top_used = sorted(index["skills"], key=lambda s: s.get("usage_count", 0), reverse=True)[:5]
    if any(s.get("usage_count", 0) > 0 for s in top_used):
        print("\n🔥 最常用:")
        for skill in top_used:
            if skill.get("usage_count", 0) > 0:
                print(f"   • {skill['name']}: {skill['usage_count']} 次")


def main():
    if len(sys.argv) < 2:
        print("""
🔍 Find Skill v2.0 - 智能 Skill 推荐系统

用法:
  python find_skill.py search <查询>     搜索 skill
  python find_skill.py categories        列出所有分类
  python find_skill.py category <名称>   显示某个分类
  python find_skill.py rebuild           重建索引
  python find_skill.py stats             显示统计信息

示例:
  python find_skill.py search 监控服务器
  python find_skill.py category monitoring
        """)
        return
    
    cmd = sys.argv[1]
    
    # 确保索引存在
    if cmd != "rebuild" and not INDEX_FILE.exists():
        print("⚠️  索引不存在，正在创建...")
        cmd_rebuild()
        print()
    
    if cmd == "search":
        if len(sys.argv) < 3:
            print("❌ 请提供搜索查询")
            return
        query = " ".join(sys.argv[2:])
        cmd_search(query)
    
    elif cmd == "categories":
        cmd_list_categories()
    
    elif cmd == "category":
        if len(sys.argv) < 3:
            print("❌ 请提供分类名称")
            return
        cmd_show_category(sys.argv[2])
    
    elif cmd == "rebuild":
        cmd_rebuild()
    
    elif cmd == "stats":
        cmd_stats()
    
    else:
        print(f"❌ 未知命令: {cmd}")


if __name__ == "__main__":
    main()
