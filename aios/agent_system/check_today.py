import json
from pathlib import Path

execs = [json.loads(line) for line in Path('task_executions.jsonl').read_text(encoding='utf-8').strip().split('\n') if line.strip()]
today = [e for e in execs if e.get('timestamp', '').startswith('2026-03-09')]
print(f'今日任务执行: {len(today)}')

failed = [e for e in today if e.get('status') == 'failed']
print(f'失败: {len(failed)}')

if failed:
    print('\n失败任务:')
    import pprint
    pprint.pprint(failed[-3:])

completed = [e for e in today if e.get('status') == 'completed']
print(f'\n成功: {len(completed)}')
