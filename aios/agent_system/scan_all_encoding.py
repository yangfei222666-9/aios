#!/usr/bin/env python3
"""扫描所有编码问题（不只是 f-string）"""
import re
from pathlib import Path

base_dir = Path(__file__).parent
learner_files = list(base_dir.glob("learner_*.py"))

print("扫描所有编码问题...\n")

for filepath in learner_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试编译
        compile(content, str(filepath), 'exec')
        print(f"✅ {filepath.name} 无编码问题")
    
    except SyntaxError as e:
        print(f"❌ {filepath.name}:")
        print(f"   L{e.lineno}: {e.msg}")
        print(f"   {e.text.strip() if e.text else '(无法显示)'}")
        print()
