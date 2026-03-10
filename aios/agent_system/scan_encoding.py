import ast
import sys

with open('low_success_regeneration.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all lines with replacement character (encoding corruption)
lines = content.split('\n')
bad_lines = []
for i, line in enumerate(lines, 1):
    if '\ufffd' in line or '\ue511' in line or '\ue594' in line:
        bad_lines.append((i, line.strip()[:80]))

print(f"Total lines with encoding issues: {len(bad_lines)}")
for lineno, text in bad_lines[:30]:
    print(f"  Line {lineno}: {repr(text)}")
