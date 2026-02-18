#!/usr/bin/env python3
"""
Unicode 清理工具
处理语音识别文本中的编码问题
"""

import unicodedata
import re
from typing import Optional

def sanitize_unicode(s: str) -> str:
    """
    清理 Unicode 字符串
    
    参数:
        s: 输入字符串
    
    返回:
        清理后的字符串
    """
    if not s:
        return ""
    
    # 统一正规化（中文/全角/兼容字符）
    s = unicodedata.normalize("NFKC", s)
    
    cleaned = []
    for ch in s:
        o = ord(ch)
        
        # 1) 去代理项（理论上不该出现在正常 str；但有时外部库/解码会带进来）
        if 0xD800 <= o <= 0xDFFF:
            continue
        
        # 2) 去零宽/BOM/方向控制等"格式控制符"(Cf)，常见于复制/编码混入
        cat = unicodedata.category(ch)
        if cat == "Cf":
            # 但保留一些可能有用的格式字符
            if ch in ('\u00AD',):  # 软连字符
                cleaned.append(ch)
            else:
                # 其他格式控制符替换为空格
                cleaned.append(" ")
            continue
        
        # 3) 去控制字符(Cc)，保留换行/制表符/回车
        if cat == "Cc":
            if ch in ("\n", "\t", "\r", " "):
                cleaned.append(ch)
            else:
                # 其他控制字符替换为空格
                cleaned.append(" ")
            continue
        
        cleaned.append(ch)
    
    # 4) 收尾：压缩空白 + strip
    s2 = "".join(cleaned)
    s2 = re.sub(r'\s+', ' ', s2.strip())
    
    return s2

def normalize_zh(s: str) -> str:
    """
    中文文本规范化
    
    参数:
        s: 输入字符串
    
    返回:
        规范化后的字符串
    """
    if not s:
        return ""
    
    # 1. Unicode 清理
    s = sanitize_unicode(s)
    
    # 2. 全角转半角（保留中文标点）
    s = _fullwidth_to_halfwidth(s)
    
    # 3. 规范化标点符号
    s = _normalize_punctuation(s)
    
    # 4. 压缩连续空格
    s = re.sub(r'\s+', ' ', s)
    
    return s.strip()

def _fullwidth_to_halfwidth(s: str) -> str:
    """全角转半角（保留中文标点）"""
    result = []
    
    # 中文标点（保留全角）
    chinese_punctuation = {
        '，', '。', '！', '？', '；', '：', '「', '」', '『', '』',
        '（', '）', '【', '】', '《', '》', '、', '～', '—', '…'
    }
    
    for ch in s:
        o = ord(ch)
        
        # 保留中文标点
        if ch in chinese_punctuation:
            result.append(ch)
            continue
        
        # 全角字母、数字、英文标点转半角
        if 0xFF01 <= o <= 0xFF5E:  # 全角字符范围
            result.append(chr(o - 0xFEE0))
        else:
            result.append(ch)
    
    return "".join(result)

def _normalize_punctuation(s: str) -> str:
    """规范化标点符号"""
    # 替换多种引号为标准引号
    replacements = {
        '＂': '"',  # 全角双引号
        '＇': "'",  # 全角单引号
        '＂': '"',  # 全角双引号
        '｀': "'",  # 全角反引号
        '﹃': '"',  # 竖排双引号
        '﹄': '"',  # 竖排双引号
        '﹁': '"',  # 竖排单引号
        '﹂': '"',  # 竖排单引号
    }
    
    for old, new in replacements.items():
        s = s.replace(old, new)
    
    return s

def clean_asr_text(text: str) -> str:
    """
    清理 ASR 识别文本
    
    参数:
        text: ASR 识别结果
    
    返回:
        清理后的文本
    """
    if not text:
        return ""
    
    # 1. 基础清理
    text = sanitize_unicode(text)
    
    # 2. 中文规范化
    text = normalize_zh(text)
    
    # 3. 移除常见 ASR 错误
    text = _remove_asr_artifacts(text)
    
    # 4. 标准化空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def _remove_asr_artifacts(text: str) -> str:
    """移除 ASR 常见错误"""
    # 移除常见的无意义字符
    artifacts = [
        r'\[.*?\]',      # 方括号内容
        r'\(.*?\)',      # 括号内容（如果只是噪音）
        r'<.*?>',        # 尖括号内容
        r'\*',           # 星号
        r'#',            # 井号
        r'~',            # 波浪号
        r'`',            # 反引号
    ]
    
    for pattern in artifacts:
        text = re.sub(pattern, '', text)
    
    # 移除连续重复字符（如"啊啊啊" -> "啊"）
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    return text

def test_sanitizer():
    """测试清理函数"""
    print("Unicode 清理工具测试")
    print("=" * 60)
    
    test_cases = [
        # (输入, 期望输出, 描述)
        ("你好　世界", "你好 世界", "全角空格转半角"),
        ("hello\u200bworld", "hello world", "零宽空格"),
        ("测试\x00文本", "测试 文本", "控制字符"),
        ("Ｈｅｌｌｏ　Ｗｏｒｌｄ", "Hello World", "全角字母转半角"),
        ("测试，。！？", "测试，。！？", "保留中文标点"),
        ("测试  \t  文本", "测试 文本", "压缩空白"),
        ("\ufeff测试文本", "测试文本", "移除 BOM"),
        ("测试啊啊啊文本", "测试啊文本", "移除连续重复"),
        ("测试[背景音]文本", "测试文本", "移除方括号内容"),
    ]
    
    all_passed = True
    
    for input_text, expected, description in test_cases:
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
        print()
    
    # 测试实际 ASR 文本
    print("实际 ASR 文本测试:")
    print("-" * 40)
    
    asr_samples = [
        "小九　检查　系统　状态",
        "你好\u200b小九\u200b噢",
        "添加笔记：明天开会",
        "现在　几点　？",
    ]
    
    for sample in asr_samples:
        cleaned = clean_asr_text(sample)
        print(f"原始: {repr(sample)}")
        print(f"清理: {repr(cleaned)}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] 所有清理测试通过！")
    else:
        print("[FAILED] 部分测试失败")
    
    return all_passed

if __name__ == "__main__":
    success = test_sanitizer()
    exit(0 if success else 1)