#!/usr/bin/env python3
"""
测试音频识别结果
"""

import sys
sys.path.insert(0, '.')

from tools.wake_listener import match_wake

def test_audio_result():
    """测试音频识别结果"""
    # 音频识别结果
    audio_text = "你好 小九 噢"
    
    # 唤醒词列表
    wake_phrases = ["小九", "你好小九", "小酒", "hi 小九", "hey 小九"]
    
    print("音频识别结果分析")
    print("=" * 60)
    print(f"识别文本: '{audio_text}'")
    print(f"唤醒词列表: {wake_phrases}")
    print()
    
    # 测试唤醒词匹配
    result = match_wake(audio_text, wake_phrases)
    
    print("唤醒词匹配测试:")
    print(f"  结果: {result}")
    
    if result:
        print("  [OK] 触发唤醒！")
        
        # 分析具体匹配
        normalized_text = audio_text.replace(" ", "")
        print(f"  规范化文本: '{normalized_text}'")
        
        for phrase in wake_phrases:
            normalized_phrase = phrase.replace(" ", "")
            if normalized_phrase in normalized_text:
                print(f"  匹配到唤醒词: '{phrase}'")
    else:
        print("  ❌ 未触发唤醒")
    
    print()
    
    # 测试其他可能的变体
    print("其他可能变体测试:")
    variants = [
        "你好小九噢",
        "你好小九",
        "小九噢",
        "小九",
        "小酒噢",
        "小酒",
    ]
    
    for variant in variants:
        variant_result = match_wake(variant, wake_phrases)
        status = "[OK]" if variant_result else "[NO]"
        print(f"  {status} '{variant}' -> {variant_result}")
    
    print()
    
    # 分析音频内容
    print("音频内容分析:")
    words = audio_text.split()
    print(f"  分词结果: {words}")
    
    if "小九" in words or "小酒" in words:
        print("  [OK] 包含唤醒词")
    if "你好" in words:
        print("  [OK] 包含问候语")
    
    return result

def main():
    """主函数"""
    result = test_audio_result()
    
    print("=" * 60)
    if result:
        print("结论: 音频成功触发了语音唤醒！")
        print("系统应该已经进入命令模式，等待后续指令。")
    else:
        print("结论: 音频未触发唤醒。")
        print("可能原因: 唤醒词不匹配或音频质量问题。")
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())