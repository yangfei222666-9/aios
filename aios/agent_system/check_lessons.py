import json
from pathlib import Path

# 检查 task_executions.jsonl 中的失败任务
exec_file = Path("task_executions.jsonl")
if exec_file.exists():
    failures = []
    with open(exec_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                task = json.loads(line)
                if task.get('status') == 'failed':
                    failures.append(task)
            except:
                pass
    print(f"Total failures in task_executions.jsonl: {len(failures)}")
    for f in failures[:10]:
        print(f"  task_id={f.get('task_id','?')} error_type={f.get('error_type','unknown')} error={f.get('error','')[:80]}")
else:
    print("task_executions.jsonl not found")

# 检查 lessons.json.migrated
lessons_file = Path("lessons.json.migrated")
if lessons_file.exists():
    with open(lessons_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lessons = data if isinstance(data, list) else data.get('lessons', [])
    print(f"\nlessons.json.migrated: {len(lessons)} entries")
    for l in lessons[:10]:
        print(f"  task_id={l.get('task_id','?')} error_type={l.get('error_type','unknown')} source={l.get('source','?')}")
