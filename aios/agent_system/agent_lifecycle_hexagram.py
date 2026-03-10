#!/usr/bin/env python3
"""
Agent Lifecycle Hexagram - Agent 生命周期卦象（独立模块）

与全局卦象分离，专注回答：这个 Agent 现在处于哪个成长/退化阶段？

主路径：
- 屯卦：刚启用，样本极少，困难多
- 蒙卦：能力边界未明，结果波动大
- 需卦：暂时缺少足够任务，继续等待样本
- 渐卦：开始稳定成长，质量上升
- 既济卦：成熟稳定，可放心 active
- 未济卦：开始退化，需修复或降级

Author: 珊瑚海 + 小九
Date: 2026-03-07
Version: 2.0
"""

from typing import Dict
from dataclasses import dataclass
from enum import Enum

class LifecycleStage(Enum):
    """Agent 生命周期阶段"""
    ZHUN = "屯卦"      # 草创维艰
    MENG = "蒙卦"      # 启蒙学习
    XU = "需卦"        # 等待时机
    JIAN = "渐卦"      # 循序渐进
    JIJI = "既济卦"    # 功成圆满
    WEIJI = "未济卦"   # 退化待修

@dataclass
class LifecycleMetrics:
    """Agent 生命周期指标"""
    task_count: int  # 总任务数
    success_rate: float  # 成功率（0~1）
    useful_output_count: int  # 有效输出数
    recent_failures: int  # 最近失败次数
    last_run_age_hours: float  # 上次运行距今小时数
    trend: str  # 趋势（improving/stable/degrading）

@dataclass
class LifecycleHexagram:
    """生命周期卦象结果"""
    stage: LifecycleStage
    meaning: str
    confidence: float
    recommended_actions: list
    explanation: str

# ============================================================
# 生命周期卦象判定规则
# ============================================================

