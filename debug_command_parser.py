#!/usr/bin/env python3
"""
调试命令解析器
"""

import sys
sys.path.insert(0, '.')

from tools.voice_command_handler import VoiceCommandHandler

def debug_command_parsing():
    """调试命令解析"""
    audio_text = "小九 检查 系统 噢"
    
    print("调试命令解析")
    print("=" * 60)
    print(f"原始文本: '{audio_text}'")
    print()
    
    handler = VoiceCommandHandler()
    
    # 1. 测试移除唤醒词前缀
    print("1. 测试移除唤醒词前缀")
    cleaned = handler._remove_wake_prefix(audio_text)
    print(f"   清理后: '{cleaned}'")
    
    # 2. 检查命令模式
    print("\n2. 检查命令模式匹配")
    
    # 手动检查每个模式
    cleaned_text = cleaned
    print(f"   清理文本: '{cleaned_text}'")
    
    for cmd_type, cmd_info in handler.command_patterns.items():
        for pattern in cmd_info["patterns"]:
            import re
            if re.search(pattern, cleaned_text):
                print(f"   匹配到: {cmd_type} - 模式: {pattern}")
                print(f"   描述: {cmd_info['description']}")
    
    # 3. 测试 parse_command 方法
    print("\n3. 测试 parse_command 方法")
    cmd_type, cmd_info = handler.parse_command(audio_text)
    
    print(f"   返回类型: {cmd_type}")
    print(f"   返回信息: {cmd_info}")
    
    if cmd_info:
        print(f"   清理文本: '{cmd_info.get('cleaned')}'")
        print(f"   参数: {cmd_info.get('params')}")
    
    # 4. 测试其他可能的文本格式
    print("\n4. 测试其他文本格式")
    test_variants = [
        "小九检查系统",
        "检查系统",
        "检查系统状态",
        "小九检查系统状态",
        "检查系统状态噢",
    ]
    
    for variant in test_variants:
        cmd_type, cmd_info = handler.parse_command(variant)
        if cmd_type:
            print(f"   '{variant}' -> {cmd_type}")
        else:
            print(f"   '{variant}' -> 未识别")

def main():
    debug_command_parsing()
    return 0

if __name__ == "__main__":
    sys.exit(main())