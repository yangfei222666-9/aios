"""
Skill Version Comparison - 版本对比

核心功能：
1. 比较同 skill_name 下相邻版本
2. 对比指标：成功率、平均耗时、最近 7 天使用次数
3. 输出趋势：improved / degraded / neutral

输出格式：
{
  "skill_id": "pdf-skill",
  "comparison": {
    "from_version": "1.0.0",
    "to_version": "1.1.0",
    "success_rate": {"from": 0.72, "to": 0.89, "delta": 0.17, "trend": "improved"},
    "avg_duration_ms": {"from": 18400, "to": 12100, "delta": -6300, "trend": "improved"},
    "usage_7d": {"from": 15, "to": 23, "delta": 8, "trend": "improved"}
  },
  "overall_trend": "improved"
}
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from paths import DATA_DIR
from skill_memory import SkillMemory

SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"
VERSION_COMPARISON_FILE = DATA_DIR / "skill_version_comparison.json"


def compare_skill_versions(skill_id: str = None) -> List[Dict]:
    """
    比较 Skill 版本（相邻版本对比）
    
    Args:
        skill_id: 指定 Skill ID（None = 所有 Skill）
    
    Returns:
        版本对比结果列表
    """
    if not SKILL_EXECUTIONS_FILE.exists():
        return []
    
    # 按 skill_id 分组，收集所有执行记录
    skill_executions = defaultdict(list)
    
    with open(SKILL_EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    sid = SkillMemory.normalize_skill_id(record.get("skill_id", ""))
                    
                    # 如果指定了 skill_id，只处理该 Skill
                    if skill_id and sid != SkillMemory.normalize_skill_id(skill_id):
                        continue
                    
                    skill_executions[sid].append(record)
                except (json.JSONDecodeError, KeyError):
                    continue
    
    # 对每个 Skill 进行版本对比
    comparisons = []
    
    for sid, executions in skill_executions.items():
        # 按版本分组
        version_groups = defaultdict(list)
        for record in executions:
            version = record.get("skill_version", "1.0.0")
            version_groups[version].append(record)
        
        # 如果只有一个版本，跳过
        if len(version_groups) < 2:
            continue
        
        # 按版本号排序（简单字符串排序，假设版本号格式规范）
        versions = sorted(version_groups.keys())
        
        # 相邻版本对比
        for i in range(len(versions) - 1):
            from_version = versions[i]
            to_version = versions[i + 1]
            
            comparison = _compare_two_versions(
                sid,
                from_version,
                version_groups[from_version],
                to_version,
                version_groups[to_version]
            )
            
            if comparison:
                comparisons.append(comparison)
    
    # 持久化
    if comparisons:
        _save_comparisons(comparisons)
    
    return comparisons


def _compare_two_versions(
    skill_id: str,
    from_version: str,
    from_records: List[Dict],
    to_version: str,
    to_records: List[Dict]
) -> Optional[Dict]:
    """比较两个版本的指标"""
    
    # 计算 from_version 指标
    from_stats = _calculate_version_stats(from_records)
    
    # 计算 to_version 指标
    to_stats = _calculate_version_stats(to_records)
    
    # 对比成功率
    success_rate_delta = to_stats["success_rate"] - from_stats["success_rate"]
    success_rate_trend = _determine_trend(success_rate_delta, threshold=0.05)
    
    # 对比平均耗时（耗时减少 = improved）
    duration_delta = to_stats["avg_duration_ms"] - from_stats["avg_duration_ms"]
    duration_trend = _determine_trend(-duration_delta, threshold=500)  # 500ms 阈值
    
    # 对比最近 7 天使用次数
    usage_7d_delta = to_stats["usage_7d"] - from_stats["usage_7d"]
    usage_7d_trend = _determine_trend(usage_7d_delta, threshold=2)
    
    # 综合趋势（3 个指标投票）
    trend_votes = [success_rate_trend, duration_trend, usage_7d_trend]
    improved_count = trend_votes.count("improved")
    degraded_count = trend_votes.count("degraded")
    
    if improved_count >= 2:
        overall_trend = "improved"
    elif degraded_count >= 2:
        overall_trend = "degraded"
    else:
        overall_trend = "neutral"
    
    return {
        "skill_id": skill_id,
        "skill_name": from_records[0].get("skill_name", skill_id),
        "comparison": {
            "from_version": from_version,
            "to_version": to_version,
            "success_rate": {
                "from": round(from_stats["success_rate"], 3),
                "to": round(to_stats["success_rate"], 3),
                "delta": round(success_rate_delta, 3),
                "trend": success_rate_trend
            },
            "avg_duration_ms": {
                "from": round(from_stats["avg_duration_ms"], 1),
                "to": round(to_stats["avg_duration_ms"], 1),
                "delta": round(duration_delta, 1),
                "trend": duration_trend
            },
            "usage_7d": {
                "from": from_stats["usage_7d"],
                "to": to_stats["usage_7d"],
                "delta": usage_7d_delta,
                "trend": usage_7d_trend
            }
        },
        "overall_trend": overall_trend,
        "compared_at": datetime.now().isoformat()
    }


def _calculate_version_stats(records: List[Dict]) -> Dict:
    """计算某个版本的统计指标"""
    total = len(records)
    success = sum(1 for r in records if r["status"] == "success")
    success_rate = success / total if total > 0 else 0.0
    
    avg_duration = sum(r.get("duration_ms", 0) for r in records) / total if total > 0 else 0.0
    
    # 最近 7 天使用次数
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    usage_7d = sum(1 for r in records if r.get("started_at", "") >= cutoff)
    
    return {
        "success_rate": success_rate,
        "avg_duration_ms": avg_duration,
        "usage_7d": usage_7d,
        "total_executions": total
    }


def _determine_trend(delta: float, threshold: float) -> str:
    """根据 delta 判断趋势"""
    if delta > threshold:
        return "improved"
    elif delta < -threshold:
        return "degraded"
    else:
        return "neutral"


def _save_comparisons(comparisons: List[Dict]):
    """持久化版本对比结果"""
    VERSION_COMPARISON_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(VERSION_COMPARISON_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_comparisons": len(comparisons),
            "comparisons": comparisons
        }, f, ensure_ascii=False, indent=2)


def format_comparison_message(comparison: Dict) -> str:
    """格式化版本对比消息（用于 daily_metrics 输出）"""
    comp = comparison["comparison"]
    
    # Emoji 映射
    trend_emoji = {
        "improved": "📈",
        "degraded": "📉",
        "neutral": "➡️"
    }
    
    overall_emoji = trend_emoji.get(comparison["overall_trend"], "➡️")
    
    msg = (
        f"{overall_emoji} {comparison['skill_id']} "
        f"v{comp['from_version']} → v{comp['to_version']}\n"
        f"   成功率: {comp['success_rate']['from']:.1%} → {comp['success_rate']['to']:.1%} "
        f"({comp['success_rate']['delta']:+.1%}) {trend_emoji[comp['success_rate']['trend']]}\n"
        f"   耗时: {comp['avg_duration_ms']['from']:.0f}ms → {comp['avg_duration_ms']['to']:.0f}ms "
        f"({comp['avg_duration_ms']['delta']:+.0f}ms) {trend_emoji[comp['avg_duration_ms']['trend']]}\n"
        f"   7天使用: {comp['usage_7d']['from']} → {comp['usage_7d']['to']} "
        f"({comp['usage_7d']['delta']:+d}) {trend_emoji[comp['usage_7d']['trend']]}"
    )
    
    return msg


def get_recent_comparisons(days: int = 7) -> List[Dict]:
    """获取最近 N 天的版本对比记录"""
    if not VERSION_COMPARISON_FILE.exists():
        return []
    
    with open(VERSION_COMPARISON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    return [
        comp for comp in data.get("comparisons", [])
        if comp.get("compared_at", "") >= cutoff
    ]


if __name__ == "__main__":
    import sys
    
    print("Skill Version Comparison 测试")
    print("=" * 60)
    
    # 支持指定 skill_id
    skill_id = None
    if "--skill" in sys.argv:
        idx = sys.argv.index("--skill")
        if idx + 1 < len(sys.argv):
            skill_id = sys.argv[idx + 1]
    
    # 执行对比
    comparisons = compare_skill_versions(skill_id=skill_id)
    
    if not comparisons:
        print("✅ 暂无版本对比数据（需要至少 2 个版本）")
    else:
        print(f"📊 检测到 {len(comparisons)} 个版本对比：\n")
        for comp in comparisons:
            print(format_comparison_message(comp))
            print()
    
    print("\n测试完成！")