def calculate_lifecycle_hexagram(metrics: LifecycleMetrics) -> LifecycleHexagram:
    """
    计算 Agent 生命周期卦象
    
    判定逻辑：
    1. 屯卦：task_count < 5（样本极少）
    2. 蒙卦：task_count < 20 且 success_rate 波动大（能力未明）
    3. 需卦：task_count < 10 且 last_run_age > 24h（等待任务）
    4. 渐卦：task_count >= 20 且 trend = improving（稳定成长）
    5. 既济卦：task_count >= 50 且 success_rate >= 0.85 且 trend = stable（成熟稳定）
    6. 未济卦：recent_failures >= 3 或 trend = degrading（退化）
    """
    
    # === 屯卦：刚启用，样本极少 ===
    if metrics.task_count < 5:
        return LifecycleHexagram(
            stage=LifecycleStage.ZHUN,
            meaning="草创维艰，刚启用，样本极少，困难多",
            confidence=0.9,
            recommended_actions=[
                "extend_timeout_3x",
                "allow_slow_start",
                "enable_debug_logging",
                "collect_initial_samples"
            ],
            explanation=f"""
生命周期阶段：屯卦（草创维艰）

Agent 状态：
  • 总任务数：{metrics.task_count}（样本极少）
  • 成功率：{metrics.success_rate:.1%}
  • 最近失败：{metrics.recent_failures} 次
  • 上次运行：{metrics.last_run_age_hours:.1f} 小时前
  • 趋势：{metrics.trend}

判定依据：
  • 任务数 < 5，处于初始阶段
  • 需要更多样本才能评估能力

建议动作：
  • 给予最大宽容度（超时 3x）
  • 允许慢启动，不急于评估
  • 开启调试日志，收集初始样本
  • 至少完成 10 个任务后再评估
"""
        )
    
    # === 需卦：等待任务，长时间未运行 ===
    if metrics.task_count < 10 and metrics.last_run_age_hours > 24:
        return LifecycleHexagram(
            stage=LifecycleStage.XU,
            meaning="等待时机，暂时缺少足够任务，继续等待样本",
            confidence=0.85,
            recommended_actions=[
                "wait_for_tasks",
                "prepare_environment",
                "validate_preconditions",
                "schedule_when_ready"
            ],
            explanation=f"""
生命周期阶段：需卦（等待时机）

Agent 状态：
  • 总任务数：{metrics.task_count}（样本不足）
  • 成功率：{metrics.success_rate:.1%}
  • 最近失败：{metrics.recent_failures} 次
  • 上次运行：{metrics.last_run_age_hours:.1f} 小时前（长时间未运行）
  • 趋势：{metrics.trend}

判定依据：
  • 任务数 < 10，样本不足
  • 上次运行 > 24h，长时间未调度
  • 需要更多任务才能进入成长期

建议动作：
  • 等待任务分配
  • 准备运行环境
  • 验证前置条件
  • 任务就绪时立即调度
"""
        )
    
    # === 未济卦：退化，需要修复 ===
    if metrics.recent_failures >= 3 or metrics.trend == "degrading":
        return LifecycleHexagram(
            stage=LifecycleStage.WEIJI,
            meaning="退化待修，开始退化，需修复或降级",
            confidence=0.9,
            recommended_actions=[
                "trigger_recovery_mode",
                "analyze_failure_patterns",
                "apply_historical_fixes",
                "consider_shadow_mode"
            ],
            explanation=f"""
生命周期阶段：未济卦（退化待修）

Agent 状态：
  • 总任务数：{metrics.task_count}
  • 成功率：{metrics.success_rate:.1%}
  • 最近失败：{metrics.recent_failures} 次（连续失败）
  • 上次运行：{metrics.last_run_age_hours:.1f} 小时前
  • 趋势：{metrics.trend}（退化）

判定依据：
  • 最近失败 >= 3 次，或趋势为 degrading
  • Agent 能力明显下降
  • 需要干预修复

建议动作：
  • 触发恢复模式
  • 分析失败模式
  • 应用历史修复策略
  • 考虑降级到 shadow 模式
"""
        )
    
    # === 既济卦：成熟稳定 ===
    if metrics.task_count >= 50 and metrics.success_rate >= 0.85 and metrics.trend == "stable":
        return LifecycleHexagram(
            stage=LifecycleStage.JIJI,
            meaning="功成圆满，成熟稳定，可放心 active",
            confidence=0.95,
            recommended_actions=[
                "maintain_excellence",
                "share_best_practices",
                "mentor_junior_agents",
                "celebrate_success"
            ],
            explanation=f"""
生命周期阶段：既济卦（功成圆满）

Agent 状态：
  • 总任务数：{metrics.task_count}（样本充足）
  • 成功率：{metrics.success_rate:.1%}（优秀）
  • 最近失败：{metrics.recent_failures} 次
  • 上次运行：{metrics.last_run_age_hours:.1f} 小时前
  • 趋势：{metrics.trend}（稳定）

判定依据：
  • 任务数 >= 50，样本充足
  • 成功率 >= 85%，表现优秀
  • 趋势稳定，可放心依赖

建议动作：
  • 保持卓越表现
  • 分享最佳实践
  • 指导新 Agent
  • 庆祝成功
"""
        )
    
    # === 渐卦：稳定成长 ===
    if metrics.task_count >= 20 and metrics.trend == "improving":
        return LifecycleHexagram(
            stage=LifecycleStage.JIAN,
            meaning="循序渐进，开始稳定成长，质量上升",
            confidence=0.85,
            recommended_actions=[
                "monitor_progress",
                "gradually_increase_load",
                "optimize_performance",
                "prepare_for_active"
            ],
            explanation=f"""
生命周期阶段：渐卦（循序渐进）

Agent 状态：
  • 总任务数：{metrics.task_count}（样本充足）
  • 成功率：{metrics.success_rate:.1%}
  • 最近失败：{metrics.recent_failures} 次
  • 上次运行：{metrics.last_run_age_hours:.1f} 小时前
  • 趋势：{metrics.trend}（改善中）

判定依据：
  • 任务数 >= 20，样本充足
  • 趋势为 improving，质量上升
  • 正在稳定成长期

建议动作：
  • 监控进展
  • 逐步增加负载
  • 优化性能
  • 准备进入 active 模式
"""
        )
    
    # === 蒙卦：能力边界未明（默认） ===
    return LifecycleHexagram(
        stage=LifecycleStage.MENG,
        meaning="启蒙学习，能力边界未明，结果波动大",
        confidence=0.75,
        recommended_actions=[
            "collect_more_samples",
            "validate_capabilities",
            "adjust_expectations",
            "monitor_closely"
        ],
        explanation=f"""
生命周期阶段：蒙卦（启蒙学习）

Agent 状态：
  • 总任务数：{metrics.task_count}
  • 成功率：{metrics.success_rate:.1%}
  • 最近失败：{metrics.recent_failures} 次
  • 上次运行：{metrics.last_run_age_hours:.1f} 小时前
  • 趋势：{metrics.trend}

判定依据：
  • 任务数 < 20，样本不足
  • 能力边界未明确
  • 结果可能波动

建议动作：
  • 收集更多样本
  • 验证能力边界
  • 调整预期
  • 密切监控
"""
    )

