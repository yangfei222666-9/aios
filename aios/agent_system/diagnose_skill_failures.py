"""
Skill 连败诊断工具

针对 CRIT/WARN 级别的 skill，快速诊断：
1. 最近 3 次错误类型
2. 当前 alert_level
3. 推荐 recovery strategy
4. 是否建议临时 fallback / downgrade
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"
SKILL_MEMORY_FILE = DATA_DIR / "skill_memory.jsonl"

sys.path.insert(0, str(BASE_DIR))
from skill_memory import SkillMemory


def load_recent_failures(skill_id: str, limit: int = 10) -> List[Dict]:
    """加载某 skill 最近的失败记录"""
    if not SKILL_EXECUTIONS_FILE.exists():
        return []
    
    skill_id = SkillMemory.normalize_skill_id(skill_id)
    failures = []
    
    with open(SKILL_EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    if (SkillMemory.normalize_skill_id(record.get("skill_id", "")) == skill_id 
                        and record.get("status") == "failed"):
                        failures.append(record)
                except (json.JSONDecodeError, KeyError):
                    continue
    
    # 按时间倒序，取最近 N 条
    failures.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return failures[:limit]


def classify_error(error_msg: str) -> str:
    """分类错误类型（与 skill_memory.py 保持一致）"""
    if not error_msg:
        return "unknown"
    
    error_lower = error_msg.lower()
    
    if "timeout" in error_lower or "timed out" in error_lower:
        return "timeout"
    elif "encoding" in error_lower or "decode" in error_lower or "codec" in error_lower:
        return "encoding_error"
    elif "not found" in error_lower or "no such file" in error_lower:
        return "file_not_found"
    elif "permission" in error_lower or "access denied" in error_lower:
        return "permission_denied"
    elif "memory" in error_lower or "out of memory" in error_lower:
        return "resource_exhausted"
    elif "connection" in error_lower or "network" in error_lower or "unreachable" in error_lower:
        return "network_error"
    elif "dependency" in error_lower or "module not found" in error_lower or "import" in error_lower:
        return "dependency_error"
    else:
        return "unknown"


def suggest_recovery(error_type: str, consecutive_count: int) -> str:
    """根据错误类型和连续次数推荐恢复策略"""
    base_strategies = {
        "timeout": "increase_timeout_and_retry",
        "encoding_error": "try_multiple_encodings",
        "file_not_found": "check_file_path_and_retry",
        "permission_denied": "check_permissions_and_retry",
        "resource_exhausted": "reduce_batch_size_and_retry",
        "network_error": "retry_with_backoff",
        "dependency_error": "check_dependencies_and_reinstall",
        "unknown": "default_recovery"
    }
    
    strategy = base_strategies.get(error_type, "default_recovery")
    
    # 连续失败 3+ 次，升级策略
    if consecutive_count >= 3:
        if error_type == "timeout":
            strategy = "switch_to_async_mode_or_split_task"
        elif error_type == "encoding_error":
            strategy = "fallback_to_binary_mode"
        elif error_type == "network_error":
            strategy = "switch_to_backup_endpoint"
        elif error_type == "dependency_error":
            strategy = "use_alternative_library"
        else:
            strategy = "escalate_to_human_review"
    
    return strategy


def should_downgrade(skill_id: str, consecutive_failures: int, error_types: List[str]) -> Dict:
    """判断是否需要临时降级或 fallback"""
    # 规则：
    # 1. 连续失败 3+ 次 → 建议 fallback
    # 2. 错误类型集中（>= 80%）→ 可能是环境问题，建议临时禁用
    # 3. 错误类型分散 → 可能是 skill 本身问题，建议降级
    
    if consecutive_failures < 2:
        return {"action": "none", "reason": "失败次数不足，继续观察"}
    
    # 统计错误类型分布
    error_counter = Counter(error_types)
    most_common = error_counter.most_common(1)[0] if error_counter else ("unknown", 0)
    dominant_error, dominant_count = most_common
    dominant_rate = dominant_count / len(error_types) if error_types else 0
    
    if consecutive_failures >= 3:
        if dominant_rate >= 0.8:
            # 错误集中 → 环境问题
            return {
                "action": "temporary_disable",
                "reason": f"连续 {consecutive_failures} 次失败，错误集中在 {dominant_error}（{dominant_rate:.0%}），疑似环境问题",
                "fallback_to": "next_best_skill_in_domain"
            }
        else:
            # 错误分散 → skill 本身问题
            return {
                "action": "downgrade_priority",
                "reason": f"连续 {consecutive_failures} 次失败，错误类型分散，疑似 skill 本身问题",
                "fallback_to": "next_best_skill_in_domain"
            }
    
    elif consecutive_failures == 2:
        return {
            "action": "warn_and_monitor",
            "reason": f"连续 2 次失败，错误类型: {dominant_error}，继续观察",
            "fallback_to": None
        }
    
    return {"action": "none", "reason": "失败次数不足"}


def diagnose_skill(skill_id: str) -> Dict:
    """诊断单个 skill 的连败情况"""
    skill_id = SkillMemory.normalize_skill_id(skill_id)
    
    # 加载最近失败记录
    recent_failures = load_recent_failures(skill_id, limit=10)
    
    if not recent_failures:
        return {
            "skill_id": skill_id,
            "status": "no_failures",
            "message": "最近无失败记录"
        }
    
    # 统计连续失败次数（从最近一次开始往前数）
    consecutive_failures = 0
    for record in recent_failures:
        if record.get("status") == "failed":
            consecutive_failures += 1
        else:
            break
    
    # 提取最近 3 次错误
    last_3_failures = recent_failures[:3]
    error_types = [classify_error(f.get("error", "")) for f in last_3_failures]
    error_messages = [f.get("error", "")[:100] for f in last_3_failures]  # 截断长错误
    
    # 确定 alert_level
    if consecutive_failures >= 3:
        alert_level = "CRIT"
    elif consecutive_failures >= 2:
        alert_level = "WARN"
    else:
        alert_level = "OK"
    
    # 推荐恢复策略
    dominant_error = Counter(error_types).most_common(1)[0][0] if error_types else "unknown"
    recovery_strategy = suggest_recovery(dominant_error, consecutive_failures)
    
    # 判断是否需要降级
    downgrade_decision = should_downgrade(skill_id, consecutive_failures, error_types)
    
    return {
        "skill_id": skill_id,
        "alert_level": alert_level,
        "consecutive_failures": consecutive_failures,
        "last_3_errors": [
            {"type": error_types[i], "message": error_messages[i]}
            for i in range(len(last_3_failures))
        ],
        "dominant_error": dominant_error,
        "recovery_strategy": recovery_strategy,
        "downgrade_decision": downgrade_decision,
        "total_recent_failures": len(recent_failures),
    }


def generate_diagnosis_report(target_skills: List[str]) -> Dict:
    """生成连败诊断报告"""
    print("=" * 70)
    print("  Skill 连败诊断报告")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = []
    
    for skill_id in target_skills:
        diagnosis = diagnose_skill(skill_id)
        results.append(diagnosis)
        
        # 打印
        alert_icon = {"CRIT": "🔴", "WARN": "⚠️", "OK": "✅"}.get(diagnosis.get("alert_level", "OK"), "❓")
        
        print(f"\n{alert_icon} {diagnosis['skill_id']}")
        print(f"   Alert Level: {diagnosis.get('alert_level', 'OK')}")
        print(f"   连续失败: {diagnosis.get('consecutive_failures', 0)} 次")
        
        if diagnosis.get("status") == "no_failures":
            print(f"   状态: {diagnosis['message']}")
            continue
        
        print(f"   主要错误: {diagnosis.get('dominant_error', 'unknown')}")
        print(f"   推荐策略: {diagnosis.get('recovery_strategy', 'default_recovery')}")
        
        # 最近 3 次错误
        print(f"   最近 3 次错误:")
        for i, err in enumerate(diagnosis.get("last_3_errors", []), 1):
            print(f"      [{i}] {err['type']}: {err['message'][:80]}...")
        
        # 降级建议
        downgrade = diagnosis.get("downgrade_decision", {})
        action = downgrade.get("action", "none")
        if action != "none":
            print(f"   降级建议: {action}")
            print(f"   原因: {downgrade.get('reason', '')}")
            if downgrade.get("fallback_to"):
                print(f"   Fallback: {downgrade['fallback_to']}")
    
    # 汇总
    print("\n" + "=" * 70)
    print("  汇总")
    print("=" * 70)
    
    crit_count = sum(1 for r in results if r.get("alert_level") == "CRIT")
    warn_count = sum(1 for r in results if r.get("alert_level") == "WARN")
    ok_count = sum(1 for r in results if r.get("alert_level") == "OK")
    
    print(f"  🔴 CRIT: {crit_count}")
    print(f"  ⚠️  WARN: {warn_count}")
    print(f"  ✅ OK:   {ok_count}")
    
    # 建议
    if crit_count > 0:
        print(f"\n  建议: 立即处理 {crit_count} 个 CRIT 级别 skill")
        print(f"        优先检查环境配置、依赖版本、网络连接")
    elif warn_count > 0:
        print(f"\n  建议: 关注 {warn_count} 个 WARN 级别 skill，继续观察")
    else:
        print(f"\n  建议: 所有 skill 运行正常")
    
    print("=" * 70)
    
    # 保存报告
    report = {
        "generated_at": datetime.now().isoformat(),
        "target_skills": target_skills,
        "results": results,
        "summary": {
            "crit": crit_count,
            "warn": warn_count,
            "ok": ok_count,
        }
    }
    
    report_file = DATA_DIR / "skill_failure_diagnosis.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n  报告已保存: {report_file}")
    return report


if __name__ == "__main__":
    # P2 目标 skill
    TARGET_SKILLS = [
        "api-testing-skill",
        "docker-skill",
        "pdf-skill",
    ]
    
    generate_diagnosis_report(TARGET_SKILLS)
