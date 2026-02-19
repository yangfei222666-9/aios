#!/usr/bin/env python3
"""
测试唤醒词检测功能
"""

import sys
sys.path.insert(0, '.')

from tools.wake_listener import match_wake

def test_wake_detection():
    """测试唤醒词检测"""
    wake_phrases = ["小九", "你好小九", "小酒"]
    
    test_cases = [
        ("小九", True),
        ("小酒", True),
        ("你好小九", True),
        ("小九你好", True),  # 包含即可
        ("九小", False),
        ("其他词", False),
    ]
    
    print("唤醒词检测测试")
    print("=" * 40)
    print(f"唤醒词列表: {wake_phrases}")
    print()
    
    all_passed = True
    
    for text, expected in test_cases:
        result = match_wake(text, wake_phrases)
        passed = result == expected
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} | 输入: '{text}'")
        print(f"     期望: {expected}, 实际: {result}")
        
        if not passed:
            all_passed = False
    
    print()
    print("=" * 40)
    
    if all_passed:
        print("[PASS] 所有测试通过！")
        return 0
    else:
        print("[FAIL] 有测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(test_wake_detection())