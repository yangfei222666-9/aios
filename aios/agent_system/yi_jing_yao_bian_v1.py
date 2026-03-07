#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爻变系统 v1.0 - AIOS动态适应引擎
基于易经爻变原理，实现系统状态 → 卦象 → 变卦 → 策略的完整闭环

核心功能：
1. 起卦：系统指标 → 64卦之一
2. 识别动爻：哪些指标在变化
3. 生成变卦：未来趋势预测
4. 之卦策略：可执行的行动方案

作者：小九 + 珊瑚海
日期：2026-03-05 01:17
"""

import json
from datetime import datetime
from pathlib import Path

# ==================== 64卦完整映射 ====================

HEXAGRAMS = {
    1: {"name": "乾为天", "symbol": "☰☰", "nature": "刚健", "strategy": "自强不息，主动进取", "action": "提升并发，扩大spawn率"},
    2: {"name": "坤为地", "symbol": "☷☷", "nature": "柔顺", "strategy": "厚德载物，稳健守成", "action": "降低spawn率，优先清理队列"},
    3: {"name": "水雷屯", "symbol": "☵☳", "nature": "初生", "strategy": "先守后攻，稳中求进", "action": "触发LowSuccess regeneration"},
    4: {"name": "山水蒙", "symbol": "☶☵", "nature": "启蒙", "strategy": "学习积累，不急于求成", "action": "启动Learning_Agent，积累经验"},
    5: {"name": "水天需", "symbol": "☵☰", "nature": "等待", "strategy": "等待时机，不可冒进", "action": "延迟非紧急任务，观察系统"},
    6: {"name": "天水讼", "symbol": "☰☵", "nature": "冲突", "strategy": "化解矛盾，寻求和解", "action": "启动对抗性验证，解决冲突"},
    7: {"name": "地水师", "symbol": "☷☵", "nature": "统帅", "strategy": "统一指挥，协调资源", "action": "优化task_executor调度"},
    8: {"name": "水地比", "symbol": "☵☷", "nature": "亲比", "strategy": "团结协作，互相支持", "action": "增强Agent间协作"},
    9: {"name": "风天小畜", "symbol": "☴☰", "nature": "小蓄", "strategy": "小有积蓄，不可大动", "action": "暂停扩张，巩固成果"},
    10: {"name": "天泽履", "symbol": "☰☱", "nature": "履行", "strategy": "谨慎行事，如履薄冰", "action": "启用Safety_Guard，提高警戒"},
    11: {"name": "地天泰", "symbol": "☷☰", "nature": "通泰", "strategy": "天地交泰，万事亨通", "action": "保持当前策略，稳定运行"},
    12: {"name": "天地否", "symbol": "☰☷", "nature": "闭塞", "strategy": "天地不交，需要调整", "action": "触发Auto-fixer，全面检查"},
    13: {"name": "天火同人", "symbol": "☰☲", "nature": "同心", "strategy": "志同道合，共同进退", "action": "增强团队协作"},
    14: {"name": "火天大有", "symbol": "☲☰", "nature": "大有", "strategy": "资源丰富，可以扩张", "action": "提升spawn率，扩大规模"},
    15: {"name": "地山谦", "symbol": "☷☶", "nature": "谦逊", "strategy": "谦虚谨慎，不骄不躁", "action": "降低优先级，避免过载"},
    16: {"name": "雷地豫", "symbol": "☳☷", "nature": "愉悦", "strategy": "顺势而为，保持愉悦", "action": "保持当前节奏"},
    17: {"name": "泽雷随", "symbol": "☱☳", "nature": "随从", "strategy": "顺应变化，灵活调整", "action": "动态调整策略"},
    18: {"name": "山风蛊", "symbol": "☶☴", "nature": "整治", "strategy": "整顿秩序，清理积弊", "action": "清理失败任务，重置状态"},
    19: {"name": "地泽临", "symbol": "☷☱", "nature": "临近", "strategy": "机会来临，把握时机", "action": "提升spawn率"},
    20: {"name": "风地观", "symbol": "☴☷", "nature": "观察", "strategy": "观察形势，不急于行动", "action": "进入观察模式"},
    21: {"name": "火雷噬嗑", "symbol": "☲☳", "nature": "咬合", "strategy": "果断决策，清除障碍", "action": "清理阻塞任务"},
    22: {"name": "山火贲", "symbol": "☶☲", "nature": "装饰", "strategy": "优化外观，提升体验", "action": "优化Dashboard展示"},
    23: {"name": "山地剥", "symbol": "☶☷", "nature": "剥落", "strategy": "防止崩溃，保守防御", "action": "降低spawn率，进入防御模式"},
    24: {"name": "地雷复", "symbol": "☷☳", "nature": "复归", "strategy": "一阳来复，重新开始", "action": "重启失败任务，恢复运行"},
    25: {"name": "天雷无妄", "symbol": "☰☳", "nature": "无妄", "strategy": "顺其自然，不可妄动", "action": "保持当前策略"},
    26: {"name": "山天大畜", "symbol": "☶☰", "nature": "大蓄", "strategy": "积蓄力量，等待时机", "action": "暂停扩张，积累资源"},
    27: {"name": "山雷颐", "symbol": "☶☳", "nature": "颐养", "strategy": "休养生息，恢复元气", "action": "降低负载，恢复健康"},
    28: {"name": "泽风大过", "symbol": "☱☴", "nature": "大过", "strategy": "危机时刻，紧急应对", "action": "触发紧急自愈，暂停任务"},
    29: {"name": "坎为水", "symbol": "☵☵", "nature": "险陷", "strategy": "陷入困境，需要突破", "action": "启动Auto-fixer，全面修复"},
    30: {"name": "离为火", "symbol": "☲☲", "nature": "光明", "strategy": "光明磊落，继续前进", "action": "保持当前策略"},
    31: {"name": "泽山咸", "symbol": "☱☶", "nature": "感应", "strategy": "相互感应，协调一致", "action": "增强Agent协作"},
    32: {"name": "雷风恒", "symbol": "☳☴", "nature": "恒久", "strategy": "持之以恒，长期坚持", "action": "保持当前策略"},
    33: {"name": "天山遁", "symbol": "☰☶", "nature": "退避", "strategy": "暂时退避，保存实力", "action": "降低spawn率，进入防御"},
    34: {"name": "雷天大壮", "symbol": "☳☰", "nature": "大壮", "strategy": "力量强大，可以进取", "action": "提升spawn率，扩大规模"},
    35: {"name": "火地晋", "symbol": "☲☷", "nature": "晋升", "strategy": "稳步前进，逐步提升", "action": "逐步提升spawn率"},
    36: {"name": "地火明夷", "symbol": "☷☲", "nature": "明夷", "strategy": "韬光养晦，等待时机", "action": "降低spawn率，保守运行"},
    37: {"name": "风火家人", "symbol": "☴☲", "nature": "家人", "strategy": "内部和谐，稳定发展", "action": "优化内部协作"},
    38: {"name": "火泽睽", "symbol": "☲☱", "nature": "睽违", "strategy": "意见不合，需要调和", "action": "启动对抗性验证"},
    39: {"name": "水山蹇", "symbol": "☵☶", "nature": "艰难", "strategy": "前路艰难，需要坚持", "action": "触发LowSuccess regeneration"},
    40: {"name": "雷水解", "symbol": "☳☵", "nature": "解除", "strategy": "解除困境，恢复正常", "action": "清理失败任务，恢复运行"},
    41: {"name": "山泽损", "symbol": "☶☱", "nature": "损减", "strategy": "减少消耗，节约资源", "action": "降低spawn率，节约资源"},
    42: {"name": "风雷益", "symbol": "☴☳", "nature": "增益", "strategy": "增加投入，扩大规模", "action": "提升spawn率，扩大规模"},
    43: {"name": "泽天夬", "symbol": "☱☰", "nature": "决断", "strategy": "果断决策，清除障碍", "action": "清理阻塞任务"},
    44: {"name": "天风姤", "symbol": "☰☴", "nature": "遇合", "strategy": "偶然相遇，把握机会", "action": "把握机会，提升spawn率"},
    45: {"name": "泽地萃", "symbol": "☱☷", "nature": "聚集", "strategy": "聚集资源，统一行动", "action": "优化资源调度"},
    46: {"name": "地风升", "symbol": "☷☴", "nature": "上升", "strategy": "稳步上升，逐步提升", "action": "逐步提升spawn率"},
    47: {"name": "泽水困", "symbol": "☱☵", "nature": "困顿", "strategy": "陷入困境，需要突破", "action": "触发Auto-fixer，全面修复"},
    48: {"name": "水风井", "symbol": "☵☴", "nature": "井水", "strategy": "源源不断，持续供给", "action": "保持当前策略"},
    49: {"name": "泽火革", "symbol": "☱☲", "nature": "变革", "strategy": "变革创新，推陈出新", "action": "触发Self-Improving Loop"},
    50: {"name": "火风鼎", "symbol": "☲☴", "nature": "鼎立", "strategy": "稳定鼎立，三足而立", "action": "保持当前策略"},
    51: {"name": "震为雷", "symbol": "☳☳", "nature": "震动", "strategy": "震动变化，灵活应对", "action": "动态调整策略"},
    52: {"name": "艮为山", "symbol": "☶☶", "nature": "止静", "strategy": "停止行动，静观其变", "action": "暂停任务，进入观察"},
    53: {"name": "风山渐", "symbol": "☴☶", "nature": "渐进", "strategy": "循序渐进，稳步前进", "action": "逐步提升spawn率"},
    54: {"name": "雷泽归妹", "symbol": "☳☱", "nature": "归妹", "strategy": "顺应变化，灵活调整", "action": "动态调整策略"},
    55: {"name": "雷火丰", "symbol": "☳☲", "nature": "丰盛", "strategy": "资源丰富，可以扩张", "action": "提升spawn率，扩大规模"},
    56: {"name": "火山旅", "symbol": "☲☶", "nature": "旅行", "strategy": "谨慎行事，不可冒进", "action": "降低spawn率，谨慎运行"},
    57: {"name": "巽为风", "symbol": "☴☴", "nature": "巽顺", "strategy": "顺应变化，灵活调整", "action": "动态调整策略"},
    58: {"name": "兑为泽", "symbol": "☱☱", "nature": "喜悦", "strategy": "保持愉悦，稳定运行", "action": "保持当前策略"},
    59: {"name": "风水涣", "symbol": "☴☵", "nature": "涣散", "strategy": "防止涣散，加强管理", "action": "优化task_executor调度"},
    60: {"name": "水泽节", "symbol": "☵☱", "nature": "节制", "strategy": "节制消耗，避免过度", "action": "降低spawn率，节约资源"},
    61: {"name": "风泽中孚", "symbol": "☴☱", "nature": "中孚", "strategy": "诚信为本，稳定运行", "action": "保持当前策略"},
    62: {"name": "雷山小过", "symbol": "☳☶", "nature": "小过", "strategy": "小有过失，及时纠正", "action": "触发Auto-fixer，修复问题"},
    63: {"name": "水火既济", "symbol": "☵☲", "nature": "既济", "strategy": "已经成功，保持警惕", "action": "保持当前策略，防止松懈"},
    64: {"name": "火水未济", "symbol": "☲☵", "nature": "未济", "strategy": "尚未成功，继续努力", "action": "触发LowSuccess regeneration"},
}

# ==================== 爻变映射表 ====================

# 爻变规则：当前卦 + 动爻位置 → 变卦编号
# 示例：坤卦(2)初爻动 → 复卦(24)
YAO_BIAN_MAP = {
    2: {  # 坤卦
        0: 24,  # 初爻动 → 复卦
        1: 19,  # 二爻动 → 临卦
        2: 36,  # 三爻动 → 明夷卦
        3: 7,   # 四爻动 → 师卦
        4: 46,  # 五爻动 → 升卦
        5: 11,  # 上爻动 → 泰卦
    },
    # 可扩展其他63卦的爻变映射
}

# ==================== 核心函数 ====================

from paths import HEARTBEAT_STATE

def load_system_state():
    """从Heartbeat加载真实系统指标"""
    try:
        # 读取最新的Heartbeat状态
        state_file = HEARTBEAT_STATE
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    "success_rate": data.get("success_rate", 80.0),
                    "evolution_score": data.get("evolution_score", 95.0),
                    "queue_backlog": data.get("queue_backlog", 0),
                    "memory_growth": data.get("memory_growth", 0.0),
                    "api_health": data.get("api_health", 100.0),
                    "confidence": data.get("confidence", 90.0),
                }
    except Exception as e:
        print(f"[WARN] 无法加载系统状态: {e}")
    
    # 默认值（用于测试）
    return {
        "success_rate": 98.5,
        "evolution_score": 99.5,
        "queue_backlog": 0,
        "memory_growth": 1.2,
        "api_health": 100.0,
        "confidence": 99.5,
    }


def identify_moving_lines(state):
    """识别动爻（哪些指标在变化）"""
    moving = []
    
    # 初爻：成功率（基础）
    if state["success_rate"] < 85.0:
        moving.append(0)
    
    # 二爻：Evolution Score（内在）
    if state["evolution_score"] < 95.0:
        moving.append(1)
    
    # 三爻：队列积压（中层）
    if state["queue_backlog"] > 5:
        moving.append(2)
    
    # 四爻：内存增长（资源）
    if state["memory_growth"] > 5.0:
        moving.append(3)
    
    # 五爻：API健康度（外部）
    if state["api_health"] < 95.0:
        moving.append(4)
    
    # 上爻：置信度稳定性（顶层）
    if state["confidence"] < 95.0:
        moving.append(5)
    
    return moving


def cast_hexagram(state):
    """起卦：系统指标 → 卦象"""
    # 简化起卦逻辑：根据成功率判断
    if state["success_rate"] >= 95.0 and state["evolution_score"] >= 98.0:
        current_gua = 2  # 坤卦（稳健）
    elif state["success_rate"] < 60.0:
        current_gua = 28  # 大过卦（危机）
    elif state["success_rate"] < 80.0:
        current_gua = 64  # 未济卦（未完成）
    elif state["queue_backlog"] > 10:
        current_gua = 29  # 坎卦（险陷）
    else:
        current_gua = 11  # 泰卦（通泰）
    
    return current_gua


def generate_bian_gua(current_gua, moving_lines):
    """生成变卦"""
    if not moving_lines:
        return None  # 无动爻，无变卦
    
    # 取第一个动爻（主动爻）
    main_moving = moving_lines[0]
    
    # 查找变卦
    if current_gua in YAO_BIAN_MAP and main_moving in YAO_BIAN_MAP[current_gua]:
        return YAO_BIAN_MAP[current_gua][main_moving]
    
    return None


def generate_strategy(current_gua, bian_gua, state):
    """生成之卦策略"""
    current_info = HEXAGRAMS[current_gua]
    strategy = {
        "current_gua": current_info["name"],
        "current_strategy": current_info["strategy"],
        "current_action": current_info["action"],
        "bian_gua": None,
        "bian_strategy": None,
        "bian_action": None,
        "final_recommendation": current_info["action"],
    }
    
    if bian_gua:
        bian_info = HEXAGRAMS[bian_gua]
        strategy["bian_gua"] = bian_info["name"]
        strategy["bian_strategy"] = bian_info["strategy"]
        strategy["bian_action"] = bian_info["action"]
        strategy["final_recommendation"] = bian_info["action"]
    
    return strategy


def yao_bian_analysis():
    """完整的爻变分析流程"""
    print("=" * 60)
    print("AIOS 爻变系统 v1.0 - 实时起卦分析")
    print("=" * 60)
    
    # 1. 加载系统状态
    state = load_system_state()
    print("\n[1] 系统当前状态:")
    print(f"   成功率: {state['success_rate']:.1f}%")
    print(f"   Evolution Score: {state['evolution_score']:.1f}%")
    print(f"   队列积压: {state['queue_backlog']}")
    print(f"   内存增长: {state['memory_growth']:.1f}%")
    print(f"   API健康度: {state['api_health']:.1f}%")
    print(f"   置信度: {state['confidence']:.1f}%")
    
    # 2. 起卦
    current_gua = cast_hexagram(state)
    current_info = HEXAGRAMS[current_gua]
    print(f"\n[2] 本卦: {current_info['name']} (No.{current_gua})")
    print(f"   卦象: {current_info['symbol']}")
    print(f"   性质: {current_info['nature']}")
    print(f"   策略: {current_info['strategy']}")
    print(f"   行动: {current_info['action']}")
    
    # 3. 识别动爻
    moving_lines = identify_moving_lines(state)
    yao_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    print(f"\n[3] 动爻: {[yao_names[i] for i in moving_lines] if moving_lines else '无'}")
    
    # 4. 生成变卦
    bian_gua = generate_bian_gua(current_gua, moving_lines)
    if bian_gua:
        bian_info = HEXAGRAMS[bian_gua]
        print(f"\n[4] 变卦: {bian_info['name']} (No.{bian_gua})")
        print(f"   卦象: {bian_info['symbol']}")
        print(f"   性质: {bian_info['nature']}")
        print(f"   策略: {bian_info['strategy']}")
        print(f"   行动: {bian_info['action']}")
    else:
        print("\n[4] 变卦: 无（静卦）")
    
    # 5. 生成策略
    strategy = generate_strategy(current_gua, bian_gua, state)
    print(f"\n[5] 最终建议:")
    print(f"   {strategy['final_recommendation']}")
    
    # 6. 保存结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "state": state,
        "current_gua": current_gua,
        "current_gua_name": current_info["name"],
        "moving_lines": moving_lines,
        "bian_gua": bian_gua,
        "bian_gua_name": HEXAGRAMS[bian_gua]["name"] if bian_gua else None,
        "strategy": strategy,
    }
    
    output_file = Path(__file__).parent / "yao_bian_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[6] 结果已保存: {output_file}")
    print("=" * 60)
    
    return result


# ==================== 主程序 ====================

if __name__ == "__main__":
    yao_bian_analysis()
