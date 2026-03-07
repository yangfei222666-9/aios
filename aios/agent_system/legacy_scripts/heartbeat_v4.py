#!/usr/bin/env python3
"""
AIOS Heartbeat v4.0 - 集成 Self-Improving Loop v2.0

新增功能：
- 每小时评估系统健康度
- 健康度 < 60 时发出警告
- 每天生成一次完整报告
- 自动触发改进流程
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from self_improving_loop_v2 import SelfImprovingLoopV2


# 状态文件
STATE_FILE = Path(__file__).parent / "data" / "heartbeat_v4_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state():
    """加载状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "last_health_check": None,
        "last_daily_report": None,
        "health_check_count": 0,
        "daily_report_count": 0
    }


def save_state(state):
    """保存状态"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def should_check_health(state):
    """是否应该检查健康度（每小时一次）"""
    if not state["last_health_check"]:
        return True
    
    last_check = datetime.fromisoformat(state["last_health_check"])
    now = datetime.now()
    
    return (now - last_check) > timedelta(hours=1)


def should_generate_report(state):
    """是否应该生成报告（每天一次）"""
    if not state["last_daily_report"]:
        return True
    
    last_report = datetime.fromisoformat(state["last_daily_report"])
    now = datetime.now()
    
    # 每天 00:00 生成一次
    return now.date() > last_report.date()


def check_system_health(loop, state):
    """检查系统健康度"""
    print("[HEALTH] Checking system health...")
    
    # 评估系统
    system_eval = loop.evaluate_system(time_window_hours=1)
    
    health_score = system_eval['health_score']
    grade = system_eval['grade']
    
    print(f"   Health Score: {health_score:.2f}/100 ({grade})")
    
    # 更新状态
    state["last_health_check"] = datetime.now().isoformat()
    state["health_check_count"] += 1
    
    # 如果健康度低，发出警告
    if health_score < 60:
        print(f"[WARNING] System health is low!")
        print(f"   Error Rate: {system_eval['events']['error_rate']:.2%}")
        print(f"   Task Success Rate: {system_eval['tasks']['success_rate']:.2%}")
        return "HEALTH_WARNING"
    elif health_score < 80:
        print(f"[WARNING] System health is moderate")
        return "HEALTH_OK"
    else:
        print(f"[OK] System health is good")
        return "HEALTH_GOOD"


def generate_daily_report(loop, state):
    """生成每日报告"""
    print("[REPORT] Generating daily report...")
    
    # 生成报告
    report = loop.generate_report(time_window_hours=24)
    
    print(f"   Report Time: {report['timestamp']}")
    print(f"   System Health: {report['system']['health_score']:.2f}/100 ({report['system']['grade']})")
    print(f"   Total Tasks: {report['tasks']['total']}")
    print(f"   Task Success Rate: {report['tasks']['success_rate']:.2%}")
    print(f"   Agent Count: {report['agents'].__len__()}")
    
    # 更新状态
    state["last_daily_report"] = datetime.now().isoformat()
    state["daily_report_count"] += 1
    
    print(f"[OK] Report generated")
    return "REPORT_GENERATED"


def heartbeat_v4():
    """Heartbeat v4.0 主函数"""
    print("AIOS Heartbeat v4.0 Started\n")
    
    # 加载状态
    state = load_state()
    
    # 初始化 Self-Improving Loop
    loop = SelfImprovingLoopV2()
    
    results = []
    
    # 1. 检查系统健康度（每小时）
    if should_check_health(state):
        result = check_system_health(loop, state)
        results.append(result)
    else:
        print("[SKIP] Health check (not time yet)")
    
    print()
    
    # 2. 生成每日报告（每天）
    if should_generate_report(state):
        result = generate_daily_report(loop, state)
        results.append(result)
    else:
        print("[SKIP] Daily report (not time yet)")
    
    print()
    
    # 保存状态
    save_state(state)
    
    # 输出结果
    if not results:
        print("HEARTBEAT_OK (no actions)")
    else:
        print(f"HEARTBEAT_OK ({', '.join(results)})")
    
    print("\nHeartbeat Completed")


if __name__ == "__main__":
    heartbeat_v4()
