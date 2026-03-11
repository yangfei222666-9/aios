#!/usr/bin/env python3
"""修复 evolution.py 第 248 行的 docstring"""

f = open('evolution.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()

# 修复第 248 行（索引 247）
lines[247] = '        """获取 Agent 的进化历史"""\n'

f = open('evolution.py', 'w', encoding='utf-8')
f.writelines(lines)
f.close()

print('✅ 已修复 evolution.py 第 248 行的 docstring')
