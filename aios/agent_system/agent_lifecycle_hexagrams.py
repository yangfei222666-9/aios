#!/usr/bin/env python3
"""
Agent Lifecycle Hexagrams - 用 64 卦建模 Agent 生命周期

核心思想：
1. 每个 Agent 的 6 个维度（CPU/Memory/API/Queue/Success/Evolution）对应 6 个爻
2. 任何维度的变化都会触发"爻变"，系统自动调整策略
3. 不同卦象对应不同的宽容度和调度权重

Author: 珊瑚海 + 小九
Date: 2026-03-07
"""

from enum import Enum
from typing import Dict, List, Tuple
import json
from pathlib import Path

# ============================================================
# 1. Agent 生命周期卦象枚举
# ============================================================

class AgentHexagram(Enum):
    """Agent 生命周期卦象（精选 12 个核心卦象）"""
    
    # === 初始阶段 ===
    ZHUN = "屯卦"      # 111000 - 草创维艰，刚 Spawn，正在初始化
    MENG = "蒙卦"      # 100010 - 启蒙学习，正在加载模型/数据
    
    # === 成长阶段 ===
    JIAN = "渐卦"      # 110100 - 循序渐进，稳步提升
    SHENG = "升卦"     # 110001 - 上升期，Evolution Score 快速增长
    
    # === 成熟阶段 ===
    QIAN = "乾卦"      # 111111 - 刚健中正，全维度优秀
    KUN = "坤卦"       # 000000 - 厚德载物，稳定可靠
    JIJI = "既济卦"    # 101010 - 功成，连续成功
    
    # === 衰退阶段 ===
    WEIJI = "未济卦"   # 010101 - 重整/退化，连续失败
    JIAN_BLOCK = "蹇卦" # 101000 - 前途艰难，系统阻塞
    KUN_TRAP = "困卦"  # 011010 - 困境，资源耗尽
    
    # === 恢复阶段 ===
    FU = "复卦"        # 100000 - 复苏，从失败中恢复
    HENG = "恒卦"      # 110011 - 持久，长期稳定运行

# ============================================================
# 2. Agent 状态维度（6 个爻）
# ============================================================

class AgentDimension(Enum):
    """Agent 的 6 个维度（对应 6 个爻）"""
    CPU = "cpu_usage"           # 第 1 爻：CPU 占用率
    MEMORY = "memory_usage"     # 第 2 爻：内存占用率
    API = "api_success_rate"    # 第 3 爻：API 成功率
    QUEUE = "queue_length"      # 第 4 爻：任务队列长度
    SUCCESS = "task_success_rate" # 第 5 爻：任务成功率
    EVOLUTION = "evolution_score" # 第 6 爻：Evolution Score

# ============================================================
# 3. 卦象策略配置
# ============================================================

