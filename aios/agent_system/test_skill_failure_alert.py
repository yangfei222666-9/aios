"""
测试连续失败预警
"""
import json
from pathlib import Path
from datetime import datetime

# 写入测试数据：模拟 test-skill 连续失败 3 次
data_dir = Path('data')
exec_file = data_dir / 'skill_executions.jsonl'

test_records = [
    {'execution_id': 'exec-test-001', 'skill_id': 'test-skill', 'skill_name': 'Test Skill', 'skill_version': '1.0.0', 'task_id': 'task-001', 'command': 'python test.py', 'started_at': '2026-03-07T10:00:00', 'duration_ms': 5000, 'status': 'success', 'error': None},
    {'execution_id': 'exec-test-002', 'skill_id': 'test-skill', 'skill_name': 'Test Skill', 'skill_version': '1.0.0', 'task_id': 'task-002', 'command': 'python test.py', 'started_at': '2026-03-07T11:00:00', 'duration_ms': 30000, 'status': 'failed', 'error': 'timeout: operation exceeded 30s'},
    {'execution_id': 'exec-test-003', 'skill_id': 'test-skill', 'skill_name': 'Test Skill', 'skill_version': '1.0.0', 'task_id': 'task-003', 'command': 'python test.py', 'started_at': '2026-03-07T12:00:00', 'duration_ms': 30000, 'status': 'failed', 'error': 'timeout: operation exceeded 30s'},
    {'execution_id': 'exec-test-004', 'skill_id': 'test-skill', 'skill_name': 'Test Skill', 'skill_version': '1.0.0', 'task_id': 'task-004', 'command': 'python test.py', 'started_at': '2026-03-07T13:00:00', 'duration_ms': 30000, 'status': 'failed', 'error': 'timeout: operation exceeded 30s'},
]

with open(exec_file, 'a', encoding='utf-8') as f:
    for r in test_records:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print('✓ 测试数据写入完成')

# 运行告警检查
from skill_failure_alert import check_consecutive_failures, format_alert_message
alerts = check_consecutive_failures(window_size=5)

print(f'\n检测到 {len(alerts)} 个告警:\n')
for a in alerts:
    print(format_alert_message(a))
    print(f'  alert_level: {a["alert_level"]}')
    print(f'  consecutive_failures: {a["consecutive_failures"]}')
    print(f'  last_failure_reason: {a["last_failure_reason"]}')
    print(f'  suggested_recovery: {a["suggested_recovery"]}')
    print()

# 验证 warn/crit 逻辑
test_skill_alert = [a for a in alerts if a['skill_id'] == 'test-skill']
if test_skill_alert:
    a = test_skill_alert[0]
    assert a['alert_level'] == 'crit', f"Expected crit, got {a['alert_level']}"
    assert a['consecutive_failures'] == 3, f"Expected 3, got {a['consecutive_failures']}"
    assert a['last_failure_reason'] == 'timeout', f"Expected timeout, got {a['last_failure_reason']}"
    print('✅ warn/crit 逻辑验证通过')
else:
    print('❌ 未检测到 test-skill 告警')
