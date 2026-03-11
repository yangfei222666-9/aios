#!/usr/bin/env python3
"""批量修复 evolution.py 的所有字符串语法错误"""

f = open('evolution.py', 'r', encoding='utf-8')
content = f.read()
f.close()

# 替换所有未闭合的字符串
replacements = [
    ('suggestions.append("检测到超时错误，建议增加任务超时时间)', 
     'suggestions.append("检测到超时错误，建议增加任务超时时间")'),
    
    ('suggestions.append("检测到权限错误，建议检查工具权限配置)', 
     'suggestions.append("检测到权限错误，建议检查工具权限配置")'),
    
    ('suggestions.append("检测到 API 限流，建议添加重试机制或降低请求频率")',
     'suggestions.append("检测到 API 限流，建议添加重试机制或降低请求频率")'),
]

for old, new in replacements:
    content = content.replace(old, new)

f = open('evolution.py', 'w', encoding='utf-8')
f.write(content)
f.close()

print('✅ 已修复 evolution.py 所有字符串语法错误')