HEXAGRAM_STRATEGIES = {
    # === 初始阶段：高宽容度 ===
    AgentHexagram.ZHUN: {
        "tolerance": {
            "timeout_multiplier": 3.0,      # 超时容忍度 3x
            "failure_threshold": 10,        # 允许失败 10 次
            "min_success_rate": 0.0,        # 不要求成功率
        },
        "scheduling": {
            "priority_weight": 0.3,         # 低优先级
            "max_concurrent": 1,            # 最多 1 个并发
        },
        "actions": [
            "extend_timeout",
            "increase_memory_limit",
            "enable_debug_logging",
        ],
        "description": "草创维艰，给予最大宽容度，允许慢启动"
    },
    
    AgentHexagram.MENG: {
        "tolerance": {
            "timeout_multiplier": 2.5,
            "failure_threshold": 8,
            "min_success_rate": 0.2,
        },
        "scheduling": {
            "priority_weight": 0.4,
            "max_concurrent": 2,
        },
        "actions": [
            "load_training_data",
            "warm_up_model",
            "check_dependencies",
        ],
        "description": "启蒙学习，正在加载模型/数据"
    },
    
    # === 成长阶段：中等宽容度 ===
    AgentHexagram.JIAN: {
        "tolerance": {
            "timeout_multiplier": 1.5,
            "failure_threshold": 5,
            "min_success_rate": 0.6,
        },
        "scheduling": {
            "priority_weight": 0.6,
            "max_concurrent": 3,
        },
        "actions": [
            "monitor_progress",
            "adjust_batch_size",
            "optimize_cache",
        ],
        "description": "循序渐进，稳步提升"
    },
    
    AgentHexagram.SHENG: {
        "tolerance": {
            "timeout_multiplier": 1.2,
            "failure_threshold": 3,
            "min_success_rate": 0.75,
        },
        "scheduling": {
            "priority_weight": 0.8,
            "max_concurrent": 5,
        },
        "actions": [
            "increase_task_allocation",
            "enable_fast_path",
            "reduce_logging_overhead",
        ],
        "description": "上升期，Evolution Score 快速增长"
    },
    
    # === 成熟阶段：低宽容度，高权重 ===
    AgentHexagram.QIAN: {
        "tolerance": {
            "timeout_multiplier": 1.0,
            "failure_threshold": 2,
            "min_success_rate": 0.95,
        },
        "scheduling": {
            "priority_weight": 1.0,
            "max_concurrent": 10,
        },
        "actions": [
            "maximize_throughput",
            "enable_aggressive_caching",
            "prioritize_critical_tasks",
        ],
        "description": "刚健中正，全维度优秀，系统核心干员"
    },
    
    AgentHexagram.KUN: {
        "tolerance": {
            "timeout_multiplier": 1.0,
            "failure_threshold": 1,
            "min_success_rate": 0.98,
        },
        "scheduling": {
            "priority_weight": 0.95,
            "max_concurrent": 8,
        },
        "actions": [
            "maintain_stability",
            "enable_redundancy",
            "monitor_health_metrics",
        ],
        "description": "厚德载物，稳定可靠，长期运行的基石"
    },
    
    AgentHexagram.JIJI: {
        "tolerance": {
            "timeout_multiplier": 1.0,
            "failure_threshold": 1,
            "min_success_rate": 0.98,
        },
        "scheduling": {
            "priority_weight": 1.0,
            "max_concurrent": 10,
        },
        "actions": [
            "celebrate_success",
            "share_best_practices",
            "mentor_junior_agents",
        ],
        "description": "功成，连续成功，Evolution Score 满分"
    },
    
    # === 衰退阶段：触发恢复机制 ===
    AgentHexagram.WEIJI: {
        "tolerance": {
            "timeout_multiplier": 2.0,
            "failure_threshold": 5,
            "min_success_rate": 0.5,
        },
        "scheduling": {
            "priority_weight": 0.3,
            "max_concurrent": 1,
        },
        "actions": [
            "trigger_recovery_mode",
            "analyze_failure_patterns",
            "apply_historical_fixes",
            "consider_graceful_shutdown",
        ],
        "description": "重整/退化，连续失败，需要干预"
    },
    
    AgentHexagram.JIAN_BLOCK: {
        "tolerance": {
            "timeout_multiplier": 3.0,
            "failure_threshold": 3,
            "min_success_rate": 0.3,
        },
        "scheduling": {
            "priority_weight": 0.2,
            "max_concurrent": 1,
        },
        "actions": [
            "suspend_current_task",
            "spawn_network_diagnostic_agent",
            "check_api_health",
            "retry_with_exponential_backoff",
        ],
        "description": "前途艰难，系统阻塞（网络/API 问题）"
    },
    
    AgentHexagram.KUN_TRAP: {
        "tolerance": {
            "timeout_multiplier": 1.5,
            "failure_threshold": 2,
            "min_success_rate": 0.4,
        },
        "scheduling": {
            "priority_weight": 0.1,
            "max_concurrent": 1,
        },
        "actions": [
            "release_resources",
            "scale_down_memory",
            "defer_non_critical_tasks",
            "request_resource_allocation",
        ],
        "description": "困境，资源耗尽（CPU/Memory 不足）"
    },
    
    # === 恢复阶段：观察期 ===
    AgentHexagram.FU: {
        "tolerance": {
            "timeout_multiplier": 2.0,
            "failure_threshold": 5,
            "min_success_rate": 0.6,
        },
        "scheduling": {
            "priority_weight": 0.5,
            "max_concurrent": 2,
        },
        "actions": [
            "monitor_recovery_progress",
            "gradually_increase_load",
            "validate_fixes",
        ],
        "description": "复苏，从失败中恢复"
    },
    
    AgentHexagram.HENG: {
        "tolerance": {
            "timeout_multiplier": 1.0,
            "failure_threshold": 2,
            "min_success_rate": 0.9,
        },
        "scheduling": {
            "priority_weight": 0.85,
            "max_concurrent": 6,
        },
        "actions": [
            "maintain_steady_state",
            "optimize_for_longevity",
            "enable_predictive_maintenance",
        ],
        "description": "持久，长期稳定运行"
    },
}

# ============================================================
# 4. 爻变规则（State Transition Rules）
# ============================================================

def calculate_yao_state(value: float, thresholds: Dict[str, float]) -> int:
    """
    计算单个爻的状态（0 或 1）
    
    Args:
        value: 当前值
        thresholds: 阈值配置 {"low": 0.3, "high": 0.7}
    
    Returns:
        0 (阴爻) 或 1 (阳爻)
    """
    if value >= thresholds["high"]:
        return 1  # 阳爻（优秀）
    elif value <= thresholds["low"]:
        return 0  # 阴爻（不足）
    else:
        return 1 if value >= 0.5 else 0  # 中间值按 50% 分界

