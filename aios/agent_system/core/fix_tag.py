#!/usr/bin/env python3
# -*- coding: utf-8 -*-
with open('task_executor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 442 (index 441)
lines[441] = '        tag = "OK" if success else "FAIL"\n'

with open('task_executor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed line 442")