# ============================================================
# 测试用例
# ============================================================

if __name__ == "__main__":
    print("=== Agent Lifecycle Hexagram 测试 ===\n")
    
    # 测试场景 1：新 Agent（屯卦）
    print("=" * 60)
    print("场景 1：新 Agent（屯卦）")
    print("=" * 60)
    metrics_new = LifecycleMetrics(
        task_count=2,
        success_rate=0.5,
        useful_output_count=1,
        recent_failures=1,
        last_run_age_hours=0.5,
        trend="unknown"
    )
    result = calculate_lifecycle_hexagram(metrics_new)
    print(result.explanation)
    print()
    
    # 测试场景 2：等待任务（需卦）
    print("=" * 60)
    print("场景 2：等待任务（需卦）")
    print("=" * 60)
    metrics_waiting = LifecycleMetrics(
        task_count=8,
        success_rate=0.75,
        useful_output_count=6,
        recent_failures=0,
        last_run_age_hours=30.0,
        trend="stable"
    )
    result = calculate_lifecycle_hexagram(metrics_waiting)
    print(result.explanation)
    print()
    
    # 测试场景 3：稳定成长（渐卦）
    print("=" * 60)
    print("场景 3：稳定成长（渐卦）")
    print("=" * 60)
    metrics_growing = LifecycleMetrics(
        task_count=35,
        success_rate=0.80,
        useful_output_count=28,
        recent_failures=1,
        last_run_age_hours=2.0,
        trend="improving"
    )
    result = calculate_lifecycle_hexagram(metrics_growing)
    print(result.explanation)
    print()
    
    # 测试场景 4：成熟稳定（既济卦）
    print("=" * 60)
    print("场景 4：成熟稳定（既济卦）")
    print("=" * 60)
    metrics_mature = LifecycleMetrics(
        task_count=120,
        success_rate=0.92,
        useful_output_count=110,
        recent_failures=0,
        last_run_age_hours=1.0,
        trend="stable"
    )
    result = calculate_lifecycle_hexagram(metrics_mature)
    print(result.explanation)
    print()
    
    # 测试场景 5：退化（未济卦）
    print("=" * 60)
    print("场景 5：退化（未济卦）")
    print("=" * 60)
    metrics_degraded = LifecycleMetrics(
        task_count=80,
        success_rate=0.65,
        useful_output_count=52,
        recent_failures=5,
        last_run_age_hours=0.5,
        trend="degrading"
    )
    result = calculate_lifecycle_hexagram(metrics_degraded)
    print(result.explanation)
    print()
    
    # 测试场景 6：能力未明（蒙卦）
    print("=" * 60)
    print("场景 6：能力未明（蒙卦）")
    print("=" * 60)
    metrics_uncertain = LifecycleMetrics(
        task_count=15,
        success_rate=0.70,
        useful_output_count=10,
        recent_failures=2,
        last_run_age_hours=5.0,
        trend="stable"
    )
    result = calculate_lifecycle_hexagram(metrics_uncertain)
    print(result.explanation)
