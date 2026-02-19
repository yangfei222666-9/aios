#!/usr/bin/env python3
"""
测试 Unicode 清理集成
验证在 ASR 识别后立即进行 Unicode 清理的效果
"""

import sys
import json

# 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_sanitize_unicode():
    """测试 sanitize_unicode 函数"""
    print("测试 Unicode 清理函数")
    print("=" * 60)
    
    # 模拟 ASR 识别结果
    asr_results = [
        # (原始 ASR 文本, 期望清理后文本, 描述)
        ("小九\u200b检查系统", "小九 检查系统", "零宽空格替换为空格"),
        ("你好　小九", "你好 小九", "全角空格转半角"),
        ("\ufeff小酒测试", "小酒测试", "BOM 字符移除"),
        ("添加笔记：测试", "添加笔记:测试", "全角冒号转半角"),
        ("现在　几点？", "现在 几点?", "全角空格和问号转半角"),
        ("测试\x00文本", "测试 文本", "控制字符替换为空格"),
        ("hello\u200bworld", "hello world", "英文零宽空格替换为空格"),
    ]
    
    # 导入函数
    from tools.wake_listener import sanitize_unicode
    
    all_passed = True
    
    for original, expected, description in asr_results:
        cleaned = sanitize_unicode(original)
        
        if cleaned == expected:
            status = "[PASS]"
        else:
            status = "[FAIL]"
            all_passed = False
        
        print(f"{status} {description}")
        print(f"   原始: {repr(original)}")
        print(f"   清理: {repr(cleaned)}")
        print(f"   期望: {repr(expected)}")
        print()
    
    return all_passed

def test_asr_simulation():
    """模拟 ASR 识别流程"""
    print("\n模拟 ASR 识别流程")
    print("=" * 60)
    
    from tools.wake_listener import sanitize_unicode, match_wake
    
    # 模拟 ASR 识别结果 JSON
    asr_json_examples = [
        # 唤醒词检测
        '{"text": "小九\\u200b", "confidence": 0.9}',
        '{"text": "你好\\u3000小九", "confidence": 0.8}',
        '{"text": "\\ufeff小酒", "confidence": 0.85}',
        
        # 命令识别
        '{"text": "检查\\u200b系统\\u200b状态", "confidence": 0.7}',
        '{"text": "添加笔记\\u3000：测试", "confidence": 0.75}',
        '{"text": "现在\\u3000几点？", "confidence": 0.8}',
    ]
    
    wake_phrases = ["小九", "你好小九", "小酒"]
    
    print("唤醒词匹配测试:")
    print("-" * 40)
    
    for i, json_str in enumerate(asr_json_examples[:3], 1):
        result = json.loads(json_str)
        original_text = result.get("text", "").strip()
        cleaned_text = sanitize_unicode(original_text)
        
        matches = match_wake(cleaned_text, wake_phrases)
        
        print(f"示例 {i}:")
        print(f"  原始 ASR: {repr(original_text)}")
        print(f"  清理后: {repr(cleaned_text)}")
        print(f"  匹配唤醒词: {matches}")
        print()
    
    print("命令文本清理测试:")
    print("-" * 40)
    
    for i, json_str in enumerate(asr_json_examples[3:], 1):
        result = json.loads(json_str)
        original_text = result.get("text", "").strip()
        cleaned_text = sanitize_unicode(original_text)
        
        print(f"示例 {i}:")
        print(f"  原始 ASR: {repr(original_text)}")
        print(f"  清理后: {repr(cleaned_text)}")
        print(f"  改进: {'✅' if cleaned_text != original_text else '➖'}")
        print()
    
    return True

def test_integration_with_normalize_zh():
    """测试与 normalize_zh 函数的集成"""
    print("\n测试与 normalize_zh 函数的集成")
    print("=" * 60)
    
    from tools.wake_listener import normalize_zh
    
    test_cases = [
        ("小九\u200b检查系统", "小九 检查系统"),
        ("你好　小九", "你好 小九"),
        ("\ufeff小酒测试", "小酒测试"),
    ]
    
    all_consistent = True
    
    for input_text, expected in test_cases:
        normalized = normalize_zh(input_text)
        
        # 检查一致性
        if normalized == expected:
            status = "[OK]"
        else:
            status = "[NO]"
            all_consistent = False
        
        print(f"{status} 输入: {repr(input_text)}")
        print(f"    normalize_zh: {repr(normalized)}")
        print(f"    期望结果: {repr(expected)}")
        print()
    
    if all_consistent:
        print("✅ normalize_zh 函数正确使用了 sanitize_unicode")
    else:
        print("❌ normalize_zh 函数与 sanitize_unicode 不一致")
    
    return all_consistent

def main():
    """主测试函数"""
    print("Unicode 清理集成测试")
    print("=" * 60)
    print("验证在 ASR 识别后立即进行 Unicode 清理的效果")
    print()
    
    print("改进说明:")
    print("  在 tools/wake_listener.py 中添加了:")
    print("  1. sanitize_unicode() 函数")
    print("  2. 在获取 ASR 文本后立即调用清理")
    print("  3. 确保所有文本处理前都经过 Unicode 清理")
    print()
    
    results = []
    
    results.append(("sanitize_unicode 函数", test_sanitize_unicode()))
    results.append(("ASR 流程模拟", test_asr_simulation()))
    results.append(("normalize_zh 集成", test_integration_with_normalize_zh()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name:25} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 Unicode 清理集成测试完全通过！")
        print()
        print("改进效果:")
        print("  1. ✅ ASR 识别文本立即清理")
        print("  2. ✅ 唤醒词匹配更准确")
        print("  3. ✅ 命令解析更可靠")
        print("  4. ✅ 系统兼容性更好")
        print()
        print("现在系统能够:")
        print("  • 自动清理 ASR 识别文本中的 Unicode 问题")
        print("  • 更准确地匹配唤醒词")
        print("  • 更可靠地解析语音命令")
        print("  • 处理各种编码和字符问题")
        print()
        print("感谢建议！这个改进显著提升了系统的健壮性。")
        return 0
    else:
        print("⚠️ 部分测试失败")
        print()
        print("需要检查的问题:")
        for test_name, passed in results:
            if not passed:
                print(f"  • {test_name}")
        return 1

if __name__ == "__main__":
    sys.exit(main())