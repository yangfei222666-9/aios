#!/usr/bin/env python3
"""检查 evolution.py 的三引号配对"""

f = open('evolution.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()

triple_quote_lines = []
for i, line in enumerate(lines, 1):
    if '"""' in line:
        count = line.count('"""')
        triple_quote_lines.append((i, count, line.strip()[:80]))

print("所有包含三引号的行：")
for line_num, count, content in triple_quote_lines:
    print(f"第 {line_num} 行（{count} 个）: {content}")

# 检查配对
total = sum(count for _, count, _ in triple_quote_lines)
print(f"\n总共 {total} 个三引号")
if total % 2 != 0:
    print("⚠️  三引号数量不是偶数，存在未闭合的 docstring")
