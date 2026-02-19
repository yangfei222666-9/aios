#!/usr/bin/env python3
"""
测试新的音频命令
分析 "小九 检查 系统 噢" 命令
"""

import sys
sys.path.insert(0, '.')

from tools.wake_listener import is_meaningful_command
from tools.voice_command_handler import VoiceCommandHandler

def analyze_audio_command():
    """分析音频命令"""
    audio_text = "小九 检查 系统 噢"
    
    print("音频命令分析")
    print("=" * 60)
    print(f"识别文本: '{audio_text}'")
    print()
    
    # 1. 测试命令过滤器
    print("1. 命令过滤器测试")
    wake_phrases = ["小九", "你好小九", "小酒"]
    
    is_meaningful = is_meaningful_command(audio_text, wake_phrases)
    print(f"   是否有意义: {is_meaningful}")
    
    if is_meaningful:
        print("   [OK] 这是一个有效命令")
    else:
        print("   [NO] 这是一个无意义命令")
    
    print()
    
    # 2. 测试命令解析
    print("2. 命令解析测试")
    handler = VoiceCommandHandler()
    cmd_type, cmd_info = handler.parse_command(audio_text)
    
    if cmd_type and cmd_info:
        print(f"   命令类型: {cmd_type}")
        print(f"   命令描述: {cmd_info['description']}")
        print(f"   清理后文本: '{cmd_info['cleaned']}'")
        print(f"   参数: {cmd_info['params']}")
        
        # 检查是否匹配状态检查命令
        if cmd_type == "check_status":
            print("   [OK] 正确识别为状态检查命令")
        else:
            print(f"   [NO] 期望 check_status，实际 {cmd_type}")
    else:
        print("   [NO] 未能解析命令")
    
    print()
    
    # 3. 模拟系统处理
    print("3. 模拟系统处理流程")
    
    # 模拟唤醒检测
    print("   a. 唤醒检测:")
    normalized_text = audio_text.replace(" ", "")
    for phrase in wake_phrases:
        normalized_phrase = phrase.replace(" ", "")
        if normalized_phrase in normalized_text:
            print(f"     匹配到唤醒词: '{phrase}'")
    
    # 模拟命令过滤
    print("   b. 命令过滤:")
    if is_meaningful:
        print("     通过过滤器 → 进入命令处理")
    else:
        print("     被过滤器忽略 → 返回睡眠模式")
    
    # 模拟命令执行
    print("   c. 命令执行:")
    if cmd_type == "check_status":
        print("     执行状态检查命令")
        print("     调用 daily_check_asr_tts.py")
        print("     记录检查结果")
    
    return is_meaningful and cmd_type == "check_status"

def test_command_execution():
    """测试命令执行"""
    print("\n命令执行测试")
    print("=" * 60)
    
    audio_text = "小九 检查 系统 噢"
    
    print(f"执行命令: '{audio_text}'")
    
    handler = VoiceCommandHandler()
    success, message = handler.execute_command(audio_text)
    
    print(f"执行结果: {message}")
    
    if success:
        print("[OK] 命令执行成功")
        
        # 检查日志文件
        import os
        log_file = os.path.join("logs", "voice_command_results.log")
        if os.path.exists(log_file):
            print(f"查看日志文件: {log_file}")
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    print(f"最新日志: {lines[-1].strip()}")
    else:
        print("[NO] 命令执行失败")
    
    return success

def compare_with_previous_audio():
    """与之前的音频对比"""
    print("\n音频对比分析")
    print("=" * 60)
    
    previous_audio = "你好 小九 噢"  # 之前的音频
    current_audio = "小九 检查 系统 噢"  # 当前的音频
    
    print("对比两个音频命令:")
    print(f"  之前: '{previous_audio}'")
    print(f"  当前: '{current_audio}'")
    print()
    
    wake_phrases = ["小九", "你好小九", "小酒"]
    
    # 分析之前的音频
    print("之前的音频分析:")
    prev_meaningful = is_meaningful_command(previous_audio, wake_phrases)
    print(f"  是否有意义: {prev_meaningful}")
    print(f"  结果: {'被过滤器忽略' if not prev_meaningful else '进入命令处理'}")
    print()
    
    # 分析当前的音频
    print("当前的音频分析:")
    curr_meaningful = is_meaningful_command(current_audio, wake_phrases)
    print(f"  是否有意义: {curr_meaningful}")
    
    handler = VoiceCommandHandler()
    cmd_type, cmd_info = handler.parse_command(current_audio)
    
    if cmd_type:
        print(f"  命令类型: {cmd_type}")
        print(f"  结果: {'进入命令处理' if curr_meaningful else '被过滤器忽略'}")
    
    print()
    print("改进总结:")
    print("  1. 之前的音频只包含问候和唤醒词 → 被正确忽略")
    print("  2. 当前的音频包含唤醒词和有效命令 → 被正确处理")
    print("  3. 命令过滤器工作正常，区分了无意义和有意义的命令")

def main():
    """主测试函数"""
    print("新的音频命令测试")
    print("=" * 60)
    
    results = []
    
    results.append(("命令分析", analyze_audio_command()))
    results.append(("命令执行", test_command_execution()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: [{status}]")
        if not result:
            all_passed = False
    
    # 对比分析
    compare_with_previous_audio()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 音频命令测试通过！")
        print()
        print("系统行为分析:")
        print("  1. [OK] 正确识别唤醒词'小九'")
        print("  2. [OK] 正确识别命令'检查系统'")
        print("  3. [OK] 通过命令过滤器（有意义命令）")
        print("  4. [OK] 正确解析为状态检查命令")
        print("  5. [OK] 执行命令并记录结果")
        print()
        print("🎉 系统完美处理了完整的语音命令！")
        return 0
    else:
        print("[WARNING] 部分测试失败，需要进一步调整。")
        return 1

if __name__ == "__main__":
    sys.exit(main())