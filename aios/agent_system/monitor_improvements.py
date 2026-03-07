#!/usr/bin/env python3
"""
AIOS 改进效果监控器
每小时运行一次，追踪改进措施的效果
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")
AIOS_ROOT = WORKSPACE / "aios"
MONITOR_STATE = AIOS_ROOT / "agent_system" / "data" / "monitor_state.json"

def load_state():
    """加载监控状态"""
    if MONITOR_STATE.exists():
        with open(MONITOR_STATE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "baseline": None,
        "history": [],
        "improvements_applied_at": datetime.now().isoformat()
    }

def save_state(state):
    """保存监控状态"""
    with open(MONITOR_STATE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def analyze_current_status():
    """分析当前状态"""
    # 读取错误分类配置
    config_file = AIOS_ROOT / "agent_system" / "data" / "error_classification.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 读取最新报告
    reports_dir = AIOS_ROOT / "agent_system" / "data" / "evolution" / "reports"
    reports = sorted(reports_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not reports:
        return None
    
    with open(reports[0], 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    traces = report.get('phases', {}).get('observe', {}).get('traces', [])
    failures = [t for t in traces if not t.get('success', True)]
    
    # 错误分类
    error_categories = Counter()
    for failure in failures:
        error_msg = failure.get('error', '').lower()
        categorized = False
        
        for category, cat_config in config['error_categories'].items():
            for pattern in cat_config['patterns']:
                if pattern.lower() in error_msg:
                    error_categories[category] += 1
                    categorized = True
                    break
            if categorized:
                break
        
        if not categorized:
            error_categories['unknown'] += 1
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tasks": len(traces),
        "failed_tasks": len(failures),
        "success_rate": (len(traces) - len(failures)) / len(traces) if traces else 0,
        "error_categories": dict(error_categories),
        "timeout_count": error_categories.get('timeout', 0),
        "logic_count": error_categories.get('logic', 0),
        "unknown_count": error_categories.get('unknown', 0)
    }

def main():
    state = load_state()
    current = analyze_current_status()
    
    if not current:
        print("MONITOR_NO_DATA")
        return
    
    # 设置基线（首次运行）
    if not state['baseline']:
        state['baseline'] = current
        save_state(state)
        print("MONITOR_BASELINE_SET")
        print(f"  成功率: {current['success_rate']*100:.1f}%")
        print(f"  Timeout: {current['timeout_count']}次")
        print(f"  Logic错误: {current['logic_count']}次")
        print(f"  Unknown: {current['unknown_count']}次")
        return
    
    # 对比改进效果
    baseline = state['baseline']
    state['history'].append(current)
    
    # 只保留最近24小时的历史
    cutoff = datetime.now() - timedelta(hours=24)
    state['history'] = [
        h for h in state['history']
        if datetime.fromisoformat(h['timestamp']) > cutoff
    ]
    
    save_state(state)
    
    # 计算改进
    success_rate_delta = (current['success_rate'] - baseline['success_rate']) * 100
    timeout_delta = current['timeout_count'] - baseline['timeout_count']
    logic_delta = current['logic_count'] - baseline['logic_count']
    unknown_delta = current['unknown_count'] - baseline['unknown_count']
    
    print("MONITOR_COMPARISON")
    print(f"  成功率: {current['success_rate']*100:.1f}% ({success_rate_delta:+.1f}%)")
    print(f"  Timeout: {current['timeout_count']}次 ({timeout_delta:+d})")
    print(f"  Logic错误: {current['logic_count']}次 ({logic_delta:+d})")
    print(f"  Unknown: {current['unknown_count']}次 ({unknown_delta:+d})")
    
    # 判断是否有显著改进
    if success_rate_delta > 5 or timeout_delta < -3:
        print("\n[OK] 改进效果显著！")
    elif success_rate_delta < -5 or timeout_delta > 3:
        print("\n[WARN] 性能下降，需要调查")
    else:
        print("\n[REPORT] 持续监控中...")

if __name__ == "__main__":
    main()
