import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from phase3_observer import observe_phase3, generate_phase3_report
from datetime import datetime

# 真实执行结果（来自 sessions_spawn）
results = [
    {'task_id': 'lesson-001', 'error_type': 'timeout',            'runtimeMs': 10823},
    {'task_id': 'lesson-002', 'error_type': 'dependency_error',   'runtimeMs': 5908},
    {'task_id': 'lesson-003', 'error_type': 'logic_error',        'runtimeMs': 11130},
    {'task_id': 'lesson-004', 'error_type': 'resource_exhausted', 'runtimeMs': 25018},
]

for r in results:
    observe_phase3(
        task_id=r['task_id'],
        task_description=f"Bootstrapped Regeneration: {r['error_type']}",
        success=True,
        recovery_time=r['runtimeMs'] / 1000.0,
        agent_id='LowSuccess_Agent'
    )

generate_phase3_report()
print('Done.')
