#!/usr/bin/env python3
"""生成测试数据来验证超时自动学习"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta

TRACE_FILE = Path.home() / ".openclaw" / "workspace" / "aios" / "agent_system" / "data" / "traces" / "agent_traces.jsonl"
TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)

def generate_test_traces():
    """生成测试追踪数据"""
    
    # agent_coder_001: 大部分任务 60-90s，少数超时（>120s）
    print("生成 agent_coder_001 的测试数据...")
    for i in range(50):
        start_time = datetime.now() - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23))
        
        # 90% 的任务在 60-90s 完成
        if random.random() < 0.9:
            duration = random.uniform(60, 90)
            success = True
        else:
            # 10% 的任务超时或失败
            duration = random.uniform(120, 150)
            success = False
        
        trace = {
            "trace_id": f"test_{i:03d}",
            "agent_id": "agent_coder_001",
            "env": "prod",
            "task": f"test_task_{i}",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(seconds=duration)).isoformat(),
            "duration_sec": duration,
            "success": success,
            "error": None if success else "Timeout",
            "tools_used": [],
            "steps": [],
            "metadata": {}
        }
        
        with open(TRACE_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trace, ensure_ascii=False) + '\n')
    
    print(f"✅ 已生成 50 条 agent_coder_001 的追踪数据")
    
    # test-002: 快速任务，5-15s
    print("生成 test-002 的测试数据...")
    for i in range(30):
        start_time = datetime.now() - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23))
        duration = random.uniform(5, 15)
        
        trace = {
            "trace_id": f"test_002_{i:03d}",
            "agent_id": "test-002",
            "env": "test",
            "task": f"test_task_{i}",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(seconds=duration)).isoformat(),
            "duration_sec": duration,
            "success": True,
            "error": None,
            "tools_used": [],
            "steps": [],
            "metadata": {}
        }
        
        with open(TRACE_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trace, ensure_ascii=False) + '\n')
    
    print(f"✅ 已生成 30 条 test-002 的追踪数据")
    
    print(f"\n总计: {TRACE_FILE}")

if __name__ == "__main__":
    generate_test_traces()
