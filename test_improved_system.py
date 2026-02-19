#!/usr/bin/env python3
"""
测试改进后的语音唤醒系统
验证命令过滤器功能
"""

import sys
sys.path.insert(0, '.')

from tools.wake_listener import is_meaningful_command

def test_improved_filter():
    """测试改进后的命令过滤器"""
    wake_phrases = ["小九", "你好小九", "小酒", "hi 小九", "hey 小九"]
    
    print("改进后的命令过滤器测试")
    print("=" * 60)
    print(f"唤醒词: {wake_phrases}")
    print()
    
    # 测试案例：基于之前的音频识别结果
    test_cases = [
        # 之前的音频识别结果
        ("你好 小九 噢", False, "寒暄+唤醒词+语气词 - 应忽略"),
        
        # 其他应该忽略的情况
        ("小九", False, "纯唤醒词"),
        ("小酒", False, "同音唤醒词"),
        ("你好", False, "纯寒暄"),
        ("hi", False, "英文寒暄"),
        ("喂", False, "单字寒暄"),
        ("小九你好", False, "唤醒词+寒暄"),
        ("你好小九", False, "寒暄+唤醒词"),
        ("小九好", False, "唤醒词+单字"),
        ("嗯", False, "语气词"),
        
        # 应该接受的情况
        ("小九检查系统状态", True, "唤醒词+有效命令"),
        ("检查系统状态", True, "有效命令"),
        ("添加笔记测试语音", True, "有效命令"),
        ("今天天气怎么样", True, "疑问句"),
        ("播放音乐", True, "动作命令"),
        ("小九告诉我时间", True, "唤醒词+完整命令"),
        ("搜索人工智能资料", True, "搜索命令"),
    ]
    
    all_passed = True
    
    for cmd, expected, description in test_cases:
        result = is_meaningful_command(cmd, wake_phrases)
        passed = result == expected
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {description}")
        print(f"  命令: '{cmd}'")
        print(f"  期望: {expected}, 实际: {result}")
        print()
        
        if not passed:
            all_passed = False
    
    # 特别测试：之前的音频内容
    print("特别测试 - 之前的音频识别结果:")
    audio_result = "你好 小九 噢"
    result = is_meaningful_command(audio_result, wake_phrases)
    
    print(f"音频内容: '{audio_result}'")
    print(f"过滤结果: {result}")
    
    if not result:
        print("✅ 正确过滤：无意义命令被忽略")
    else:
        print("❌ 错误：应该被过滤")
        all_passed = False
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("[SUCCESS] 所有测试通过！命令过滤器工作正常。")
        return 0
    else:
        print("[WARNING] 有测试失败，需要调整过滤器规则。")
        return 1

def analyze_audio_result():
    """分析之前的音频识别结果"""
    print("\n音频识别结果分析")
    print("=" * 60)
    
    audio_text = "你好 小九 噢"
    wake_phrases = ["小九", "你好小九", "小酒"]
    
    print(f"原始音频识别: '{audio_text}'")
    print(f"唤醒词列表: {wake_phrases}")
    print()
    
    # 分析各个部分
    parts = audio_text.split()
    print("分词分析:")
    for i, part in enumerate(parts, 1):
        print(f"  {i}. '{part}'")
    
    print()
    print("语义分析:")
    
    # 检查各部分
    has_greeting = any(part in ["你好", "嗨", "hello", "hi"] for part in parts)
    has_wake_word = any(part in ["小九", "小酒"] for part in parts)
    has_meaningful = len(audio_text.replace(" ", "")) > 3
    
    print(f"  包含问候语: {has_greeting}")
    print(f"  包含唤醒词: {has_wake_word}")
    print(f"  有实际内容: {has_meaningful}")
    
    # 应用过滤器
    result = is_meaningful_command(audio_text, wake_phrases)
    
    print()
    print("过滤器判断:")
    print(f"  是否有意义: {result}")
    
    if not result:
        print("  [OK] 正确：这是一个无意义的命令，应该被忽略")
        print("  原因: 只包含问候语和唤醒词，没有实际指令")
    else:
        print("  [NO] 错误：应该被识别为无意义命令")
    
    return 0 if not result else 1

def main():
    """主函数"""
    print("改进后的语音唤醒系统测试")
    print("=" * 60)
    
    results = []
    
    results.append(("命令过滤器", test_improved_filter()))
    results.append(("音频分析", analyze_audio_result()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result == 0 else "FAIL"
        print(f"{test_name}: [{status}]")
        if result != 0:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！系统改进成功。")
        print()
        print("改进总结:")
        print("1. [OK] 命令过滤器已集成")
        print("2. [OK] 无意义命令会被正确忽略")
        print("3. [OK] 之前的音频内容 '你好 小九 噢' 会被过滤")
        print("4. [OK] 有效命令会被正常处理")
        return 0
    else:
        print("⚠️  部分测试失败，需要进一步调整。")
        return 1

if __name__ == "__main__":
    sys.exit(main())