#!/usr/bin/env python3
"""扫描所有 learner_*.py 文件的 f-string 问题"""
import re
from pathlib import Path

base_dir = Path(__file__).parent
learner_files = list(base_dir.glob("learner_*.py"))

print("扫描 f-string 问题...\n")

all_issues = {}

for filepath in learner_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    issues = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        # 检测未闭合的 f-string
        if 'print(f"' in stripped and not stripped.endswith('")'):
            issues.append((i, stripped))
    
    if issues:
        all_issues[filepath.name] = issues
        print(f"📄 {filepath.name}:")
        for line_num, line_content in issues:
            print(f"   L{line_num}: {line_content[:80]}...")
        print()

if not all_issues:
    print("✅ 没有发现 f-string 问题")
else:
    print(f"\n总计: {sum(len(v) for v in all_issues.values())} 个问题")
