#!/usr/bin/env python3
"""
evolution_guard.py - Evolution Score 守护检查（防回归）
每次 Heartbeat 调用，检测 evolution_score.json 的健康度
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

from paths import EVOLUTION_SCORE

def check_evolution_health() -> dict:
    """
    检查 evolution_score.json 健康度
    
    Returns:
        {
            "status": "ok" | "stale" | "missing" | "low",
            "score": float,
            "age_hours": float,
            "message": str
        }
    """
    score_file = EVOLUTION_SCORE
    
    # 检查1：文件是否存在
    if not score_file.exists():
        return {
            "status": "missing",
            "score": 0,
            "age_hours": 999,
            "message": "evolution_score.json not found"
        }
    
    # 读取文件
    try:
        with open(score_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {
            "status": "error",
            "score": 0,
            "age_hours": 999,
            "message": f"Failed to read evolution_score.json: {e}"
        }
    
    score = data.get('score', 0)
    last_update = data.get('last_update', 'unknown')
    
    # 检查2：时间戳是否新鲜（超过2小时告警）
    try:
        update_time = datetime.fromisoformat(last_update)
        age_hours = (datetime.now() - update_time).total_seconds() / 3600
    except:
        age_hours = 999
    
    if age_hours > 2:
        return {
            "status": "stale",
            "score": score,
            "age_hours": age_hours,
            "message": f"evolution_score.json is stale ({age_hours:.1f}h old, threshold: 2h)"
        }
    
    # 检查3：分数是否异常低（低于阈值且时间戳陈旧）
    if score < 70 and age_hours > 1:
        return {
            "status": "low",
            "score": score,
            "age_hours": age_hours,
            "message": f"Evolution Score is low ({score:.1f}) and stale ({age_hours:.1f}h old)"
        }
    
    # 一切正常
    return {
        "status": "ok",
        "score": score,
        "age_hours": age_hours,
        "message": f"Evolution Score: {score:.1f} (updated {age_hours:.1f}h ago)"
    }


def main():
    """CLI 入口"""
    result = check_evolution_health()
    
    print(f"[EVOLUTION_GUARD] Status: {result['status']}")
    print(f"  Score: {result['score']:.1f}")
    print(f"  Age: {result['age_hours']:.1f}h")
    print(f"  Message: {result['message']}")
    
    # 返回状态码（0=ok, 1=warning, 2=error）
    if result['status'] == 'ok':
        return 0
    elif result['status'] in ['stale', 'low']:
        return 1
    else:
        return 2


if __name__ == "__main__":
    import sys
    sys.exit(main())
