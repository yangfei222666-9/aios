#!/usr/bin/env python3
"""Find all lines with garbled Chinese in learner_agent.py"""
import re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = r'C:\Users\A\.openclaw\workspace\aios\agent_system\learner_agent.py'

with open(path, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

garbled_re = re.compile(r'[\u4e00-\u9fff\ue000-\uffff]{2,}')

for i, line in enumerate(lines, 1):
    stripped = line.rstrip()
    if garbled_re.search(stripped):
        print(f"LINE {i}: {stripped}")
