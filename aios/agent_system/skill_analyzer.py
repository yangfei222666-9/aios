"""
Skill Analyzer - Phase 2 模式识别

识别 4 类 Skill：
1. 高成功 Skill（稳定）
2. 高失败 Skill（脆弱）
3. 高频 Skill（核心）
4. 恢复后改善明显的 Skill（值得优化）

回答：哪些技能稳定，哪些技能脆弱，哪些技能值得优先优化。

集成点：
- heartbeat_v5.py（每周一次自动分析）
- daily_metrics.py（每日简报附带 Skill 健康摘要）
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from paths import DATA_DIR
from skill_memory import skill_memory, SkillMemory

SKILL_ANALYSIS_FILE = DATA_DIR / "skill_analysis.json"
SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"


def analyze_skills(days: int = 30) -> Dict:
    """
    分析所有 Skill，输出 4 类分类结果

    Args:
        days: 分析最近 N 天的数据（默认 30 天）

    Returns:
        {
            "analyzed_at": "...",
            "period_days": 30,
            "total_skills": 5,
            "categories": {
                "stable": [...],      # 高成功（success_rate >= 0.85）
                "fragile": [...],     # 高失败（success_rate < 0.60）
                "core": [...],        # 高频（usage_count top 30%）
                "improving": [...]    # 恢复后改善明显
            },
            "priority_optimize": [...],  # 最值得优先优化的 Skill
            "weekly_tip": "..."          # 本周最该优化的 skill 提示
        }
    """
    all_skills = skill_memory.get_all_skills()
    if not all_skills:
        return _empty_result(days)

    # 加载最近 N 天的执行记录用于趋势分析
    recent_executions = _load_recent_executions(days)

    # 分类
    stable = []
    fragile = []
    core = []
    improving = []

    # 高频阈值：usage_count top 30%
    usage_counts = sorted([s.get("usage_count", 0) for s in all_skills], reverse=True)
    core_threshold = usage_counts[max(0, len(usage_counts) * 30 // 100)] if usage_counts else 1

    for skill in all_skills:
        sid = skill.get("skill_id", "")
        rate = skill.get("success_rate", 0)
        count = skill.get("usage_count", 0)
        evo = skill.get("evolution_score", 0)

        entry = {
            "skill_id": sid,
            "skill_name": skill.get("skill_name", sid),
            "skill_version": skill.get("skill_version", "1.0.0"),
            "success_rate": rate,
            "usage_count": count,
            "evolution_score": evo,
            "failure_count": skill.get("failure_count", 0),
        }

        # 1. 高成功（稳定）
        if rate >= 0.85 and count >= 3:
            stable.append(entry)

        # 2. 高失败（脆弱）
        if rate < 0.60 and count >= 2:
            fragile.append(entry)

        # 3. 高频（核心）
        if count >= core_threshold and count >= 3:
            core.append(entry)

        # 4. 恢复后改善明显
        trend = _compute_trend(sid, recent_executions)
        if trend and trend["improved"]:
            entry["trend"] = trend
            improving.append(entry)

    # 排序
    stable.sort(key=lambda x: x["success_rate"], reverse=True)
    fragile.sort(key=lambda x: x["success_rate"])
    core.sort(key=lambda x: x["usage_count"], reverse=True)
    improving.sort(key=lambda x: x["trend"]["delta"], reverse=True)

    # 最值得优先优化：脆弱 + 高频交集，或脆弱中 usage 最高的
    priority = _pick_priority_optimize(fragile, core, all_skills)

    # 本周提示
    weekly_tip = _generate_weekly_tip(stable, fragile, core, improving, priority)

    result = {
        "analyzed_at": datetime.now().isoformat(),
        "period_days": days,
        "total_skills": len(all_skills),
        "categories": {
            "stable": stable,
            "fragile": fragile,
            "core": core,
            "improving": improving,
        },
        "priority_optimize": priority,
        "weekly_tip": weekly_tip,
    }

    # 持久化
    SKILL_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SKILL_ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def get_skill_recommendation(task_type: str = "") -> List[Dict]:
    """
    Phase 3 轻版：推荐 Top3 skill strategy

    Args:
        task_type: 任务类型关键词（如 "pdf", "code", "analysis"）

    Returns:
        Top 3 推荐 Skill（按 evolution_score 排序）
    """
    all_skills = skill_memory.get_all_skills()
    if not all_skills:
        return []

    candidates = all_skills
    if task_type:
        task_lower = task_type.lower()
        # 优先匹配 skill_id 或 skill_name 包含关键词的
        matched = [s for s in all_skills
                   if task_lower in s.get("skill_id", "").lower()
                   or task_lower in s.get("skill_name", "").lower()]
        if matched:
            candidates = matched

    # 按 evolution_score 排序，取 Top 3
    candidates.sort(key=lambda s: s.get("evolution_score", 0), reverse=True)
    return [
        {
            "skill_id": s["skill_id"],
            "skill_name": s.get("skill_name", s["skill_id"]),
            "skill_version": s.get("skill_version", "1.0.0"),
            "evolution_score": s.get("evolution_score", 0),
            "success_rate": s.get("success_rate", 0),
            "usage_count": s.get("usage_count", 0),
            "top_pattern": s["common_patterns"][0]["pattern"] if s.get("common_patterns") else None,
        }
        for s in candidates[:3]
    ]


def get_failure_recovery(skill_id: str) -> Optional[Dict]:
    """
    Phase 3 轻版：某 skill 连续失败时推荐恢复方案

    Args:
        skill_id: 技能 ID

    Returns:
        恢复建议（如果有连续失败）
    """
    skill_id = SkillMemory.normalize_skill_id(skill_id)
    mem = skill_memory.get_skill_memory(skill_id)
    if not mem:
        return None

    lessons = mem.get("failure_lessons", [])
    if not lessons:
        return None

    # 检查最近执行是否连续失败
    recent = _load_recent_executions_for_skill(skill_id, limit=5)
    if not recent:
        return None

    consecutive_failures = 0
    for e in reversed(recent):
        if e["status"] == "failed":
            consecutive_failures += 1
        else:
            break

    if consecutive_failures < 2:
        return None

    # 找最常见的错误类型和恢复策略
    top_lesson = lessons[0]
    return {
        "skill_id": skill_id,
        "consecutive_failures": consecutive_failures,
        "dominant_error": top_lesson["error_type"],
        "recommended_recovery": top_lesson["recovery_strategy"],
        "total_failure_types": len(lessons),
        "suggestion": f"Skill '{skill_id}' 连续失败 {consecutive_failures} 次，"
                      f"主要错误: {top_lesson['error_type']}，"
                      f"建议: {top_lesson['recovery_strategy']}"
    }


# ── 内部函数 ──────────────────────────────────────────────

def _empty_result(days: int) -> Dict:
    return {
        "analyzed_at": datetime.now().isoformat(),
        "period_days": days,
        "total_skills": 0,
        "categories": {"stable": [], "fragile": [], "core": [], "improving": []},
        "priority_optimize": [],
        "weekly_tip": "暂无 Skill 数据，等待执行记录积累。",
    }


def _load_recent_executions(days: int) -> List[Dict]:
    """加载最近 N 天的所有执行记录"""
    if not SKILL_EXECUTIONS_FILE.exists():
        return []

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    records = []
    with open(SKILL_EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    if r.get("started_at", "") >= cutoff:
                        records.append(r)
                except (json.JSONDecodeError, KeyError):
                    continue
    return records


def _load_recent_executions_for_skill(skill_id: str, limit: int = 10) -> List[Dict]:
    """加载某 Skill 最近 N 条执行记录"""
    if not SKILL_EXECUTIONS_FILE.exists():
        return []

    records = []
    with open(SKILL_EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    if SkillMemory.normalize_skill_id(r.get("skill_id", "")) == skill_id:
                        records.append(r)
                except (json.JSONDecodeError, KeyError):
                    continue

    records.sort(key=lambda x: x.get("started_at", ""))
    return records[-limit:]


def _compute_trend(skill_id: str, all_recent: List[Dict]) -> Optional[Dict]:
    """
    计算某 Skill 的趋势：前半段 vs 后半段成功率

    Returns:
        {"early_rate": 0.5, "late_rate": 0.8, "delta": 0.3, "improved": True}
        或 None（数据不足）
    """
    records = [r for r in all_recent
               if SkillMemory.normalize_skill_id(r.get("skill_id", "")) == skill_id]

    if len(records) < 4:
        return None

    records.sort(key=lambda x: x.get("started_at", ""))
    mid = len(records) // 2
    early = records[:mid]
    late = records[mid:]

    early_success = sum(1 for r in early if r["status"] == "success")
    late_success = sum(1 for r in late if r["status"] == "success")

    early_rate = early_success / len(early) if early else 0
    late_rate = late_success / len(late) if late else 0
    delta = late_rate - early_rate

    return {
        "early_rate": round(early_rate, 3),
        "late_rate": round(late_rate, 3),
        "delta": round(delta, 3),
        "improved": delta >= 0.10,  # 改善 10%+ 算"明显改善"
    }


def _pick_priority_optimize(fragile: List, core: List, all_skills: List) -> List[Dict]:
    """选出最值得优先优化的 Skill"""
    priority = []

    # 脆弱 + 高频交集
    core_ids = {s["skill_id"] for s in core}
    for s in fragile:
        if s["skill_id"] in core_ids:
            s["reason"] = "脆弱且高频，优化收益最大"
            priority.append(s)

    # 如果交集为空，取脆弱中 usage 最高的
    if not priority and fragile:
        top = max(fragile, key=lambda x: x["usage_count"])
        top["reason"] = "最脆弱的 Skill，优先修复"
        priority.append(top)

    # 补充：成功率在 0.60-0.85 之间且高频的（潜力股）
    for s in all_skills:
        sid = s.get("skill_id", "")
        rate = s.get("success_rate", 0)
        count = s.get("usage_count", 0)
        if 0.60 <= rate < 0.85 and count >= 5 and sid not in {p["skill_id"] for p in priority}:
            priority.append({
                "skill_id": sid,
                "skill_name": s.get("skill_name", sid),
                "success_rate": rate,
                "usage_count": count,
                "evolution_score": s.get("evolution_score", 0),
                "reason": "成功率中等但高频，优化空间大",
            })

    return priority[:5]


def _generate_weekly_tip(stable, fragile, core, improving, priority) -> str:
    """生成本周最该优化的 skill 提示"""
    parts = []

    if priority:
        top = priority[0]
        parts.append(f"🎯 本周最该优化: {top['skill_id']}（{top.get('reason', '')}）")

    if fragile:
        names = ", ".join(s["skill_id"] for s in fragile[:3])
        parts.append(f"⚠️ 脆弱 Skill: {names}")

    if improving:
        names = ", ".join(s["skill_id"] for s in improving[:2])
        parts.append(f"📈 改善中: {names}")

    if stable:
        parts.append(f"✅ 稳定 Skill: {len(stable)} 个")

    if not parts:
        return "暂无足够数据生成建议，继续积累执行记录。"

    return " | ".join(parts)


def print_analysis(result: Dict):
    """打印分析结果（人类可读）"""
    print(f"\n{'='*60}")
    print(f"  Skill Analysis Report")
    print(f"  {result['analyzed_at']} | {result['period_days']}d window")
    print(f"  Total Skills: {result['total_skills']}")
    print(f"{'='*60}")

    cats = result["categories"]

    if cats["stable"]:
        print(f"\n✅ 稳定 Skill（success_rate >= 85%）:")
        for s in cats["stable"]:
            print(f"   {s['skill_id']} v{s.get('skill_version','?')} | "
                  f"{s['success_rate']:.0%} success | {s['usage_count']} uses | "
                  f"evo {s['evolution_score']:.0f}")

    if cats["fragile"]:
        print(f"\n⚠️ 脆弱 Skill（success_rate < 60%）:")
        for s in cats["fragile"]:
            print(f"   {s['skill_id']} v{s.get('skill_version','?')} | "
                  f"{s['success_rate']:.0%} success | {s['failure_count']} failures")

    if cats["core"]:
        print(f"\n🔥 高频 Skill（核心）:")
        for s in cats["core"]:
            print(f"   {s['skill_id']} | {s['usage_count']} uses | "
                  f"{s['success_rate']:.0%} success")

    if cats["improving"]:
        print(f"\n📈 恢复改善中:")
        for s in cats["improving"]:
            t = s.get("trend", {})
            print(f"   {s['skill_id']} | {t.get('early_rate',0):.0%} → "
                  f"{t.get('late_rate',0):.0%} (+{t.get('delta',0):.0%})")

    if result["priority_optimize"]:
        print(f"\n🎯 优先优化:")
        for s in result["priority_optimize"]:
            print(f"   {s['skill_id']} — {s.get('reason', '')}")

    print(f"\n💡 {result['weekly_tip']}")
    print()


if __name__ == "__main__":
    import sys

    days = 30
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    result = analyze_skills(days=days)
    print_analysis(result)
