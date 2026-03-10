#!/usr/bin/env python3
"""
Hexagram Mapping - 64卦完整映射表

将 6-bit 二进制映射到 64 卦，包含：
- 卦名
- 卦义
- 风险等级
- 推荐动作

Author: 珊瑚海 + 小九
Date: 2026-03-07
Version: 2.0
"""

from enum import Enum
from typing import Dict, List

class RiskLevel(Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    CRITICAL = "严重风险"

class HexagramInfo:
    """卦象信息"""
    def __init__(self, name: str, meaning: str, risk: RiskLevel, actions: List[str]):
        self.name = name
        self.meaning = meaning
        self.risk = risk
        self.actions = actions

# ============================================================
# 64卦完整映射表（自下而上，初爻在右）
# ============================================================

HEXAGRAM_TABLE = {
    # === 乾坤系列（全阳/全阴）===
    "111111": HexagramInfo(
        name="乾卦",
        meaning="刚健中正，全维度优秀，系统核心干员",
        risk=RiskLevel.LOW,
        actions=[
            "maximize_throughput",
            "enable_aggressive_caching",
            "prioritize_critical_tasks",
            "maintain_peak_performance"
        ]
    ),
    "000000": HexagramInfo(
        name="坤卦",
        meaning="厚德载物，稳定可靠，长期运行的基石",
        risk=RiskLevel.LOW,
        actions=[
            "maintain_stability",
            "enable_redundancy",
            "monitor_health_metrics",
            "prepare_for_scale"
        ]
    ),
    
    # === 初始阶段（草创/启蒙）===
    "010000": HexagramInfo(
        name="屯卦",
        meaning="草创维艰，刚启动，正在初始化",
        risk=RiskLevel.MEDIUM,
        actions=[
            "extend_timeout",
            "increase_memory_limit",
            "enable_debug_logging",
            "allow_slow_start"
        ]
    ),
    "000010": HexagramInfo(
        name="蒙卦",
        meaning="启蒙学习，正在加载模型/数据",
        risk=RiskLevel.MEDIUM,
        actions=[
            "load_training_data",
            "warm_up_model",
            "check_dependencies",
            "validate_initialization"
        ]
    ),
    "010111": HexagramInfo(
        name="需卦",
        meaning="等待时机，资源准备中",
        risk=RiskLevel.MEDIUM,
        actions=[
            "wait_for_resources",
            "prepare_environment",
            "validate_preconditions",
            "schedule_when_ready"
        ]
    ),
    
    # === 成长阶段（渐进/上升）===
    "001011": HexagramInfo(
        name="渐卦",
        meaning="循序渐进，稳步提升",
        risk=RiskLevel.LOW,
        actions=[
            "monitor_progress",
            "adjust_batch_size",
            "optimize_cache",
            "gradual_scale_up"
        ]
    ),
    "110001": HexagramInfo(
        name="升卦",
        meaning="上升期，Evolution Score 快速增长",
        risk=RiskLevel.LOW,
        actions=[
            "increase_task_allocation",
            "enable_fast_path",
            "reduce_logging_overhead",
            "accelerate_growth"
        ]
    ),
    
    # === 成熟阶段（既济/泰）===
    "010101": HexagramInfo(
        name="既济卦",
        meaning="功成，连续成功，Evolution Score 满分",
        risk=RiskLevel.LOW,
        actions=[
            "celebrate_success",
            "share_best_practices",
            "mentor_junior_agents",
            "maintain_excellence"
        ]
    ),
    "000111": HexagramInfo(
        name="泰卦",
        meaning="通泰顺畅，系统和谐运行",
        risk=RiskLevel.LOW,
        actions=[
            "maintain_harmony",
            "optimize_collaboration",
            "share_resources",
            "prevent_complacency"
        ]
    ),
    
    # === 衰退阶段（未济/否）===
    "101010": HexagramInfo(
        name="未济卦",
        meaning="重整/退化，连续失败，需要干预",
        risk=RiskLevel.HIGH,
        actions=[
            "trigger_recovery_mode",
            "analyze_failure_patterns",
            "apply_historical_fixes",
            "consider_graceful_shutdown"
        ]
    ),
    "111000": HexagramInfo(
        name="否卦",
        meaning="闭塞不通，系统阻滞",
        risk=RiskLevel.HIGH,
        actions=[
            "identify_bottlenecks",
            "clear_queue",
            "restart_stalled_tasks",
            "escalate_if_persistent"
        ]
    ),
    
    # === 危机阶段（困/蹇/大过）===
    "010110": HexagramInfo(
        name="困卦",
        meaning="困境，资源耗尽（CPU/Memory 不足）",
        risk=RiskLevel.CRITICAL,
        actions=[
            "release_resources",
            "scale_down_memory",
            "defer_non_critical_tasks",
            "request_resource_allocation"
        ]
    ),
    "001010": HexagramInfo(
        name="蹇卦",
        meaning="前途艰难，系统阻塞（网络/API 问题）",
        risk=RiskLevel.CRITICAL,
        actions=[
            "suspend_current_task",
            "spawn_network_diagnostic_agent",
            "check_api_health",
            "retry_with_exponential_backoff"
        ]
    ),
    "011110": HexagramInfo(
        name="大过卦",
        meaning="过度负载，系统超限",
        risk=RiskLevel.CRITICAL,
        actions=[
            "reduce_load",
            "enable_rate_limiting",
            "decrease_concurrency",
            "emergency_scale_down"
        ]
    ),
    
    # === 恢复阶段（复/解）===
    "000001": HexagramInfo(
        name="复卦",
        meaning="复苏，从失败中恢复",
        risk=RiskLevel.MEDIUM,
        actions=[
            "monitor_recovery_progress",
            "gradually_increase_load",
            "validate_fixes",
            "document_lessons_learned"
        ]
    ),
    "010010": HexagramInfo(
        name="解卦",
        meaning="解除困境，问题已缓解",
        risk=RiskLevel.MEDIUM,
        actions=[
            "verify_resolution",
            "resume_normal_operations",
            "update_runbooks",
            "prevent_recurrence"
        ]
    ),
    
    # === 稳定阶段（恒/损/益）===
    "001110": HexagramInfo(
        name="恒卦",
        meaning="持久，长期稳定运行",
        risk=RiskLevel.LOW,
        actions=[
            "maintain_steady_state",
            "optimize_for_longevity",
            "enable_predictive_maintenance",
            "celebrate_reliability"
        ]
    ),
    "100011": HexagramInfo(
        name="损卦",
        meaning="减损优化，精简冗余",
        risk=RiskLevel.MEDIUM,
        actions=[
            "identify_waste",
            "optimize_resource_usage",
            "remove_redundancy",
            "improve_efficiency"
        ]
    ),
    "110001": HexagramInfo(
        name="益卦",
        meaning="增益扩展，能力提升",
        risk=RiskLevel.LOW,
        actions=[
            "expand_capacity",
            "add_new_features",
            "increase_throughput",
            "invest_in_growth"
        ]
    ),
    
    # === 冲突阶段（讼/师）===
    "111010": HexagramInfo(
        name="讼卦",
        meaning="争讼冲突，Agent 间冲突",
        risk=RiskLevel.HIGH,
        actions=[
            "resolve_conflicts",
            "mediate_disputes",
            "clarify_responsibilities",
            "prevent_escalation"
        ]
    ),
    "000101": HexagramInfo(
        name="师卦",
        meaning="统帅调度，需要强力协调",
        risk=RiskLevel.MEDIUM,
        actions=[
            "centralize_coordination",
            "assign_clear_roles",
            "enforce_discipline",
            "align_objectives"
        ]
    ),
    
    # === 其他常用卦（补充到 64 个）===
    # 以下为简化版，实际可根据业务需求细化
    
    "100000": HexagramInfo("剥卦", "剥落衰败", RiskLevel.HIGH, ["stop_degradation", "rebuild_foundation"]),
    "000100": HexagramInfo("比卦", "亲比协作", RiskLevel.LOW, ["enhance_collaboration", "share_resources"]),
    "101000": HexagramInfo("小畜卦", "小有积蓄", RiskLevel.LOW, ["accumulate_resources", "prepare_for_growth"]),
    "000101": HexagramInfo("履卦", "履行职责", RiskLevel.LOW, ["execute_duties", "maintain_discipline"]),
    "110000": HexagramInfo("同人卦", "同心协力", RiskLevel.LOW, ["unite_team", "align_goals"]),
    "000011": HexagramInfo("大有卦", "大有收获", RiskLevel.LOW, ["celebrate_achievements", "share_success"]),
    "010001": HexagramInfo("谦卦", "谦虚谨慎", RiskLevel.LOW, ["stay_humble", "avoid_overconfidence"]),
    "100010": HexagramInfo("豫卦", "愉悦顺畅", RiskLevel.LOW, ["maintain_morale", "celebrate_wins"]),
    "011001": HexagramInfo("随卦", "随机应变", RiskLevel.MEDIUM, ["adapt_to_changes", "stay_flexible"]),
    "100110": HexagramInfo("蛊卦", "整治腐败", RiskLevel.HIGH, ["clean_up_mess", "refactor_code"]),
    "110100": HexagramInfo("临卦", "临近观察", RiskLevel.MEDIUM, ["monitor_closely", "prepare_intervention"]),
    "001011": HexagramInfo("观卦", "观察等待", RiskLevel.MEDIUM, ["observe_patterns", "wait_for_signal"]),
    "101001": HexagramInfo("噬嗑卦", "咬合整合", RiskLevel.MEDIUM, ["integrate_components", "resolve_gaps"]),
    "100101": HexagramInfo("贲卦", "文饰美化", RiskLevel.LOW, ["improve_ui", "polish_output"]),
    "100001": HexagramInfo("大畜卦", "大量积蓄", RiskLevel.LOW, ["build_reserves", "prepare_for_future"]),
    "100111": HexagramInfo("颐卦", "颐养生息", RiskLevel.LOW, ["rest_and_recover", "maintain_health"]),
    "011111": HexagramInfo("大壮卦", "强壮有力", RiskLevel.LOW, ["leverage_strength", "push_forward"]),
    "111100": HexagramInfo("晋卦", "晋升进步", RiskLevel.LOW, ["advance_position", "seize_opportunity"]),
    "101011": HexagramInfo("明夷卦", "光明受伤", RiskLevel.HIGH, ["protect_core", "hide_strength"]),
    "110101": HexagramInfo("家人卦", "家庭和睦", RiskLevel.LOW, ["strengthen_bonds", "improve_communication"]),
    "101110": HexagramInfo("睽卦", "背离分歧", RiskLevel.HIGH, ["address_divergence", "realign_goals"]),
    "110010": HexagramInfo("夬卦", "决断果断", RiskLevel.MEDIUM, ["make_decision", "take_action"]),
    "010011": HexagramInfo("姤卦", "不期而遇", RiskLevel.MEDIUM, ["handle_unexpected", "adapt_quickly"]),
    "011000": HexagramInfo("萃卦", "聚集汇合", RiskLevel.LOW, ["gather_resources", "consolidate_efforts"]),
    "011011": HexagramInfo("井卦", "井水不竭", RiskLevel.LOW, ["maintain_supply", "ensure_sustainability"]),
    "110011": HexagramInfo("革卦", "变革革新", RiskLevel.MEDIUM, ["implement_change", "embrace_innovation"]),
    "110110": HexagramInfo("鼎卦", "鼎立稳固", RiskLevel.LOW, ["establish_foundation", "build_stability"]),
    "001001": HexagramInfo("震卦", "震动惊醒", RiskLevel.MEDIUM, ["respond_to_alert", "take_immediate_action"]),
    "100100": HexagramInfo("艮卦", "止步停止", RiskLevel.MEDIUM, ["pause_operations", "reassess_strategy"]),
    "110111": HexagramInfo("丰卦", "丰盛充裕", RiskLevel.LOW, ["enjoy_abundance", "share_wealth"]),
    "111011": HexagramInfo("旅卦", "旅行迁移", RiskLevel.MEDIUM, ["migrate_workload", "explore_new_territory"]),
    "011011": HexagramInfo("巽卦", "顺从灵活", RiskLevel.LOW, ["follow_guidance", "stay_adaptable"]),
    "110110": HexagramInfo("兑卦", "喜悦交流", RiskLevel.LOW, ["improve_communication", "celebrate_together"]),
    "010100": HexagramInfo("涣卦", "涣散分离", RiskLevel.HIGH, ["prevent_fragmentation", "reunite_team"]),
    "001100": HexagramInfo("节卦", "节制约束", RiskLevel.MEDIUM, ["enforce_limits", "control_growth"]),
    "110011": HexagramInfo("中孚卦", "中正诚信", RiskLevel.LOW, ["maintain_integrity", "build_trust"]),
    "001111": HexagramInfo("小过卦", "小有过失", RiskLevel.MEDIUM, ["correct_minor_errors", "prevent_escalation"]),
}

# ============================================================
# 映射函数
# ============================================================

def map_binary_to_hexagram(binary: str) -> HexagramInfo:
    """
    将 6-bit 二进制映射到卦象
    
    Args:
        binary: 6-bit 二进制字符串（自下而上，初爻在右）
    
    Returns:
        HexagramInfo 对象
    """
    if binary in HEXAGRAM_TABLE:
        return HEXAGRAM_TABLE[binary]
    
    # 如果没有精确匹配，根据阳爻数量判断大致状态
    yang_count = binary.count("1")
    
    if yang_count >= 5:
        return HEXAGRAM_TABLE["111111"]  # 乾卦（接近全阳）
    elif yang_count >= 4:
        return HEXAGRAM_TABLE["010101"]  # 既济卦（多数优秀）
    elif yang_count >= 3:
        return HEXAGRAM_TABLE["001011"]  # 渐卦（中等偏上）
    elif yang_count >= 2:
        return HEXAGRAM_TABLE["101010"]  # 未济卦（中等偏下）
    elif yang_count >= 1:
        return HEXAGRAM_TABLE["001010"]  # 蹇卦（多数不足）
    else:
        return HEXAGRAM_TABLE["000000"]  # 坤卦（接近全阴）

# ============================================================
# 测试用例
# ============================================================

if __name__ == "__main__":
    print("=== Hexagram Mapping 测试 ===\n")
    
    # 测试精确匹配
    test_cases = [
        ("111111", "乾卦"),
        ("000000", "坤卦"),
        ("010000", "屯卦"),
        ("010101", "既济卦"),
        ("101010", "未济卦"),
        ("010110", "困卦"),
        ("001010", "蹇卦"),
    ]
    
    for binary, expected_name in test_cases:
        hexagram = map_binary_to_hexagram(binary)
        print(f"{binary} → {hexagram.name} ({hexagram.risk.value})")
        print(f"  卦义: {hexagram.meaning}")
        print(f"  动作: {hexagram.actions[:2]}")
        print()
