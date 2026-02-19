#!/usr/bin/env python3
"""
Unicode 清理集成测试
验证清理工具在完整系统中的效果
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, '.')

def test_unicode_cleaner():
    """测试 Unicode 清理工具"""
    print("Unicode 清理工具测试")
    print("=" * 60)
    
    from tools.unicode_sanitizer import (
        sanitize_unicode,
        normalize_zh,
        clean_asr_text
    )
    
    # 测试各种 Unicode 问题
    test_cases = [
        # ASR 常见问题
        ("小九\u200b检查\u200b系统", "小九 检查 系统", "零宽空格"),
        ("你好　世界", "你好 世界", "全角空格"),
        ("测试\x00文本", "测试 文本", "控制字符"),
        ("Ｈｅｌｌｏ　Ｗｏｒｌｄ", "Hello World", "全角字母"),
        ("测试，。！？", "测试，。！？", "中文标点"),
        ("\ufeff开始文本", "开始文本", "BOM 字符"),
        ("测试[背景音]完成", "测试完成", "ASR 标记"),
        ("说话啊啊啊结束", "说话啊结束", "重复字符"),
        
        # 实际音频识别结果
        ("小九 检查 系统 状态", "小九 检查 系统 状态", "正常命令"),
        ("添加笔记：明天开会", "添加笔记:明天开会", "带冒号命令"),
        ("现在　几点？", "现在 几点?", "全角空格和问号"),
    ]
    
    all_passed = True
    
    for input_text, expected, description in test_cases:
        # 测试 clean_asr_text（主要函数）
        cleaned = clean_asr_text(input_text)
        
        if cleaned == expected:
            status = "[PASS]"
            passed = True
        else:
            status = "[FAIL]"
            passed = False
            all_passed = False
        
        print(f"{status} {description}")
        print(f"   输入: {repr(input_text)}")
        print(f"   输出: {repr(cleaned)}")
        print(f"   期望: {repr(expected)}")
        
        # 同时测试其他函数
        sanitized = sanitize_unicode(input_text)
        normalized = normalize_zh(input_text)
        print(f"   sanitize_unicode: {repr(sanitized)}")
        print(f"   normalize_zh: {repr(normalized)}")
        print()
    
    return all_passed

def test_system_integration():
    """测试系统集成"""
    print("\n系统集成测试")
    print("=" * 60)
    
    # 创建测试环境
    test_dir = tempfile.mkdtemp(prefix="unicode_test_")
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    try:
        # 创建必要的目录
        os.makedirs("notes", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        print(f"测试目录: {test_dir}")
        print()
        
        # 测试语音唤醒系统的文本规范化
        print("1. 测试语音唤醒系统文本规范化")
        
        # 导入并测试 normalize_zh 函数
        import sys
        sys.path.insert(0, original_dir)
        
        from tools.wake_listener import normalize_zh, match_wake
        
        test_texts = [
            ("小九\u200b检查系统", "小九检查系统", "清理零宽字符"),
            ("你好　小九", "你好 小九", "清理全角空格"),
            ("\ufeff小酒测试", "小酒测试", "清理BOM"),
        ]
        
        integration_passed = True
        
        for input_text, expected_clean, description in test_texts:
            cleaned = normalize_zh(input_text)
            
            if cleaned == expected_clean:
                status = "[PASS]"
            else:
                status = "[FAIL]"
                integration_passed = False
            
            print(f"{status} {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   清理: {repr(cleaned)}")
            print(f"   期望: {repr(expected_clean)}")
            print()
        
        # 测试唤醒词匹配
        print("2. 测试唤醒词匹配（带Unicode清理）")
        
        wake_phrases = ["小九", "你好小九", "小酒"]
        
        match_tests = [
            ("小九\u200b", True, "带零宽字符的唤醒词"),
            ("你好　小九", True, "带全角空格的唤醒词"),
            ("\ufeff小酒", True, "带BOM的唤醒词"),
            ("小九检查系统", True, "唤醒词+命令"),
            ("未知命令", False, "非唤醒词"),
        ]
        
        for text, should_match, description in match_tests:
            matches = match_wake(text, wake_phrases)
            
            if matches == should_match:
                status = "[PASS]"
            else:
                status = "[FAIL]"
                integration_passed = False
            
            print(f"{status} {description}")
            print(f"   文本: {repr(text)}")
            print(f"   匹配: {matches} (期望: {should_match})")
            print()
        
        # 测试命令路由器
        print("3. 测试命令路由器（带Unicode清理）")
        
        from tools.command_router import CommandRouter
        
        router = CommandRouter(test_dir)
        
        command_tests = [
            ("小九\u200b检查系统", "RUN_DAILY_CHECK", "带零宽字符的命令"),
            ("添加笔记\u200b：测试", "ADD_NOTE", "带零宽字符的笔记"),
            ("现在　几点？", "TELL_TIME", "带全角空格的查询"),
        ]
        
        for text, expected_action, description in command_tests:
            action, payload = router.route_command(text)
            
            if action == expected_action:
                status = "[PASS]"
            else:
                status = "[FAIL]"
                integration_passed = False
            
            print(f"{status} {description}")
            print(f"   命令: {repr(text)}")
            print(f"   动作: {action} (期望: {expected_action})")
            print()
        
        return integration_passed
        
    finally:
        # 恢复原始目录
        os.chdir(original_dir)
        
        # 清理测试目录
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"已清理测试目录: {test_dir}")
        except:
            pass

def main():
    """主测试函数"""
    print("Unicode 清理集成验证")
    print("=" * 60)
    
    print("系统改进: 增强的 Unicode 清理功能")
    print("解决 ASR 文本中的编码问题:")
    print("  1. 零宽字符 (\\u200b, \\ufeff 等)")
    print("  2. 全角/半角转换")
    print("  3. 控制字符清理")
    print("  4. ASR 特定标记移除")
    print("  5. 文本规范化")
    print()
    
    # 运行测试
    cleaner_passed = test_unicode_cleaner()
    integration_passed = test_system_integration()
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = cleaner_passed and integration_passed
    
    if all_passed:
        print("[SUCCESS] 所有 Unicode 清理测试通过！")
        print()
        print("🎉 Unicode 清理功能已成功集成！")
        print()
        print("系统现在能够处理:")
        print("  1. [OK] 零宽字符和 BOM")
        print("  2. [OK] 全角/半角转换")
        print("  3. [OK] 控制字符清理")
        print("  4. [OK] ASR 特定标记")
        print("  5. [OK] 文本规范化")
        print("  6. [OK] 系统集成")
        print()
        print("用户体验提升:")
        print("  • 更准确的语音识别文本处理")
        print("  • 更可靠的命令解析")
        print("  • 更好的编码兼容性")
        print("  • 更稳定的系统运行")
        return 0
    else:
        print("[FAILED] 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())