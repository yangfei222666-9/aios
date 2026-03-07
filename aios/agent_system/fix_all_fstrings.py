#!/usr/bin/env python3
"""批量修复所有 learner_*.py 文件的 f-string 问题"""
import re
from pathlib import Path

# 所有需要修复的行（文件名 -> {行号: 新内容}）
fixes = {
    "learner_agent_behavior.py": {
        67: '        print(f"  识别了 {len(tool_analysis.get(\'effective_combinations\', []))} 个有效工具组合")',
        78: '        print(f"  识别了 {len(best_practices.get(\'practices\', []))} 个最佳实践")',
        84: '        print(f"  生成了 {len(suggestions)} 条建议")',
        92: '            print(f"  完成！生成 {len(suggestions)} 条建议")',
    },
    "learner_error_pattern.py": {
        60: '        print(f"  识别了 {len(repeat_analysis.get(\'patterns\', []))} 个重复错误模式")',
        66: '        print(f"  识别了 {len(root_cause_analysis.get(\'causes\', []))} 个根因")',
        78: '        print(f"  识别了 {len(temporal_analysis.get(\'patterns\', []))} 个时间规律")',
        84: '        print(f"  生成了 {len(suggestions)} 条建议")',
        92: '            print(f"  完成！生成 {len(suggestions)} 条建议")',
    },
    "learner_optimization.py": {
        61: '        print(f"  有效优化：{effectiveness_analysis.get(\'effective_count\', 0)} 个")',
        67: '        print(f"  无效优化：{len(ineffective_analysis.get(\'optimizations\', []))} 个")',
        73: '        print(f"  识别了 {len(trend_analysis.get(\'trends\', []))} 个趋势")',
        79: '        print(f"  生成了 {len(suggestions)} 条建议")',
        87: '            print(f"  完成！生成 {len(suggestions)} 条建议")',
    },
    "learner_playbook.py": {
        75: '        print(f"  生成了 {len(suggestions)} 条建议")',
        83: '            print(f"  完成！生成 {len(suggestions)} 条建议")',
    },
    "learner_provider.py": {
        69: '        print(f"  识别了 {len(error_analysis.get(\'error_types\', []))} 种错误类型")',
        75: '        print(f"  生成了 {len(suggestions)} 条建议")',
        83: '            print(f"  完成！生成 {len(suggestions)} 条建议")',
    }
}

base_dir = Path(__file__).parent
fixed_count = 0

for filename, line_fixes in fixes.items():
    filepath = base_dir / filename
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # 修复指定行
    for line_num, new_line in line_fixes.items():
        idx = line_num - 1
        if idx < len(lines):
            lines[idx] = new_line + '\n'
            fixed_count += 1
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"[OK] {filename} 已修复 {len(line_fixes)} 行")

print(f"\n总计修复: {fixed_count} 行")

# 验证
print("\n验证修复结果...")
import py_compile
all_passed = True
for filename in fixes.keys():
    filepath = base_dir / filename
    try:
        py_compile.compile(str(filepath), doraise=True)
        print(f"[OK] {filename} 语法正确")
    except SyntaxError as e:
        print(f"[FAIL] {filename} 仍有错误: {e}")
        all_passed = False

if all_passed:
    print("\n[SUCCESS] 所有文件修复成功！")
else:
    print("\n[WARN]  部分文件仍有问题")
