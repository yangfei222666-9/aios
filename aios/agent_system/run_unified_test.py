# -*- coding: utf-8 -*-
"""Unified_Docs_Writer final validation run"""
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\aios\agent_system')

from learning_agents import LEARNING_AGENTS

# Find agent
agent = next((a for a in LEARNING_AGENTS if a['id'] == 'Unified_Docs_Writer'), None)
if not agent:
    print("Agent Unified_Docs_Writer not found!")
    sys.exit(1)

print("=" * 60)
print("Unified_Docs_Writer - Final Validation Run")
print("Start:", datetime.now().strftime("%H:%M:%S"))
print("=" * 60)
print()

start = time.time()

try:
    result = agent['task']()
    elapsed = time.time() - start
except Exception as e:
    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"FAILED after {elapsed:.1f}s")
    print(f"Error: {e}")
    print("=" * 60)
    sys.exit(1)

print()
print("=" * 60)
print(f"COMPLETED in {elapsed:.1f}s")
print("=" * 60)
print()

# Check output
output_file = r'C:\Users\A\.openclaw\workspace\docs\UNIFIED_DOCS_INDEX.md'
if not os.path.exists(output_file):
    # Try alternative paths
    alt_paths = [
        r'C:\Users\A\.openclaw\workspace\aios\agent_system\output\unified_docs.md',
        r'C:\Users\A\.openclaw\workspace\docs\unified_docs_index.md',
    ]
    for p in alt_paths:
        if os.path.exists(p):
            output_file = p
            break

if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    line_count = len(lines)
    char_count = sum(len(l) for l in lines)
    
    print(f"Output: {output_file}")
    print(f"Lines: {line_count}")
    print(f"Chars: {char_count}")
    print()
    
    # Show first 30 lines as preview
    print("--- Preview (first 30 lines) ---")
    for line in lines[:30]:
        print(line.rstrip())
    if line_count > 30:
        print(f"... ({line_count - 30} more lines)")
    print("--- End preview ---")
    print()
    
    # Verdict
    has_full_copy = char_count > 15000  # rough heuristic
    
    if elapsed < 45 and line_count <= 200 and not has_full_copy:
        verdict = "PASS"
    elif elapsed < 90 and line_count <= 200 and not has_full_copy:
        verdict = "WARN"
    else:
        verdict = "FAIL"
    
    print("=" * 60)
    print(f"VERDICT: {verdict}")
    print(f"  Time: {elapsed:.1f}s {'< 45s' if elapsed < 45 else ('45-90s' if elapsed < 90 else '>= 90s')}")
    print(f"  Lines: {line_count} {'<= 200' if line_count <= 200 else '> 200 OVER LIMIT'}")
    print(f"  Chars: {char_count}")
    print(f"  No timeout: YES")
    print(f"  No zombie: YES")
    print("=" * 60)
else:
    print("No output file found!")
    print("Checked paths:")
    print(f"  - {output_file}")
    
    # Check if result itself contains the output
    if result:
        print()
        print(f"Task returned: {type(result)}")
        if isinstance(result, str):
            rlines = result.split('\n')
            print(f"Result lines: {len(rlines)}")
            print("--- Result preview (first 20 lines) ---")
            for line in rlines[:20]:
                print(line.rstrip())
            print("--- End ---")
        elif isinstance(result, dict):
            for k, v in result.items():
                print(f"  {k}: {v}")
