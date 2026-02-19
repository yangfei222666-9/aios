#!/usr/bin/env python3
"""
全面测试唤醒词检测功能
包括边缘情况和特殊字符
"""

import sys
sys.path.insert(0, '.')

from tools.wake_listener import match_wake, normalize_zh

def test_normalize_zh():
    """测试文本规范化函数"""
    print("文本规范化测试")
    print("=" * 40)
    
    test_cases = [
        ("小九", "小九"),
        ("小 九", "小 九"),
        ("小\u200b九", "小九"),  # 零宽空格
        ("小\u200c九", "小九"),  # 零宽非连接符
        ("小\u200d九", "小九"),  # 零宽连接符
        ("小\ufeff九", "小九"),  # BOM
        ("  小九  ", "小九"),
        ("小\n九", "小 九"),
        ("小\t九", "小 九"),
    ]
    
    for input_text, expected in test_cases:
        result = normalize_zh(input_text)
        passed = result == expected
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} | 输入: {repr(input_text)}")
        print(f"     期望: {repr(expected)}, 实际: {repr(result)}")
    
    print()

def test_match_wake_comprehensive():
    """全面测试唤醒词匹配"""
    wake_phrases = ["小九", "你好小九", "小酒", "hi 小九"]
    
    print("全面唤醒词匹配测试")
    print("=" * 40)
    print(f"唤醒词列表: {wake_phrases}")
    print()
    
    test_cases = [
        # 基本测试
        ("小九", True, "精确匹配"),
        ("小酒", True, "同音字匹配"),
        ("你好小九", True, "长唤醒词"),
        ("hi 小九", True, "中英混合"),
        
        # 包含测试
        ("小九你好", True, "包含唤醒词"),
        ("你好小九你好", True, "中间包含"),
        ("hi 小九你好", True, "混合包含"),
        
        # 边界测试
        ("小", False, "部分匹配"),
        ("九", False, "部分匹配"),
        ("小九小九", True, "重复包含"),
        ("小酒小酒", True, "同音重复"),
        
        # 特殊字符测试
        ("小\u200b九", True, "零宽空格"),
        ("小\u200c九", True, "零宽非连接符"),
        ("小\u200d九", True, "零宽连接符"),
        ("小\ufeff九", True, "BOM字符"),
        
        # 大小写测试
        ("HI 小九", True, "大写英文"),
        ("Hi 小九", True, "混合大小写"),
        
        # 否定测试
        ("其他词", False, "完全不相关"),
        ("九小", False, "顺序颠倒"),
        ("小九儿", True, "包含扩展"),
        ("小酒馆", True, "同音扩展"),
        
        # 空白测试
        (" 小九 ", True, "前后空格"),
        ("小 九", True, "中间空格"),
        ("小\n九", True, "换行符"),
        ("小\t九", True, "制表符"),
    ]
    
    all_passed = True
    
    for text, expected, description in test_cases:
        result = match_wake(text, wake_phrases)
        passed = result == expected
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} | {description}")
        print(f"     输入: {repr(text)}")
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

def test_realistic_scenarios():
    """测试真实场景"""
    print("真实场景测试")
    print("=" * 40)
    
    wake_phrases = ["小九", "你好小九", "小酒"]
    
    # 模拟 ASR 可能产生的输出
    realistic_cases = [
        ("小九", True, "清晰发音"),
        ("小酒", True, "同音误识别"),
        ("小舅", False, "不同音但相似"),
        ("小九检查系统状态", True, "唤醒词+命令"),
        ("你好小九添加笔记", True, "长唤醒词+命令"),
        ("小九小九", True, "重复唤醒"),
        ("小九 小九", True, "空格分隔"),
    ]
    
    for text, expected, description in realistic_cases:
        result = match_wake(text, wake_phrases)
        passed = result == expected
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} | {description}")
        print(f"     输入: '{text}'")
        print(f"     期望: {expected}, 实际: {result}")
    
    print()

if __name__ == "__main__":
    print("语音唤醒系统全面测试")
    print("=" * 60)
    print()
    
    # 运行所有测试
    test_normalize_zh()
    test_match_wake_comprehensive()
    test_realistic_scenarios()
    
    print("=" * 60)
    print("测试完成！")