def calculate_hexagram(agent_metrics: Dict[str, float]) -> Tuple[str, AgentHexagram]:
    """
    根据 Agent 的 6 个维度计算当前卦象
    
    Args:
        agent_metrics: {
            "cpu_usage": 0.45,
            "memory_usage": 0.60,
            "api_success_rate": 0.95,
            "queue_length": 0.20,  # 归一化到 [0, 1]
            "task_success_rate": 0.88,
            "evolution_score": 0.92
        }
    
    Returns:
        (binary_string, hexagram_enum)
        例如: ("111010", AgentHexagram.JIJI)
    """
    # 阈值配置（可根据业务调整）
    thresholds = {
        "cpu_usage": {"low": 0.3, "high": 0.7},
        "memory_usage": {"low": 0.3, "high": 0.7},
        "api_success_rate": {"low": 0.7, "high": 0.9},
        "queue_length": {"low": 0.3, "high": 0.7},  # 队列长度低为好
        "task_success_rate": {"low": 0.7, "high": 0.9},
        "evolution_score": {"low": 0.7, "high": 0.9},
    }
    
    # 计算 6 个爻的状态
    yao_states = []
    for dim in AgentDimension:
        value = agent_metrics.get(dim.value, 0.5)
        # 队列长度需要反转（低为好）
        if dim == AgentDimension.QUEUE:
            value = 1.0 - value
        yao = calculate_yao_state(value, thresholds[dim.value])
        yao_states.append(str(yao))
    
    binary_string = "".join(yao_states)
    
    # 映射到具体卦象（简化版，实际可用查表法）
    hexagram = map_binary_to_hexagram(binary_string)
    
    return binary_string, hexagram

def map_binary_to_hexagram(binary: str) -> AgentHexagram:
    """
    将 6-bit 二进制映射到卦象（简化版）
    
    实际应用中可以建立完整的 64 卦查找表
    这里只映射核心的 12 个卦象
    """
    mapping = {
        "111000": AgentHexagram.ZHUN,
        "100010": AgentHexagram.MENG,
        "110100": AgentHexagram.JIAN,
        "110001": AgentHexagram.SHENG,
        "111111": AgentHexagram.QIAN,
        "000000": AgentHexagram.KUN,
        "101010": AgentHexagram.JIJI,
        "010101": AgentHexagram.WEIJI,
        "101000": AgentHexagram.JIAN_BLOCK,
        "011010": AgentHexagram.KUN_TRAP,
        "100000": AgentHexagram.FU,
        "110011": AgentHexagram.HENG,
    }
    
    # 如果精确匹配，返回对应卦象
    if binary in mapping:
        return mapping[binary]
    
    # 否则，根据阳爻数量判断大致状态
    yang_count = binary.count("1")
    
    if yang_count >= 5:
        return AgentHexagram.QIAN  # 接近全阳
    elif yang_count >= 4:
        return AgentHexagram.JIJI  # 多数优秀
    elif yang_count >= 3:
        return AgentHexagram.JIAN  # 中等偏上
    elif yang_count >= 2:
        return AgentHexagram.WEIJI  # 中等偏下
    elif yang_count >= 1:
        return AgentHexagram.JIAN_BLOCK  # 多数不足
    else:
        return AgentHexagram.KUN  # 接近全阴（稳定但低调）

def detect_yao_change(old_binary: str, new_binary: str) -> List[int]:
    """
    检测哪些爻发生了变化
    
    Returns:
        变化的爻的索引列表（1-6）
    """
    changes = []
    for i in range(6):
        if old_binary[i] != new_binary[i]:
            changes.append(i + 1)  # 爻的编号从 1 开始
    return changes

# ============================================================
# 5. 策略应用
# ============================================================

def get_strategy(hexagram: AgentHexagram) -> Dict:
    """获取卦象对应的策略"""
    return HEXAGRAM_STRATEGIES.get(hexagram, HEXAGRAM_STRATEGIES[AgentHexagram.WEIJI])

def apply_strategy(agent_id: str, hexagram: AgentHexagram, strategy: Dict) -> Dict:
    """
    应用卦象策略到 Agent
    
    Returns:
        应用结果 {"actions_taken": [...], "config_updated": {...}}
    """
    result = {
        "agent_id": agent_id,
        "hexagram": hexagram.value,
        "actions_taken": [],
        "config_updated": {}
    }
    
    # 1. 更新超时配置
    timeout_multiplier = strategy["tolerance"]["timeout_multiplier"]
    result["config_updated"]["timeout_multiplier"] = timeout_multiplier
    result["actions_taken"].append(f"adjust_timeout_to_{timeout_multiplier}x")
    
    # 2. 更新调度权重
    priority_weight = strategy["scheduling"]["priority_weight"]
    result["config_updated"]["priority_weight"] = priority_weight
    result["actions_taken"].append(f"set_priority_weight_to_{priority_weight}")
    
    # 3. 执行推荐动作
    for action in strategy["actions"]:
        result["actions_taken"].append(action)
    
    return result

