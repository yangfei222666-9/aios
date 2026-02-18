#!/usr/bin/env python3
"""
文本规范化工具
用于处理中文文本的Unicode标准化、零宽字符移除等
"""

import re
import unicodedata

def normalize_zh(s: str) -> str:
    """
    中文文本规范化
    
    功能:
    1. Unicode NFC 规范化
    2. 移除零宽字符 (\\u200b-\\u200f, \\u2060, \\ufeff)
    3. 标准化空白字符（多个空白 → 单个空格）
    
    参数:
        s: 输入字符串
        
    返回:
        规范化后的字符串
    """
    if not isinstance(s, str):
        return s
    
    # 1. Unicode 规范化 (NFC)
    s = unicodedata.normalize("NFC", s)
    
    # 2. 移除零宽字符
    # \\u200b: 零宽空格, \\u200c: 零宽非连接符, \\u200d: 零宽连接符
    # \\u200e: 左至右标记, \\u200f: 右至左标记
    # \\u2060: 词连接符, \\ufeff: 字节顺序标记
    s = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", s)
    
    # 3. 标准化空白字符
    s = re.sub(r"\s+", " ", s).strip()
    
    return s

def normalize_for_asr(s: str) -> str:
    """
    ASR 专用文本规范化
    
    在基础规范化的基础上，移除标点符号，适合ASR结果处理
    """
    s = normalize_zh(s)
    
    # 移除常见标点（ASR通常不输出标点，但以防万一）
    s = re.sub(r"[,.!?;:，。！？；：]", " ", s)
    
    # 再次标准化空白
    s = re.sub(r"\s+", " ", s).strip()
    
    return s

def normalize_for_comparison(s: str) -> str:
    """
    比较专用规范化
    
    用于字符串比较，移除所有空白和标点
    """
    s = normalize_zh(s)
    
    # 移除所有非字母数字和中文字符
    # 保留中文、英文、数字
    s = re.sub(r"[^\w\u4e00-\u9fff]", "", s, flags=re.UNICODE)
    
    return s

def test_normalization():
    """测试函数"""
    test_cases = [
        ("你好 世界", "你好 世界"),  # 普通文本
        ("你好\u200b世界", "你好世界"),  # 包含零宽空格
        ("你好  \t  世界", "你好 世界"),  # 多个空白
        ("café", "café"),  # Unicode 字符
    ]
    
    print("测试文本规范化:")
    for input_str, expected in test_cases:
        result = normalize_zh(input_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} 输入: {repr(input_str)}")
        print(f"   期望: {repr(expected)}")
        print(f"   结果: {repr(result)}")
        print()

if __name__ == "__main__":
    test_normalization()