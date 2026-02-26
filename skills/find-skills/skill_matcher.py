#!/usr/bin/env python3
"""
Skill Matcher - 智能匹配算法
"""
import json
from typing import List, Dict, Tuple
from pathlib import Path
import os

WORKSPACE = Path(os.getenv("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
INDEX_FILE = WORKSPACE / "skills" / "find-skills" / "skills_index.json"


def load_index() -> Dict:
    """加载索引"""
    if not INDEX_FILE.exists():
        return {"skills": [], "categories": {}}
    
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


# 中文关键词映射表
CN_KEYWORD_MAP = {
    # 监控相关
    "监控": ["monitor", "monitoring", "watch", "check"],
    "服务器": ["server", "host", "machine"],
    "系统": ["system", "os"],
    "健康": ["health", "status"],
    "资源": ["resource", "usage"],
    "性能": ["performance", "perf"],
    
    # 自动化相关
    "自动化": ["automation", "automate", "automatic"],
    "工作流": ["workflow", "flow"],
    "任务": ["task", "job"],
    "定时": ["schedule", "cron", "timer"],
    
    # 信息相关
    "新闻": ["news", "article"],
    "搜索": ["search", "find", "query"],
    "网页": ["web", "page", "site"],
    "抓取": ["scrape", "crawl", "fetch"],
    
    # 维护相关
    "备份": ["backup", "archive"],
    "清理": ["cleanup", "clean", "clear"],
    "整理": ["organize", "sort"],
    "文件": ["file", "document"],
    
    # UI相关
    "界面": ["ui", "interface", "gui"],
    "测试": ["test", "testing"],
    "截图": ["screenshot", "capture"],
    "窗口": ["window", "windows"],
    
    # 其他
    "文档": ["document", "doc", "documentation"],
    "代码": ["code", "coding"],
    "数据": ["data"],
    "配置": ["config", "configuration"],
}


def translate_cn_query(query: str) -> str:
    """将中文查询翻译为英文关键词"""
    query_lower = query.lower()
    translated = []
    
    # 检查每个中文关键词
    for cn_word, en_words in CN_KEYWORD_MAP.items():
        if cn_word in query_lower:
            translated.extend(en_words)
    
    # 如果有翻译，返回翻译后的查询
    if translated:
        return " ".join(translated)
    
    # 否则返回原查询
    return query


def calculate_similarity(query: str, skill: Dict) -> float:
    """计算查询与 skill 的相似度（0-1）
    
    注意：query 应该已经是翻译后的英文查询
    """
    query_lower = query.lower()
    score = 0.0
    
    # 1. 名称匹配（权重 0.3）
    name_lower = skill["name"].lower()
    query_words = set(query_lower.split())
    name_words = set(name_lower.replace('-', ' ').replace('_', ' ').split())
    name_matches = len(query_words & name_words)
    if name_matches > 0:
        score += 0.3 * (name_matches / len(query_words))
    
    # 2. 描述匹配（权重 0.2）
    desc_lower = skill["description"].lower()
    desc_matches = sum(1 for word in query_words if word in desc_lower)
    if desc_matches > 0:
        score += 0.2 * (desc_matches / len(query_words))
    
    # 3. 关键词匹配（权重 0.4，提高权重）
    keyword_matches = len(query_words & set(skill["keywords"]))
    if keyword_matches > 0:
        score += 0.4 * (keyword_matches / len(query_words))
    
    # 4. 使用频率加成（权重 0.1）
    usage_bonus = min(skill.get("usage_count", 0) / 10, 0.1)
    score += usage_bonus
    
    return min(score, 1.0)


def search_skills(query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
    """搜索 skills 并返回匹配结果"""
    index = load_index()
    
    if not index["skills"]:
        return []
    
    # 翻译中文查询
    translated_query = translate_cn_query(query)
    
    # 计算所有 skill 的相似度（使用翻译后的查询）
    results = []
    for skill in index["skills"]:
        similarity = calculate_similarity(translated_query, skill)
        if similarity > 0.01:  # 降低阈值到 1%
            results.append((skill, similarity))
    
    # 按相似度排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_k]


def get_category_skills(category: str) -> List[Dict]:
    """获取某个分类的所有 skills"""
    index = load_index()
    
    if category not in index["categories"]:
        return []
    
    skill_names = index["categories"][category]
    return [s for s in index["skills"] if s["name"] in skill_names]


def compare_skills(skill_names: List[str]) -> Dict:
    """对比多个 skills"""
    index = load_index()
    skills = [s for s in index["skills"] if s["name"] in skill_names]
    
    if not skills:
        return {}
    
    comparison = {
        "skills": skills,
        "common_keywords": set(skills[0]["keywords"]),
        "unique_features": {}
    }
    
    # 找出共同关键词
    for skill in skills[1:]:
        comparison["common_keywords"] &= set(skill["keywords"])
    
    # 找出独特特性
    for skill in skills:
        unique = set(skill["keywords"]) - comparison["common_keywords"]
        comparison["unique_features"][skill["name"]] = list(unique)
    
    comparison["common_keywords"] = list(comparison["common_keywords"])
    
    return comparison


def recommend_skill(query: str) -> Dict:
    """智能推荐（主入口）"""
    results = search_skills(query, top_k=3)
    
    if not results:
        return {
            "found": False,
            "message": f"没有找到与 '{query}' 相关的 skill",
            "suggestions": ["试试更具体的关键词", "或者浏览所有分类"]
        }
    
    # 如果只有1个高相关度结果，直接推荐
    if len(results) == 1 or results[0][1] > 0.7:
        best = results[0][0]
        return {
            "found": True,
            "recommended": best,
            "confidence": results[0][1],
            "alternatives": [r[0] for r in results[1:]] if len(results) > 1 else []
        }
    
    # 多个相似结果，提供对比
    return {
        "found": True,
        "multiple_matches": True,
        "results": [{"skill": r[0], "score": r[1]} for r in results],
        "comparison": compare_skills([r[0]["name"] for r in results])
    }


def increment_usage(skill_name: str):
    """增加 skill 使用计数"""
    index = load_index()
    
    for skill in index["skills"]:
        if skill["name"] == skill_name:
            skill["usage_count"] = skill.get("usage_count", 0) + 1
            break
    
    # 保存更新后的索引
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python skill_matcher.py <查询>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    result = recommend_skill(query)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
