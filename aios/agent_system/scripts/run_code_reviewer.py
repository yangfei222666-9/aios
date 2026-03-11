#!/usr/bin/env python3
"""
Code_Reviewer Agent 执行脚本
审查 AIOS 代码，发现问题和改进点
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import re

def run_code_reviewer():
    """执行 Code Reviewer 任务"""
    
    base_dir = Path(__file__).parent.parent
    
    print("=== Code_Reviewer Agent 执行 ===\n")
    
    issues_found = []
    
    # 1. 检查代码质量
    print("1. 检查代码质量...")
    
    # 检查核心模块（动态扫描，避免硬编码）
    core_dir = base_dir / 'core'
    if core_dir.exists():
        core_modules = [f for f in core_dir.glob('*.py') if f.is_file()]
    else:
        core_modules = []
    
    for module_path in core_modules:
        if not module_path.exists():
            issues_found.append({
                'type': 'missing_file',
                'file': str(module_path.name),
                'severity': 'high',
                'issue': '核心模块文件不存在'
            })
            continue
        
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # 检查文档字符串
        if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
            issues_found.append({
                'type': 'missing_docstring',
                'file': module_path.name,
                'severity': 'low',
                'issue': '缺少模块级文档字符串'
            })
        
        # 检查异常处理
        try_count = content.count('try:')
        except_count = content.count('except')
        if try_count > 0 and except_count < try_count:
            issues_found.append({
                'type': 'incomplete_exception_handling',
                'file': module_path.name,
                'severity': 'medium',
                'issue': f'try块({try_count})多于except块({except_count})'
            })
        
        # 检查TODO注释
        todos = [i+1 for i, line in enumerate(lines) if 'TODO' in line or 'FIXME' in line]
        if todos:
            issues_found.append({
                'type': 'pending_todos',
                'file': module_path.name,
                'severity': 'low',
                'issue': f'存在 {len(todos)} 个待办事项',
                'lines': todos[:5]  # 只显示前5个
            })
    
    # 2. 检查数据结构一致性
    print("2. 检查数据结构一致性...")
    
    # 检查 agents.json 结构
    agents_path = base_dir / 'data/agents.json'
    if agents_path.exists():
        with open(agents_path, 'r', encoding='utf-8') as f:
            agents_data = json.load(f)
        
        required_fields = ['name', 'role', 'group', 'enabled', 'routable']
        for agent in agents_data['agents']:
            missing_fields = [f for f in required_fields if f not in agent]
            if missing_fields:
                issues_found.append({
                    'type': 'incomplete_agent_definition',
                    'file': 'agents.json',
                    'agent': agent.get('name', 'unknown'),
                    'severity': 'medium',
                    'issue': f'缺少必需字段: {", ".join(missing_fields)}'
                })
    
    # 3. 检查命名规范
    print("3. 检查命名规范...")
    
    # 检查文件命名
    script_dir = base_dir / 'scripts'
    if script_dir.exists():
        for script_file in script_dir.glob('*.py'):
            # 检查是否使用下划线命名
            if not re.match(r'^[a-z_]+\.py$', script_file.name):
                issues_found.append({
                    'type': 'naming_convention',
                    'file': script_file.name,
                    'severity': 'low',
                    'issue': '文件名应使用小写字母和下划线'
                })
    
    # 4. 生成报告
    print("\n=== Code Review 报告 ===\n")
    
    if not issues_found:
        print("✓ 代码质量良好，未发现明显问题")
        result = {
            'success': True,
            'issues_found': 0,
            'message': '代码质量良好'
        }
    else:
        print(f"发现 {len(issues_found)} 个问题:\n")
        
        # 按严重程度分组
        by_severity = {'high': [], 'medium': [], 'low': []}
        for issue in issues_found:
            by_severity[issue['severity']].append(issue)
        
        for severity in ['high', 'medium', 'low']:
            if by_severity[severity]:
                print(f"[{severity.upper()}] {len(by_severity[severity])} 个问题:")
                for issue in by_severity[severity][:3]:  # 每个级别最多显示3个
                    print(f"  - {issue['file']}: {issue['issue']}")
                if len(by_severity[severity]) > 3:
                    print(f"  ... 还有 {len(by_severity[severity]) - 3} 个")
                print()
        
        result = {
            'success': True,
            'issues_found': len(issues_found),
            'issues': issues_found,
            'summary': {
                'high': len(by_severity['high']),
                'medium': len(by_severity['medium']),
                'low': len(by_severity['low'])
            },
            'message': f'发现 {len(issues_found)} 个问题'
        }
    
    # 5. 记录执行结果
    execution_record = {
        'agent_id': 'Code_Reviewer',
        'executed_at': datetime.now().isoformat(),
        'result': result
    }
    
    record_path = base_dir / 'data/agent_execution_record.jsonl'
    with open(record_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(execution_record, ensure_ascii=False) + '\n')
    
    print(f"\n执行记录已写入: {record_path}")
    
    return result

if __name__ == '__main__':
    try:
        result = run_code_reviewer()
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)
