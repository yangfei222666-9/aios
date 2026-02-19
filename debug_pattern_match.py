#!/usr/bin/env python3
"""
调试模式匹配
"""

import re
import sys

def test_pattern_matching():
    """测试模式匹配"""
    text = "检查 系统 噢"
    patterns = [
        r"检查.*状态",
        r"查看.*状态", 
        r"系统状态",
        r"状态检查",
        r"运行状态",
        r"检查系统",
        r"查看系统",
        r"系统检查",
    ]
    
    print("模式匹配测试")
    print("=" * 60)
    print(f"文本: '{text}'")
    print()
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            print(f"✅ 匹配: {pattern}")
            print(f"   匹配部分: '{match.group()}'")
        else:
            print(f"❌ 不匹配: {pattern}")
    
    print()
    
    # 测试空格处理
    print("测试空格处理:")
    text_variants = [
        "检查系统",
        "检查 系统",
        "检查系统状态",
        "检查 系统 状态",
    ]
    
    for variant in text_variants:
        print(f"\n文本: '{variant}'")
        for pattern in patterns:
            if re.search(pattern, variant):
                print(f"  匹配: {pattern}")

def main():
    test_pattern_matching()
    return 0

if __name__ == "__main__":
    sys.exit(main())