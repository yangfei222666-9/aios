#!/usr/bin/env python3
"""Fix syntax errors by line number"""

# Fix daily_metrics.py line 37
with open('daily_metrics.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Line 37 (index 36) - fix unterminated string
line = lines[36]
print(f"[daily_metrics] Line 37 raw: {repr(line)}")
# Replace the whole line with a clean version
lines[36] = '    "bad_plan": "bad_plan",\n'
with open('daily_metrics.py', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(lines)
print("[OK] Fixed daily_metrics.py line 37")

# Fix experience_engine.py line 44
with open('experience_engine.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"[experience_engine] Line 44 raw: {repr(lines[43])}")
print(f"[experience_engine] Line 43 raw: {repr(lines[42])}")
# Remove lines that are just corrupted comment + code merged
# Find lines with pattern: "# <garbage>?<whitespace>if/for/etc"
fixed = []
i = 0
while i < len(lines):
    line = lines[i]
    # Detect corrupted comment lines that swallowed the next line
    if line.strip().startswith('#') and '?' in line:
        # Check if there's code after the ?
        parts = line.split('?', 1)
        if len(parts) > 1 and parts[1].strip():
            # There's code after the ?, split it
            comment_part = parts[0] + '\n'
            code_part = '    ' + parts[1].strip() + '\n'
            fixed.append(comment_part)
            fixed.append(code_part)
            print(f"  Split line {i+1}: {repr(line.rstrip())} -> comment + {repr(code_part.rstrip())}")
        else:
            fixed.append(line)
    else:
        fixed.append(line)
    i += 1

with open('experience_engine.py', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(fixed)
print("[OK] Fixed experience_engine.py")

# Fix learnings_extractor.py line 154
with open('learnings_extractor.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"[learnings_extractor] Line 154 raw: {repr(lines[153])}")
print(f"[learnings_extractor] Line 153 raw: {repr(lines[152])}")
# Fix corrupted docstring - line 154 has """Extract golden rules""" but line 153 has def
# The issue is the docstring is on the same line as def or has wrong indentation
# Check context
for idx in range(150, 158):
    print(f"  Line {idx+1}: {repr(lines[idx])}")
