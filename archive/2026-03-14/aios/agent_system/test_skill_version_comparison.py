"""
测试版本对比
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

# 写入测试数据：模拟 test-skill v1.0.0 → v2.0.0 的改进
data_dir = Path('data')
exec_file = data_dir / 'skill_executions.jsonl'

now = datetime.now()

# v1.0.0: 成功率 60%, 平均耗时 2000ms
v1_records = [
    {'execution_id': f'exec-v1-{i:03d}', 'skill_id': 'version-test-skill', 'skill_name': 'Version Test Skill', 'skill_version': '1.0.0', 'task_id': f'task-v1-{i:03d}', 'command': 'python test.py', 'started_at': (now - timedelta(days=10-i)).isoformat(), 'duration_ms': 2000 + i*100, 'status': 'success' if i % 5 != 0 else 'failed', 'error': 'timeout' if i % 5 == 0 else None}
    for i in range(10)
]

# v2.0.0: 成功率 90%, 平均耗时 1200ms
v2_records = [
    {'execution_id': f'exec-v2-{i:03d}', 'skill_id': 'version-test-skill', 'skill_name': 'Version Test Skill', 'skill_version': '2.0.0', 'task_id': f'task-v2-{i:03d}', 'command': 'python test.py', 'started_at': (now - timedelta(days=5-i)).isoformat(), 'duration_ms': 1200 + i*50, 'status': 'success' if i % 10 != 0 else 'failed', 'error': 'timeout' if i % 10 == 0 else None}
    for i in range(10)
]

with open(exec_file, 'a', encoding='utf-8') as f:
    for r in v1_records + v2_records:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print('✓ 测试数据写入完成')

# 运行版本对比
from skill_version_comparison import compare_skill_versions, format_comparison_message
comparisons = compare_skill_versions(skill_id='version-test-skill')

print(f'\n检测到 {len(comparisons)} 个版本对比:\n')
for comp in comparisons:
    print(format_comparison_message(comp))
    print()

# 验证对比逻辑
if comparisons:
    comp = comparisons[0]
    c = comp['comparison']
    
    # 验证版本号
    assert c['from_version'] == '1.0.0', f"Expected 1.0.0, got {c['from_version']}"
    assert c['to_version'] == '2.0.0', f"Expected 2.0.0, got {c['to_version']}"
    
    # 验证成功率改进
    assert c['success_rate']['delta'] > 0, f"Expected positive delta, got {c['success_rate']['delta']}"
    assert c['success_rate']['trend'] == 'improved', f"Expected improved, got {c['success_rate']['trend']}"
    
    # 验证耗时改进
    assert c['avg_duration_ms']['delta'] < 0, f"Expected negative delta, got {c['avg_duration_ms']['delta']}"
    assert c['avg_duration_ms']['trend'] == 'improved', f"Expected improved, got {c['avg_duration_ms']['trend']}"
    
    # 验证综合趋势
    assert comp['overall_trend'] == 'improved', f"Expected improved, got {comp['overall_trend']}"
    
    print('✅ 版本对比逻辑验证通过')
else:
    print('❌ 未检测到版本对比')
