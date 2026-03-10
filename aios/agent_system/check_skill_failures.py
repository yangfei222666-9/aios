import json
import os

base = r'C:\Users\A\.openclaw\workspace\aios\agent_system'

# 妫€鏌?task_executions_v2.jsonl 涓殑澶辫触璁板綍
exec_file = os.path.join(base, TASK_EXECUTIONS)
if os.path.exists(exec_file):
    print('=== task_executions_v2.jsonl failures ===')
    with open(exec_file, encoding='utf-8') as f:
        for line in f:
            try:
                d = json.loads(line)
                if d.get('status') == 'failed':
                    print(f"task_id: {d.get('task_id')}")
                    print(f"agent_id: {d.get('agent_id')}")
                    print(f"error: {d.get('error', 'N/A')[:200]}")
                    print()
            except:
                pass

# 妫€鏌?lessons.json
lessons_file = os.path.join(base, 'lessons.json')
if os.path.exists(lessons_file):
    print('\n=== lessons.json ===')
    with open(lessons_file, encoding='utf-8') as f:
        lessons = json.load(f)
    for l in lessons:
        print(f"lesson_id: {l.get('lesson_id')}")
        print(f"task_type: {l.get('task_type')}")
        print(f"error_type: {l.get('error_type')}")
        print(f"error_message: {l.get('error_message', '')[:200]}")
        print()


