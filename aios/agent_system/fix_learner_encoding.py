#!/usr/bin/env python3
"""修复 learner_*.py 文件的编码问题"""
import re
from pathlib import Path

# 需要修复的文件和对应的行号
fixes = {
    "learner_agent_behavior.py": {
        56: '        print(f"  收集了 {agent_data[\'total_agents\']} 个 Agent 的数据")'
    },
    "learner_error_pattern.py": {
        54: '        print(f"  收集了 {error_data[\'total_errors\']} 个错误")'
    },
    "learner_optimization.py": {
        55: '        print(f"  收集了 {optimization_data[\'total_optimizations\']} 个优化")'
    },
    "learner_playbook.py": {
        52: '        print(f"  收集了 {playbook_data[\'total_executions\']} 次执行")'
    },
    "learner_provider.py": {
        52: '        print(f"  收集了 {provider_data[\'total_calls\']} 次调用")'
    }
}

base_dir = Path(__file__).parent

for filename, line_fixes in fixes.items():
    filepath = base_dir / filename
    
    # 读取文件（尝试多种编码）
    content = None
    for encoding in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.readlines()
            break
        except:
            continue
    
    if content is None:
        print(f"❌ 无法读取 {filename}")
        continue
    
    # 修复指定行
    modified = False
    for line_num, new_line in line_fixes.items():
        idx = line_num - 1  # 转换为 0-based index
        if idx < len(content):
            old_line = content[idx].rstrip()
            if 'print(f"' in old_line and not old_line.endswith('")'):
                content[idx] = new_line + '\n'
                modified = True
                print(f"✅ {filename}:{line_num} 已修复")
    
    # 写回文件（UTF-8）
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"   {filename} 已保存为 UTF-8")

print("\n验证修复结果...")
import py_compile
for filename in fixes.keys():
    filepath = base_dir / filename
    try:
        py_compile.compile(str(filepath), doraise=True)
        print(f"✅ {filename} 语法正确")
    except SyntaxError as e:
        print(f"❌ {filename} 仍有错误: {e}")
