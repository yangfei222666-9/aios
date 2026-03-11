#!/usr/bin/env python3
"""修复 evolution.py 的 f-string 语法错误"""

f = open('evolution.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()

# 修复第 144 行（索引 143）
lines[143] = '                suggestions.append(f"{task_type} 任务失败 {data[\'count\']} 次，建议：")\n'
lines[146] = '                    suggestions.append("  - 添加 \'coding-agent\' 技能")\n'
lines[147] = '                    suggestions.append("  - 确保 \'exec\', \'read\', \'write\', \'edit\' 工具权限")\n'
lines[150] = '                    suggestions.append("  - 添加数据分析相关技能")\n'
lines[151] = '                    suggestions.append("  - 确保 \'web_search\', \'web_fetch\' 工具权限")\n'
lines[154] = '                    suggestions.append("  - 添加 \'system-resource-monitor\' 技能")\n'
lines[155] = '                    suggestions.append("  - 确保 \'exec\' 工具权限")\n'

f = open('evolution.py', 'w', encoding='utf-8')
f.writelines(lines)
f.close()

print('✅ 已修复 evolution.py 语法错误')
