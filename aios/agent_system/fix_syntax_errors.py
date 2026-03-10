#!/usr/bin/env python3
"""
Fix specific syntax errors in the 3 files
"""
import re

# Fix daily_metrics.py line 37
with open('daily_metrics.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix unterminated string
content = content.replace('"bad_plan": "计划不合�?,', '"bad_plan": "bad_plan",')

with open('daily_metrics.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("[OK] Fixed daily_metrics.py")

# Fix experience_engine.py - remove corrupted comments with ?
with open('experience_engine.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    # Remove lines that are just corrupted comments
    if line.strip().startswith('#') and '?' in line and len(line.strip()) < 10:
        continue
    fixed_lines.append(line)

with open('experience_engine.py', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(fixed_lines)
print("[OK] Fixed experience_engine.py")

# Fix learnings_extractor.py - fix docstring
with open('learnings_extractor.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix corrupted docstring
content = re.sub(r'"""鎻愮偧榛勯噾娉曞垯"""', '"""Extract golden rules"""', content)
content = re.sub(r'"""鐢熸垚 golden_rules\.md"""', '"""Generate golden_rules.md"""', content)
content = re.sub(r'#\s+\(Golden Rules\)', '# Golden Rules', content)

with open('learnings_extractor.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("[OK] Fixed learnings_extractor.py")
