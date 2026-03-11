#!/usr/bin/env python3
"""直接用行号修复 evolution.py"""

f = open('evolution.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()

# 修复第 164, 167, 170 行（索引 163, 166, 169）
lines[163] = '            suggestions.append("检测到超时错误，建议增加任务超时时间")\n'
lines[166] = '            suggestions.append("检测到权限错误，建议检查工具权限配置")\n'
lines[169] = '            suggestions.append("检测到 API 限流，建议添加重试机制或降低请求频率")\n'

f = open('evolution.py', 'w', encoding='utf-8')
f.writelines(lines)
f.close()

print('✅ 已修复 evolution.py 第 164, 167, 170 行')
