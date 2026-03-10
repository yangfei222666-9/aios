#!/usr/bin/env python3
"""
Hexagram Guardrails - 强兜底规则层

职责：
- 禁止规则：某些状态绝不能落入稳定卦
- 强制规则：某些状态必须进入风险卦
- 按故障类型分流风险卦（蹇/困/大过/未济）

Author: 珊瑚海 + 小九
Date: 2026-03-07
Version: 2.0
"""

from typing import Dict, Tuple, List
from hexagram_mapping import HexagramInfo, RiskLevel
from hexagram_lines import LineScore

# ============================================================
# 风险卦模板
# ============================================================

def _hexagram_jian() -> HexagramInfo:
    return HexagramInfo(
        name="蹇卦",
        meaning="前途艰难，系统阻塞（基础设施/执行受阻）",
        risk=RiskLevel.CRITICAL,
        actions=[
            "suspend_current_task",
            "spawn_network_diagnostic_agent",
            "check_api_health",
            "retry_with_exponential_backoff"
        ]
    )

def _hexagram_kun_trap() -> HexagramInfo:
    return HexagramInfo(
        name="困卦",
        meaning="困境，资源耗尽（多维度低分）",
        risk=RiskLevel.CRITICAL,
        actions=[
            "release_resources",
            "scale_down_memory",
            "defer_non_critical_tasks",
            "request_resource_allocation"
        ]
    )

def _hexagram_da_guo() -> HexagramInfo:
    return HexagramInfo(
        name="大过卦",
        meaning="过度负载，系统超限（硬跑风险）",
        risk=RiskLevel.CRITICAL,
        actions=[
            "reduce_load",
            "enable_rate_limiting",
            "decrease_concurrency",
            "emergency_scale_down"
        ]
    )

def _hexagram_wei_ji() -> HexagramInfo:
    return HexagramInfo(
        name="未济卦",
        meaning="重整/退化，系统未完成修复",
        risk=RiskLevel.HIGH,
        actions=[
            "trigger_recovery_mode",
            "analyze_failure_patterns",
            "apply_historical_fixes",
            "consider_graceful_shutdown"
        ]
    )

# ============================================================
# 兜底规则入口
# ============================================================

def apply_guardrails(lines: Dict[str, LineScore], base_hexagram: HexagramInfo) -> Tuple[HexagramInfo, List[str]]:
    """
    应用强兜底规则

    规则：
    A. 禁止规则
       - infra < 0.20 → 禁止稳定卦（乾/坤/既济/泰）
    B. 强制规则
       - infra < 0.10 → 强制进入风险卦
       - infra < 0.10 且 execution < 0.25 → 蹇/困（阻塞型）
       - infra < 0.10 且 execution >= 0.25 且系统仍高负载 → 大过（过载型）
       - infra < 0.20 且 execution < 0.25 → 未济（重整型）
       - 多爻低分（>=2）且稳定卦 → 困（多维异常）

    Returns:
        (修正后的卦象, 触发原因列表)
    """
    triggered = []
    infra = lines["line_1_infra"].score
    execution = lines["line_2_execution"].score
    routing = lines["line_4_routing"].score
    collaboration = lines["line_5_collaboration"].score
    governance = lines["line_6_governance"].score

    stable_names = {"乾卦", "坤卦", "既济卦", "泰卦"}

    # 禁止规则：基础设施较差，不允许稳定卦
    if infra < 0.20 and base_hexagram.name in stable_names:
        triggered.append("guardrail_forbid_stable_when_infra_low")
        base_hexagram = _hexagram_wei_ji()

    # 强制规则：基础设施灾难
    if infra < 0.10:
        triggered.append("guardrail_infra_critical")

        # 执行层也低：阻塞型
        if execution < 0.25:
            # 如果调度/协作/治理也低，判为困
            if sum(1 for s in [routing, collaboration, governance] if s < 0.3) >= 2:
                triggered.append("guardrail_multi_dimension_low")
                return _hexagram_kun_trap(), triggered
            return _hexagram_jian(), triggered

        # 基础设施坏但系统还在硬跑：过载型
        high_load_signal = (routing > 0.7 and collaboration > 0.7 and governance > 0.7)
        if high_load_signal:
            triggered.append("guardrail_hard_running_overload")
            return _hexagram_da_guo(), triggered

        # 其他情况：未济（未完成修复）
        triggered.append("guardrail_recovery_needed")
        return _hexagram_wei_ji(), triggered

    # 强制规则：执行层极低
    if execution < 0.25:
        triggered.append("guardrail_execution_critical")
        return _hexagram_wei_ji(), triggered

    # 多爻低分：稳定卦降级到困
    low_lines = [name for name, line in lines.items() if line.score < 0.30]
    if len(low_lines) >= 2 and base_hexagram.name in stable_names:
        triggered.append("guardrail_multi_dimension_low")
        return _hexagram_kun_trap(), triggered

    return base_hexagram, triggered

# ============================================================
# 测试用例
# ============================================================

if __name__ == "__main__":
    from hexagram_lines import calculate_six_lines

    print("=== Guardrails 测试 ===\n")

    # 场景：基础设施灾难 + 执行低
    metrics_fail = {
        "api_health": 0.05,
        "network_latency": 0.95,
        "dependency_available": 0.1,
        "task_success_rate": 0.15,
        "timeout_rate": 0.9,
        "retry_rate": 0.8,
        "recommendation_hit_rate": 0.7,
        "learning_gain": 0.6,
        "experience_validity": 0.7,
        "router_accuracy": 0.6,
        "queue_length": 0.8,
        "dispatch_stability": 0.5,
        "agent_cooperation": 0.6,
        "resource_sharing": 0.6,
        "conflict_rate": 0.3,
        "evolution_score": 70.0,
        "canary_health": 0.6,
        "global_stability": 0.5,
    }

    lines = calculate_six_lines(metrics_fail)
    base = HexagramInfo("乾卦", "稳定", RiskLevel.LOW, ["noop"])
    guarded, reasons = apply_guardrails(lines, base)
    print(f"Guarded → {guarded.name} | Reasons: {reasons}")
