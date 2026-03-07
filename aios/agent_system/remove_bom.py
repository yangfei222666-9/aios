#!/usr/bin/env python3
"""移除 UTF-8 BOM"""
from pathlib import Path

base_dir = Path(__file__).parent
files_to_fix = [
    "learner_agent_behavior.py",
    "learner_error_pattern.py",
    "learner_optimization.py",
    "learner_playbook.py",
    "learner_provider.py"
]

for filename in files_to_fix:
    filepath = base_dir / filename
    
    # 读取（保留 BOM）
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # 移除 BOM
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
        print(f"[OK] {filename} 移除 BOM")
    else:
        print(f"⏭️  {filename} 无 BOM")
    
    # 写回
    with open(filepath, 'wb') as f:
        f.write(content)

print("\n验证修复结果...")
import py_compile
all_passed = True
for filename in files_to_fix:
    filepath = base_dir / filename
    try:
        py_compile.compile(str(filepath), doraise=True)
        print(f"[OK] {filename} 语法正确")
    except SyntaxError as e:
        print(f"[FAIL] {filename} 仍有错误: {e}")
        all_passed = False

if all_passed:
    print("\n[SUCCESS] 所有文件修复成功！")
