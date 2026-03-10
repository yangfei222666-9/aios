#!/usr/bin/env python3
"""Restore files from git HEAD"""
import subprocess
import sys

files = [
    'daily_metrics.py',
    'experience_engine.py',
    'learnings_extractor.py',
]

for filename in files:
    try:
        result = subprocess.run(
            ['git', 'show', f'HEAD:aios/agent_system/{filename}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd='C:\\Users\\A\\.openclaw\\workspace'
        )
        
        if result.returncode == 0:
            with open(f'C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\{filename}', 'w', encoding='utf-8', newline='\n') as f:
                f.write(result.stdout)
            print(f"[OK] Restored {filename}")
        else:
            print(f"[FAIL] {filename}: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
