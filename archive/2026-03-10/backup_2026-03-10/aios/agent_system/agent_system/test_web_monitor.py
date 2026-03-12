#!/usr/bin/env python3
"""
Web Monitor 测试脚本 - 模拟变化检测
"""
import json
from pathlib import Path

STATE_FILE = Path(__file__).parent / "web_monitor_state.json"

def test_change_detection():
    """测试变化检测"""
    print("[TEST] Simulating change detection...")
    
    # 读取状态
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    # 模拟 Data Dragon Versions 变化
    if "Data Dragon Versions" in state:
        old_version = state["Data Dragon Versions"]["last_value"]
        new_version = "16.5.1"  # 模拟新版本
        
        print(f"\n[SIMULATE] Data Dragon Versions")
        print(f"   Old: {old_version}")
        print(f"   New: {new_version}")
        
        # 修改状态
        state["Data Dragon Versions"]["last_value"] = new_version
        
        # 保存
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        print(f"[SAVE] State updated")
        print(f"\n[NEXT] Run: python web_monitor.py --filter 6h")
        print(f"   Expected: Detect change and queue notification")
    else:
        print("[ERROR] Data Dragon Versions not found in state")
        print("[INFO] Run web_monitor.py first to initialize state")

if __name__ == "__main__":
    test_change_detection()
