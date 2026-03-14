"""
Recommendation Quality Test - 10 真实任务类型样例验证

目标：
1. 验证 Top1/Top3/fallback 是否符合人类直觉
2. 加入 recommendation_quality 三档评分（good/acceptable/poor）
3. 统计采纳率、合理率

评分标准：
  good       - Top1 明显正确，业务相关性强
  acceptable - Top1 合理但不是最优，或 Top3 中有正确答案
  poor       - Top1 明显错误，Top3 也没有合理选项
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORT_FILE = DATA_DIR / "recommendation_quality_report.json"

sys.path.insert(0, str(BASE_DIR))
from skill_memory import skill_memory, SkillMemory
from paths import DATA_DIR as _DATA_DIR


# ── 推荐引擎（Phase 3 校准版）────────────────────────────────────────────────

# 任务类型 → 领域关键词映射（精确规则）
TASK_DOMAIN_MAP = {
    "pdf": ["pdf", "document", "doc"],
    "git": ["git", "commit", "push", "branch", "repo", "version"],
    "api": ["api", "http", "request", "endpoint", "rest", "test"],
    "docker": ["docker", "container", "image", "build", "deploy"],
    "code": ["code", "python", "script", "refactor", "debug"],
    "analysis": ["analysis", "analyze", "report", "data", "metric"],
    "monitor": ["monitor", "health", "status", "alert", "check"],
    "file": ["file", "organize", "folder", "directory", "move"],
}

# 最低领域相关性门槛（Top1 必须满足）
DOMAIN_MATCH_THRESHOLD = 0.5  # skill_id 或 skill_name 包含领域关键词


def _contains_keyword(text: str, keyword: str) -> bool:
    """关键词匹配：优先用单词边界，避免 doc ⊂ docker 这种误匹配"""
    import re
    text = text.lower()
    keyword = keyword.lower()
    # 使用单词边界匹配（适用于英文关键词）
    if re.search(rf"\b{re.escape(keyword)}\b", text):
        return True
    # 兼容中文/复合词：允许包含，但避免过短关键词误匹配
    if len(keyword) >= 4 and keyword in text:
        return True
    return False


def get_task_domain(task_type: str) -> Optional[str]:
    """从任务类型推断领域（避免短词误匹配）"""
    task_lower = task_type.lower()
    # 关键词按长度降序，提高精确度
    for domain, keywords in TASK_DOMAIN_MAP.items():
        ordered = sorted(keywords, key=len, reverse=True)
        if any(_contains_keyword(task_lower, kw) for kw in ordered):
            return domain
    return None


def is_domain_relevant(skill: Dict, domain: str) -> bool:
    """判断 skill 是否与领域相关"""
    if not domain:
        return True
    keywords = TASK_DOMAIN_MAP.get(domain, [domain])
    sid = skill.get("skill_id", "").lower()
    sname = skill.get("skill_name", "").lower()
    return any(_contains_keyword(sid, kw) or _contains_keyword(sname, kw) for kw in keywords)


def recommend_skills(task_type: str, task_desc: str = "") -> Dict:
    """
    Phase 3 校准版推荐引擎

    策略：
    1. 先过滤领域相关 skill（精确规则）
    2. 领域内按 evolution_score 排序 → Top1
    3. fallback：同领域其他 skill，再全局最高分
    4. Top3 = 领域相关 + 全局补充

    Returns:
        {
            "task_type": ...,
            "domain": ...,
            "top1": {...},
            "top3": [...],
            "fallback": {...},
            "domain_matched": bool,
            "reasoning": str
        }
    """
    all_skills = skill_memory.get_all_skills()
    if not all_skills:
        return {"task_type": task_type, "top1": None, "top3": [], "fallback": None,
                "domain_matched": False, "reasoning": "no skills available"}

    domain = get_task_domain(task_type)

    # 领域相关 skill
    domain_skills = [s for s in all_skills if is_domain_relevant(s, domain)] if domain else []
    domain_skills.sort(key=lambda s: s.get("evolution_score", 0), reverse=True)

    # 全局排序（fallback 用）
    global_skills = sorted(all_skills, key=lambda s: s.get("evolution_score", 0), reverse=True)

    # Top1：领域内最高分（有门槛）
    top1 = domain_skills[0] if domain_skills else global_skills[0]
    domain_matched = bool(domain_skills)

    # Top3：领域内 + 全局补充（去重）
    seen_ids = set()
    top3 = []
    for s in domain_skills + global_skills:
        if s["skill_id"] not in seen_ids:
            top3.append(s)
            seen_ids.add(s["skill_id"])
        if len(top3) >= 3:
            break

    # Fallback：领域内第二名，或全局第二名
    fallback_candidates = [s for s in (domain_skills if domain_skills else global_skills)
                           if s["skill_id"] != top1["skill_id"]]
    fallback = fallback_candidates[0] if fallback_candidates else None

    # 推理说明
    if domain_matched:
        reasoning = f"领域 '{domain}' 匹配 {len(domain_skills)} 个 skill，Top1 按 evolution_score 排序"
    else:
        reasoning = f"无领域匹配，使用全局最高分 skill（evolution_score={top1.get('evolution_score', 0):.1f}）"

    return {
        "task_type": task_type,
        "domain": domain,
        "top1": _format_skill(top1),
        "top3": [_format_skill(s) for s in top3],
        "fallback": _format_skill(fallback) if fallback else None,
        "domain_matched": domain_matched,
        "reasoning": reasoning,
    }


def _format_skill(s: Optional[Dict]) -> Optional[Dict]:
    if not s:
        return None
    return {
        "skill_id": s["skill_id"],
        "skill_name": s.get("skill_name", s["skill_id"]),
        "evolution_score": round(s.get("evolution_score", 0), 1),
        "success_rate": round(s.get("success_rate", 0), 3),
        "usage_count": s.get("usage_count", 0),
    }


# ── 10 个真实任务类型样例 ────────────────────────────────────────────────────

TEST_CASES = [
    # (task_type, task_desc, expected_top1_domain, human_label)
    # human_label: 人类直觉期望的 Top1 skill_id（用于评分）
    {
        "id": 1,
        "task_type": "pdf extraction",
        "task_desc": "从 PDF 文件中提取文本内容",
        "expected_domain": "pdf",
        "expected_top1": "pdf-skill",
        "notes": "最典型的 pdf 任务，Top1 必须是 pdf-skill"
    },
    {
        "id": 2,
        "task_type": "git commit and push",
        "task_desc": "提交代码变更并推送到远程仓库",
        "expected_domain": "git",
        "expected_top1": "git-skill",
        "notes": "明确的 git 操作"
    },
    {
        "id": 3,
        "task_type": "api endpoint testing",
        "task_desc": "测试 REST API 接口的响应和性能",
        "expected_domain": "api",
        "expected_top1": "api-testing-skill",
        "notes": "API 测试场景"
    },
    {
        "id": 4,
        "task_type": "docker container build",
        "task_desc": "构建 Docker 镜像并运行容器",
        "expected_domain": "docker",
        "expected_top1": "docker-skill",
        "notes": "Docker 操作"
    },
    {
        "id": 5,
        "task_type": "pdf merge multiple files",
        "task_desc": "合并多个 PDF 文件为一个",
        "expected_domain": "pdf",
        "expected_top1": "pdf-skill",
        "notes": "PDF 合并，仍然是 pdf-skill"
    },
    {
        "id": 6,
        "task_type": "git branch management",
        "task_desc": "创建新分支、切换分支、合并分支",
        "expected_domain": "git",
        "expected_top1": "git-skill",
        "notes": "Git 分支管理"
    },
    {
        "id": 7,
        "task_type": "http request validation",
        "task_desc": "验证 HTTP 请求的状态码和响应体",
        "expected_domain": "api",
        "expected_top1": "api-testing-skill",
        "notes": "HTTP 验证，属于 api 领域"
    },
    {
        "id": 8,
        "task_type": "code analysis and refactor",
        "task_desc": "分析代码质量并重构",
        "expected_domain": "code",
        "expected_top1": None,  # 没有 code-skill，期望 fallback 合理
        "notes": "无直接匹配 skill，测试 fallback 行为"
    },
    {
        "id": 9,
        "task_type": "document processing",
        "task_desc": "处理文档，提取关键信息",
        "expected_domain": "pdf",  # document → pdf 领域
        "expected_top1": "pdf-skill",
        "notes": "document 关键词应映射到 pdf 领域"
    },
    {
        "id": 10,
        "task_type": "deploy application",
        "task_desc": "部署应用到生产环境",
        "expected_domain": "docker",  # deploy → docker 领域
        "expected_top1": "docker-skill",
        "notes": "deploy 关键词应映射到 docker 领域"
    },
]

# 更新 TASK_DOMAIN_MAP 以覆盖 document 和 deploy
TASK_DOMAIN_MAP["pdf"].extend(["document", "extract", "merge", "split"])
TASK_DOMAIN_MAP["docker"].extend(["deploy", "deployment", "container", "run"])


# ── 评分函数 ─────────────────────────────────────────────────────────────────

def score_recommendation(result: Dict, test_case: Dict) -> Tuple[str, str]:
    """
    评分推荐质量

    Returns:
        (quality, reason)
        quality: "good" | "acceptable" | "poor"
    """
    top1 = result.get("top1")
    top3 = result.get("top3", [])
    expected = test_case.get("expected_top1")
    domain_matched = result.get("domain_matched", False)

    top3_ids = [s["skill_id"] for s in top3 if s]

    # Case 1: 有期望 Top1
    if expected:
        if top1 and top1["skill_id"] == expected:
            return "good", f"Top1 精确匹配期望 '{expected}'"
        elif expected in top3_ids:
            return "acceptable", f"Top1 不是期望，但 Top3 包含 '{expected}'"
        else:
            return "poor", f"Top1={top1['skill_id'] if top1 else 'None'}，期望 '{expected}'，Top3 也未包含"

    # Case 2: 无期望 Top1（测试 fallback）
    else:
        fallback = result.get("fallback")
        if not domain_matched and top1:
            return "acceptable", f"无领域匹配，全局 fallback 到 '{top1['skill_id']}'（合理）"
        elif domain_matched and top1:
            return "good", f"领域匹配，Top1='{top1['skill_id']}'"
        else:
            return "poor", "无推荐结果"


# ── 主测试流程 ────────────────────────────────────────────────────────────────

def run_quality_test() -> Dict:
    """运行 10 个样例测试，输出质量报告"""
    print("=" * 65)
    print("  Recommendation Quality Test - 10 Real Task Samples")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    results = []
    quality_counts = {"good": 0, "acceptable": 0, "poor": 0}

    for tc in TEST_CASES:
        result = recommend_skills(tc["task_type"], tc["task_desc"])
        quality, reason = score_recommendation(result, tc)
        quality_counts[quality] += 1

        top1 = result.get("top1")
        top3_ids = [s["skill_id"] for s in result.get("top3", []) if s]
        fallback = result.get("fallback")

        # 打印
        icon = {"good": "✅", "acceptable": "⚠️", "poor": "❌"}[quality]
        print(f"\n[{tc['id']:02d}] {tc['task_type']}")
        print(f"     描述: {tc['task_desc']}")
        print(f"     领域: {result.get('domain', 'none')} | 匹配: {'是' if result['domain_matched'] else '否'}")
        print(f"     Top1: {top1['skill_id'] if top1 else 'None'} "
              f"(evo={top1['evolution_score'] if top1 else 0:.1f}, "
              f"rate={top1['success_rate'] if top1 else 0:.0%})")
        print(f"     Top3: {top3_ids}")
        print(f"     Fallback: {fallback['skill_id'] if fallback else 'None'}")
        print(f"     {icon} {quality.upper()} — {reason}")
        print(f"     备注: {tc['notes']}")

        results.append({
            "id": tc["id"],
            "task_type": tc["task_type"],
            "expected_top1": tc.get("expected_top1"),
            "actual_top1": top1["skill_id"] if top1 else None,
            "top3": top3_ids,
            "fallback": fallback["skill_id"] if fallback else None,
            "domain": result.get("domain"),
            "domain_matched": result["domain_matched"],
            "quality": quality,
            "reason": reason,
            "notes": tc["notes"],
        })

    # 汇总
    total = len(TEST_CASES)
    good_rate = quality_counts["good"] / total
    acceptable_rate = (quality_counts["good"] + quality_counts["acceptable"]) / total

    print("\n" + "=" * 65)
    print("  汇总")
    print("=" * 65)
    print(f"  总样例: {total}")
    print(f"  ✅ good:       {quality_counts['good']:2d} ({quality_counts['good']/total:.0%})")
    print(f"  ⚠️  acceptable: {quality_counts['acceptable']:2d} ({quality_counts['acceptable']/total:.0%})")
    print(f"  ❌ poor:       {quality_counts['poor']:2d} ({quality_counts['poor']/total:.0%})")
    print(f"\n  合理率（good+acceptable）: {acceptable_rate:.0%}")
    print(f"  Top1 精确率（good）:        {good_rate:.0%}")

    # 判断结论
    if quality_counts["good"] >= 8:
        verdict = "🎉 推荐系统可稳定挂主链路建议模式（good >= 8）"
    elif quality_counts["good"] >= 7:
        verdict = "✅ 推荐系统已可用（good >= 7），可挂主链路"
    elif quality_counts["good"] >= 6:
        verdict = "⚠️ 推荐系统基本可用，继续调规则后再挂主链路"
    else:
        verdict = "❌ 推荐系统需要继续调整规则，暂不挂主链路"

    print(f"\n  结论: {verdict}")
    print("=" * 65)

    # 保存报告
    report = {
        "tested_at": datetime.now().isoformat(),
        "total_cases": total,
        "quality_counts": quality_counts,
        "good_rate": round(good_rate, 3),
        "acceptable_rate": round(acceptable_rate, 3),
        "verdict": verdict,
        "cases": results,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n  报告已保存: {REPORT_FILE}")
    return report


if __name__ == "__main__":
    run_quality_test()
