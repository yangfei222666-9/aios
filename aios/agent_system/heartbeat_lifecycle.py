#!/usr/bin/env python3
"""
Heartbeat Lifecycle Integration - 心跳生命周期集成
在 Heartbeat 中调用 Lifecycle Engine，输出 Agent 当前阶段
"""

import json
import sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from agent_lifecycle_engine import calculate_all_lifecycle_scores


def get_lifecycle_stage_name(lifecycle_state: str, failure_rate: float, failure_streak: int) -> str:
    """
    将 lifecycle_state 映射到易经卦象阶段
    
    Args:
        lifecycle_state: active/shadow/disabled
        failure_rate: 失败率
        failure_streak: 连续失败次数
    
    Returns:
        str: 卦象阶段名称
    """
    if lifecycle_state == "disabled":
        return "坎卦 - 险中求安（永久禁用）"
    
    if lifecycle_state == "shadow":
        return "坤卦 - 厚德载物（冷却期）"
    
    # active 状态下，根据失败率细分
    if failure_rate == 0.0:
        return "既济 - 功成身退（稳定运行）"
    elif failure_rate < 0.3:
        return "渐卦 - 循序渐进（成长中）"
    elif failure_rate < 0.5:
        return "需卦 - 待时而动（需要观察）"
    elif failure_rate < 0.7:
        return "蒙卦 - 启蒙教育（早期探索）"
    else:
        return "屯卦 - 艰难起步（初始阶段）"


def format_lifecycle_report(scores: dict) -> str:
    """
    格式化生命周期报告
    
    Args:
        scores: {agent_id: lifecycle_score}
    
    Returns:
        str: 格式化的报告文本
    """
    if not scores:
        return "LIFECYCLE_NO_AGENTS"
    
    lines = []
    lines.append("🔄 Agent Lifecycle Status")
    lines.append("")
    
    # 按 routable + lifecycle_state 分桶
    routable_active = []
    routable_degraded = []
    non_routable_shadow = []
    non_routable_disabled = []
    
    for agent_id, score in scores.items():
        routable = score.get("routable", False)
        state = score["lifecycle_state"]
        
        if routable and state == "active":
            routable_active.append((agent_id, score))
        elif routable and state in ("shadow", "recovering"):
            routable_degraded.append((agent_id, score))
        elif not routable and state == "shadow":
            non_routable_shadow.append((agent_id, score))
        elif not routable or state == "disabled":
            non_routable_disabled.append((agent_id, score))
    
    # 输出 routable active agents
    if routable_active:
        lines.append(f"✅ Active & Routable ({len(routable_active)}):")
        for agent_id, score in sorted(routable_active, key=lambda x: x[1]["last_failure_rate"]):
            stage = get_lifecycle_stage_name(
                score["lifecycle_state"],
                score["last_failure_rate"],
                score["last_failure_streak"]
            )
            lines.append(f"  • {agent_id}")
            lines.append(f"    Stage: {stage}")
            lines.append(f"    Failure Rate: {score['last_failure_rate']*100:.1f}%")
            if score["last_failure_streak"] > 0:
                lines.append(f"    Failure Streak: {score['last_failure_streak']}")
            lines.append(f"    Timeout: {score['timeout']}s | Priority: {score['priority']}")
            lines.append("")
    
    # 输出 routable but degraded
    if routable_degraded:
        lines.append(f"⚠️  Degraded but Routable ({len(routable_degraded)}):")
        for agent_id, score in routable_degraded:
            stage = get_lifecycle_stage_name(
                score["lifecycle_state"],
                score["last_failure_rate"],
                score["last_failure_streak"]
            )
            lines.append(f"  • {agent_id}")
            lines.append(f"    Stage: {stage}")
            lines.append(f"    Failure Rate: {score['last_failure_rate']*100:.1f}%")
            if score["cooldown_until"]:
                lines.append(f"    Cooldown Until: {score['cooldown_until']}")
            lines.append("")
    
    # 输出 non-routable shadow (保留但禁用)
    if non_routable_shadow:
        lines.append(f"🔕 Shadow / Non-Routable ({len(non_routable_shadow)}):")
        for agent_id, score in non_routable_shadow[:10]:  # 最多显示10个
            gate = score.get("availability_gate", "unknown")
            lines.append(f"  • {agent_id} (gate: {gate})")
        if len(non_routable_shadow) > 10:
            lines.append(f"  ... and {len(non_routable_shadow) - 10} more")
        lines.append("")
    
    # 输出 disabled agents
    if non_routable_disabled:
        lines.append(f"❌ Disabled ({len(non_routable_disabled)}):")
        for agent_id, score in non_routable_disabled[:10]:
            gate = score.get("availability_gate", "unknown")
            lines.append(f"  • {agent_id} (gate: {gate})")
        if len(non_routable_disabled) > 10:
            lines.append(f"  ... and {len(non_routable_disabled) - 10} more")
        lines.append("")
    
    # 统计摘要
    lines.append("📊 Summary:")
    lines.append(f"  Active & Routable: {len(routable_active)}")
    lines.append(f"  Degraded: {len(routable_degraded)}")
    lines.append(f"  Shadow: {len(non_routable_shadow)}")
    lines.append(f"  Disabled: {len(non_routable_disabled)}")
    
    return "\n".join(lines)


def run_lifecycle_check(write_back: bool = False) -> str:
    """
    运行生命周期检查
    
    Args:
        write_back: 是否写回 agents.json（默认 False，只读模式）
    
    Returns:
        str: 报告文本
    """
    # 计算所有 Agent 的生命周期状态
    scores = calculate_all_lifecycle_scores()
    
    # 格式化报告
    report = format_lifecycle_report(scores)
    
    # 可选：写回 agents.json
    if write_back:
        from agent_lifecycle_engine import write_lifecycle_states
        updated_count = write_lifecycle_states(scores)
        report += f"\n\n✍️  Updated {updated_count} agents in agents.json"
    
    # 记录到日志
    log_file = BASE / "lifecycle_check.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"{'='*60}\n")
        f.write(report)
        f.write("\n")
    
    return report


def main():
    """
    主函数 - 可以直接运行测试
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Lifecycle Check")
    parser.add_argument("--write", action="store_true", help="Write back to agents.json")
    args = parser.parse_args()
    
    report = run_lifecycle_check(write_back=args.write)
    print(report)


if __name__ == "__main__":
    main()