# ============================================================
# 6. 主函数：Agent 生命周期管理
# ============================================================

def manage_agent_lifecycle(agent_id: str, agent_metrics: Dict[str, float], 
                          previous_hexagram: str = None) -> Dict:
    """
    管理 Agent 生命周期
    
    Args:
        agent_id: Agent ID
        agent_metrics: 当前指标
        previous_hexagram: 上一次的卦象（用于检测爻变）
    
    Returns:
        {
            "agent_id": "coder-001",
            "current_hexagram": "既济卦",
            "binary": "101010",
            "yao_changes": [4],  # 第 4 爻发生变化
            "strategy": {...},
            "actions": {...}
        }
    """
    # 1. 计算当前卦象
    binary, hexagram = calculate_hexagram(agent_metrics)
    
    # 2. 检测爻变
    yao_changes = []
    if previous_hexagram:
        yao_changes = detect_yao_change(previous_hexagram, binary)
    
    # 3. 获取策略
    strategy = get_strategy(hexagram)
    
    # 4. 应用策略
    actions = apply_strategy(agent_id, hexagram, strategy)
    
    return {
        "agent_id": agent_id,
        "current_hexagram": hexagram.value,
        "binary": binary,
        "yao_changes": yao_changes,
        "strategy": strategy,
        "actions": actions,
        "timestamp": Path(__file__).stat().st_mtime
    }

# ============================================================
# 7. 测试用例
# ============================================================

if __name__ == "__main__":
    print("=== Agent Lifecycle Hexagrams 测试 ===\n")
    
    # 测试场景 1：新 Agent 刚启动（屯卦）
    print("场景 1：新 Agent 刚启动")
    metrics_new = {
        "cpu_usage": 0.85,  # 高 CPU（初始化）
        "memory_usage": 0.75,  # 高内存（加载模型）
        "api_success_rate": 0.0,  # 还没开始调用 API
        "queue_length": 0.0,  # 队列为空
        "task_success_rate": 0.0,  # 还没完成任务
        "evolution_score": 0.0,  # 初始分数
    }
    result = manage_agent_lifecycle("agent-new-001", metrics_new)
    print(f"卦象: {result['current_hexagram']} ({result['binary']})")
    print(f"策略: {result['strategy']['description']}")
    print(f"动作: {result['actions']['actions_taken'][:3]}")
    print()
    
    # 测试场景 2：成熟 Agent（既济卦）
    print("场景 2：成熟 Agent")
    metrics_mature = {
        "cpu_usage": 0.45,
        "memory_usage": 0.60,
        "api_success_rate": 0.98,
        "queue_length": 0.15,
        "task_success_rate": 0.96,
        "evolution_score": 0.95,
    }
    result = manage_agent_lifecycle("agent-mature-001", metrics_mature)
    print(f"卦象: {result['current_hexagram']} ({result['binary']})")
    print(f"策略: {result['strategy']['description']}")
    print(f"优先级权重: {result['strategy']['scheduling']['priority_weight']}")
    print()
    
    # 测试场景 3：衰退 Agent（未济卦）
    print("场景 3：衰退 Agent")
    metrics_degraded = {
        "cpu_usage": 0.25,
        "memory_usage": 0.40,
        "api_success_rate": 0.45,
        "queue_length": 0.80,
        "task_success_rate": 0.35,
        "evolution_score": 0.50,
    }
    result = manage_agent_lifecycle("agent-degraded-001", metrics_degraded)
    print(f"卦象: {result['current_hexagram']} ({result['binary']})")
    print(f"策略: {result['strategy']['description']}")
    print(f"恢复动作: {result['actions']['actions_taken'][:3]}")
    print()
    
    # 测试场景 4：爻变检测（既济 → 蹇）
    print("场景 4：爻变检测（API 突然超时）")
    old_binary = "101010"  # 既济卦
    new_metrics = metrics_mature.copy()
    new_metrics["api_success_rate"] = 0.30  # API 突然大量失败
    result = manage_agent_lifecycle("agent-mature-001", new_metrics, old_binary)
    print(f"卦象变化: 既济卦 ({old_binary}) → {result['current_hexagram']} ({result['binary']})")
    print(f"爻变: 第 {result['yao_changes']} 爻")
    print(f"触发动作: {result['actions']['actions_taken'][:3]}")
