import re
import unicodedata

def normalize_zh(s: str) -> str:
    s = unicodedata.normalize('NFC', s)
    s = re.sub(r'[\u200b-\u200f\u2060\ufeff]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# 测试实际识别文本
test_text = '你好 我 是 小九 今天 我们 测试 语音识别'
print('测试文本:', repr(test_text))
print('规范化后:', repr(normalize_zh(test_text)))
print()

# 检查包含关系
print('检查包含关系:')
print('  "小九" in 原始文本:', '小九' in test_text)
print('  "小九" in 规范化文本:', '小九' in normalize_zh(test_text))
print()

# 检查字符
print('检查字符:')
for i, char in enumerate(test_text):
    if i < 15:
        print(f'  {i:2}: {repr(char)} (U+{ord(char):04X})')

# 检查子字符串
print()
print('检查子字符串 text[7:9]:', repr(test_text[7:9]))
print('是否等于 "小九":', test_text[7:9] == '小九')

# 手动检查
print()
print('手动检查:')
search_text = '小九'
for i in range(len(test_text) - len(search_text) + 1):
    if test_text[i:i+len(search_text)] == search_text:
        print(f'  在位置 {i} 找到 "{search_text}"')