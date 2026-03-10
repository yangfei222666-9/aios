"""
Skill Recommender - Phase 3 正式版

三个核心约束：
1. Top1 最低分门槛（score < 0.55 → 不给 Top1，只返回 Top3 备选）
2. fallback_skill 只从稳定 skill 里选（stable / recent_success_rate 高 / 非连败中）
3. recommendation_accepted 三态：accepted / rejected / not_applicable

主链路接入点：
- 任务前：recommend_for_task(task_type) → 给 Router 用
- 连败恢复：recommend_recovery(skill_id) → 给 LowSuccess_Agent 用
- 采纳记录：record_acceptance(rec_id, state) → 给 task_executor 用
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from collections import defaultdict

from paths import DATA_DIR
from skill_memory import skill_memory, SkillMemory

# ── 常量 ──────────────────────────────────────────────────
TOP1_MIN_SCORE = 0.55          # Top1 最低门槛（evolution_score 归一化后）
TASK_MATCH_MIN_FOR_TOP1 = 0.60 # Top1 领域相关性门槛
STABLE_MIN_RATE = 0.75         # fallback 候选最低成功率
CONSECUTIVE_FAIL_WARN = 2      # 连败预警阈值
CONSECUTIVE_FAIL_CRIT = 3      # 连败严重阈值

RECOMMENDATION_LOG = DATA_DIR / "recommendation_log.jsonl"
SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"

AcceptanceState = Literal["accepted", "rejected", "not_applicable"]


# ── 主接口 ────────────────────────────────────────────────

def recommend_for_task(task_type: str = "", top_n: int = 3) -> Dict:
    """
    任务前推荐：给 Router 调用

    约束 1：Top1 必须 score >= 0.55，否则只返回 Top3 备选，不给 Top1
    约束 2：fallback_skill 只从稳定 skill 里选

    Returns:
        {
            "rec_id": "rec-20260307-001",
            "task_type": "pdf",
            "top1": {...} | None,          # None = 无明显优势 skill
            "top1_reason": "...",
            "top3": [...],                 # 备选列表（含理由）
            "fallback_skill": {...} | None,
            "no_top1_reason": "..." | None # 为什么没有 Top1
        }
    """
    all_skills = skill_memory.get_all_skills()
    rec_id = _gen_rec_id()

    if not all_skills:
        result = {
            "rec_id": rec_id,
            "task_type": task_type,
            "top1": None,
            "top1_reason": None,
            "top3": [],
            "fallback_skill": None,
            "no_top1_reason": "暂无 Skill 数据",
        }
        _log_recommendation(result)
        return result

    # 过滤 + 评分
    candidates = _score_candidates(all_skills, task_type)

    # Top3（不受门槛限制，但要有基本数据）
    top3 = _build_top3(candidates[:top_n])

    # Top1 门槛检查（约束 1）
    top1 = None
    top1_reason = None
    no_top1_reason = None

    if candidates:
        best = candidates[0]
        normalized_score = best["_score"] / 100.0  # evolution_score 是 0-100
        match_score = best.get("_task_match", 0)

        # 只从满足领域相关性的候选里选 Top1
        eligible = [
            c for c in candidates
            if c.get("_task_match", 0) >= TASK_MATCH_MIN_FOR_TOP1
            and (c.get("_score", 0) / 100.0) >= TOP1_MIN_SCORE
        ]

        if eligible:
            top1_candidate = eligible[0]
            top1 = _format_skill_entry(top1_candidate, rank=1)
            top1_reason = _explain_top1(top1_candidate, candidates)
        else:
            reason_parts = []
            if not any(c.get("_task_match", 0) >= TASK_MATCH_MIN_FOR_TOP1 for c in candidates):
                reason_parts.append(
                    f"无满足领域相关性门槛 {TASK_MATCH_MIN_FOR_TOP1} 的技能"
                )
            if not any((c.get("_score", 0) / 100.0) >= TOP1_MIN_SCORE for c in candidates):
                reason_parts.append(
                    f"无技能达到最低分门槛 {TOP1_MIN_SCORE}"
                )
            if not reason_parts:
                if normalized_score < TOP1_MIN_SCORE:
                    reason_parts.append(
                        f"最高分 skill '{best['skill_id']}' 得分 {normalized_score:.2f} "
                        f"低于门槛 {TOP1_MIN_SCORE}"
                    )
                if match_score < TASK_MATCH_MIN_FOR_TOP1:
                    reason_parts.append(
                        f"领域相关性 {match_score:.2f} 低于门槛 {TASK_MATCH_MIN_FOR_TOP1}"
                    )

            no_top1_reason = "，".join(reason_parts) + "，无明显优势 skill"

    # fallback（约束 2：只从稳定 skill 里选，且优先同领域）
    fallback = _pick_fallback(
        all_skills,
        task_type=task_type,
        exclude_id=top1["skill_id"] if top1 else None
    )

    result = {
        "rec_id": rec_id,
        "task_type": task_type,
        "top1": top1,
        "top1_reason": top1_reason,
        "top3": top3,
        "fallback_skill": fallback,
        "no_top1_reason": no_top1_reason,
    }
    _log_recommendation(result)
    return result


def recommend_recovery(skill_id: str) -> Dict:
    """
    连败恢复推荐：给 LowSuccess_Agent 调用

    约束 2：fallback_skill 只从稳定 skill 里选（非连败中）

    Returns:
        {
            "rec_id": "rec-...",
            "skill_id": "pdf-skill",
            "consecutive_failures": 3,
            "severity": "warn" | "crit",
            "dominant_error": "timeout",
            "recommended_recovery": "increase_timeout_and_retry",
            "fallback_skill": {...} | None,
            "downgrade_suggestion": "..." | None
        }
    """
    skill_id = SkillMemory.normalize_skill_id(skill_id)
    rec_id = _gen_rec_id()

    mem = skill_memory.get_skill_memory(skill_id)
    recent = _load_recent_for_skill(skill_id, limit=10)

    # 计算连败数
    consecutive = 0
    for e in reversed(recent):
        if e.get("status") == "failed":
            consecutive += 1
        else:
            break

    if consecutive < CONSECUTIVE_FAIL_WARN:
        result = {
            "rec_id": rec_id,
            "skill_id": skill_id,
            "consecutive_failures": consecutive,
            "severity": "ok",
            "dominant_error": None,
            "recommended_recovery": None,
            "fallback_skill": None,
            "downgrade_suggestion": None,
        }
        _log_recommendation(result)
        return result

    severity = "crit" if consecutive >= CONSECUTIVE_FAIL_CRIT else "warn"

    # 主要错误类型
    lessons = mem.get("failure_lessons", []) if mem else []
    dominant_error = lessons[0]["error_type"] if lessons else "unknown"
    recovery = lessons[0]["recovery_strategy"] if lessons else "default_recovery"

    # fallback（约束 2）
    all_skills = skill_memory.get_all_skills()
    fallback = _pick_fallback(all_skills, task_type=skill_id, exclude_id=skill_id)

    # downgrade 建议
    downgrade = None
    if severity == "crit" and fallback:
        downgrade = (
            f"建议暂时降级到 '{fallback['skill_id']}'（成功率 {fallback['success_rate']:.0%}），"
            f"待 '{skill_id}' 修复后再切回"
        )

    result = {
        "rec_id": rec_id,
        "skill_id": skill_id,
        "consecutive_failures": consecutive,
        "severity": severity,
        "dominant_error": dominant_error,
        "recommended_recovery": recovery,
        "fallback_skill": fallback,
        "downgrade_suggestion": downgrade,
    }
    _log_recommendation(result)
    return result


def record_acceptance(rec_id: str, state: AcceptanceState, note: str = "") -> bool:
    """
    记录推荐采纳状态（约束 3：三态）

    Args:
        rec_id: 推荐记录 ID
        state: "accepted" | "rejected" | "not_applicable"
        note: 可选备注

    Returns:
        True = 找到并更新，False = 未找到
    """
    if not RECOMMENDATION_LOG.exists():
        return False

    lines = RECOMMENDATION_LOG.read_text(encoding="utf-8").splitlines()
    updated = False
    new_lines = []

    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if rec.get("rec_id") == rec_id:
                rec["recommendation_accepted"] = state
                rec["acceptance_note"] = note
                rec["accepted_at"] = datetime.now().isoformat()
                updated = True
            new_lines.append(json.dumps(rec, ensure_ascii=False))
        except json.JSONDecodeError:
            new_lines.append(line)

    if updated:
        RECOMMENDATION_LOG.write_text(
            "\n".join(new_lines) + "\n", encoding="utf-8"
        )

    return updated


# ── 内部函数 ──────────────────────────────────────────────

def _score_candidates(all_skills: List[Dict], task_type: str) -> List[Dict]:
    """对候选 skill 评分并排序"""
    task_lower = task_type.lower() if task_type else ""
    scored = []

    for s in all_skills:
        sid = s.get("skill_id", "")
        score = s.get("evolution_score", 0)

        # 任务领域匹配分数（0~1）
        task_match = _calc_task_match(s, task_lower)

        # 关键词匹配加成（+10）
        if task_match >= 0.6:
            score += 10

        s = dict(s)  # 不改原始数据
        s["_score"] = score
        s["_task_match"] = task_match
        s["_keyword_match"] = task_match >= 0.6
        scored.append(s)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored


def _build_top3(candidates: List[Dict]) -> List[Dict]:
    """构建 Top3 列表，每个都附带区分理由"""
    result = []
    for i, s in enumerate(candidates):
        entry = _format_skill_entry(s, rank=i + 1)
        entry["reason"] = _explain_rank(s, i, candidates)
        result.append(entry)
    return result


def _format_skill_entry(s: Dict, rank: int) -> Dict:
    return {
        "rank": rank,
        "skill_id": s["skill_id"],
        "skill_name": s.get("skill_name", s["skill_id"]),
        "skill_version": s.get("skill_version", "1.0.0"),
        "evolution_score": s.get("evolution_score", 0),
        "success_rate": s.get("success_rate", 0),
        "usage_count": s.get("usage_count", 0),
        "top_pattern": (
            s["common_patterns"][0]["pattern"]
            if s.get("common_patterns") else None
        ),
    }


def _explain_top1(best: Dict, candidates: List[Dict]) -> str:
    """解释为什么 Top1 是它"""
    parts = []
    rate = best.get("success_rate", 0)
    evo = best.get("evolution_score", 0)
    count = best.get("usage_count", 0)

    if best.get("_keyword_match"):
        parts.append("关键词精确匹配")
    if rate >= 0.85:
        parts.append(f"成功率高（{rate:.0%}）")
    if evo >= 70:
        parts.append(f"演化分数高（{evo:.0f}）")
    if count >= 10:
        parts.append(f"使用经验丰富（{count} 次）")

    # 与第二名的差距
    if len(candidates) >= 2:
        gap = best["_score"] - candidates[1]["_score"]
        if gap >= 10:
            parts.append(f"领先第二名 {gap:.0f} 分")

    return "，".join(parts) if parts else "综合评分最高"


def _explain_rank(s: Dict, rank: int, candidates: List[Dict]) -> str:
    """解释 Top3 中每个 skill 的理由（要区分清楚）"""
    rate = s.get("success_rate", 0)
    evo = s.get("evolution_score", 0)
    count = s.get("usage_count", 0)

    if rank == 0:
        return _explain_top1(s, candidates)

    # 第 2、3 名：说明与第 1 名的差异
    top1 = candidates[0]
    diff_rate = rate - top1.get("success_rate", 0)
    diff_evo = evo - top1.get("evolution_score", 0)

    parts = []
    if s.get("_keyword_match"):
        parts.append("关键词匹配")
    if diff_rate > 0:
        parts.append(f"成功率略高于 Top1（+{diff_rate:.0%}）")
    elif diff_rate < -0.1:
        parts.append(f"成功率低于 Top1（{rate:.0%}）")
    else:
        parts.append(f"成功率相近（{rate:.0%}）")

    if count >= 5:
        parts.append(f"有一定使用经验（{count} 次）")
    else:
        parts.append(f"使用次数较少（{count} 次）")

    return "，".join(parts) if parts else f"综合评分第 {rank + 1}"


def _pick_fallback(
    all_skills: List[Dict],
    task_type: str = "",
    exclude_id: Optional[str] = None
) -> Optional[Dict]:
    """
    约束 2：fallback 只从稳定 skill 里选
    条件：success_rate >= STABLE_MIN_RATE，且非连败中

    优先策略：
    1) 同领域稳定 skill
    2) 全局稳定 skill
    """
    task_lower = task_type.lower() if task_type else ""

    # 找出连败中的 skill
    failing_ids = _get_currently_failing_skills()

    def _is_stable(s: Dict) -> bool:
        return (
            s.get("success_rate", 0) >= STABLE_MIN_RATE
            and s.get("skill_id") != exclude_id
            and s.get("skill_id") not in failing_ids
            and s.get("usage_count", 0) >= 2
        )

    # 1) 优先同领域
    domain_candidates = [
        s for s in all_skills
        if _is_stable(s) and _calc_task_match(s, task_lower) >= 0.6
    ]

    candidates = domain_candidates if domain_candidates else [
        s for s in all_skills if _is_stable(s)
    ]

    if not candidates:
        return None

    # 选成功率最高的
    best = max(candidates, key=lambda x: (x.get("success_rate", 0), x.get("usage_count", 0)))
    return {
        "skill_id": best["skill_id"],
        "skill_name": best.get("skill_name", best["skill_id"]),
        "skill_version": best.get("skill_version", "1.0.0"),
        "success_rate": best.get("success_rate", 0),
        "usage_count": best.get("usage_count", 0),
        "why_stable": f"成功率 {best.get('success_rate', 0):.0%}，非连败中",
    }


def _get_currently_failing_skills() -> set:
    """找出当前连败中的 skill（最近 N 次全失败）"""
    if not SKILL_EXECUTIONS_FILE.exists():
        return set()

    # 按 skill_id 分组，取最近 3 条
    recent_by_skill: Dict[str, List[Dict]] = defaultdict(list)
    with open(SKILL_EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    sid = SkillMemory.normalize_skill_id(r.get("skill_id", ""))
                    recent_by_skill[sid].append(r)
                except json.JSONDecodeError:
                    continue

    failing = set()
    for sid, records in recent_by_skill.items():
        records.sort(key=lambda x: x.get("started_at", ""))
        last3 = records[-3:]
        if len(last3) >= 2 and all(r.get("status") == "failed" for r in last3):
            failing.add(sid)

    return failing


def _calc_task_match(skill: Dict, task_lower: str) -> float:
    """
    计算 task_match（0~1）

    规则：
    1) task_type 命中 skill_id / skill_name = 1.0
    2) task_type 命中 top_pattern = 1.0
    3) task_type 命中其他 pattern = 0.7
    4) 否则 0.0
    """
    if not task_lower:
        return 0.0

    sid = skill.get("skill_id", "").lower()
    sname = skill.get("skill_name", "").lower()

    if task_lower in sid or task_lower in sname:
        return 1.0

    if skill.get("common_patterns"):
        top_pattern = skill["common_patterns"][0].get("pattern", "")
        if task_lower in top_pattern.lower():
            return 1.0

    for p in skill.get("common_patterns", []):
        if task_lower in p.get("pattern", "").lower():
            return 0.7

    return 0.0


def _load_recent_for_skill(skill_id: str, limit: int = 10) -> List[Dict]:
    """加载某 skill 最近 N 条执行记录"""
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
                except json.JSONDecodeError:
                    continue

    records.sort(key=lambda x: x.get("started_at", ""))
    return records[-limit:]


def _log_recommendation(rec: Dict):
    """写入推荐日志"""
    RECOMMENDATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    rec["logged_at"] = datetime.now().isoformat()
    # 默认状态：not_applicable（等待 record_acceptance 更新）
    if "recommendation_accepted" not in rec:
        rec["recommendation_accepted"] = "not_applicable"
    with open(RECOMMENDATION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _gen_rec_id() -> str:
    return f"rec-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:19]}"
