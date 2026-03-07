import json
from pathlib import Path
from paths import TASK_EXECUTIONS, SPAWN_REQUESTS, LESSONS, EXPERIENCE_LIBRARY, DATA_DIR

# LanceDB 状态
db_path = Path('lancedb_trajectories')
if db_path.exists():
    try:
        import lancedb
        db = lancedb.connect(str(db_path))
        table = db.open_table('trajectories')
        total = table.count_rows()
        print(f'LanceDB 轨迹总数: {total}')
        rows = table.to_pandas()
        print(rows[['task_id', 'strategy', 'success']].to_string())
    except Exception as e:
        print(f'LanceDB 读取失败: {e}')
else:
    print('LanceDB 数据库不存在')

# 任务执行记录
exec_file = TASK_EXECUTIONS
if exec_file.exists():
    with open(exec_file, 'r', encoding='utf-8') as f:
        execs = [json.loads(line) for line in f if line.strip()]
    total_tasks = len(execs)
    completed = len([e for e in execs if e.get('status') == 'completed'])
    failed = len([e for e in execs if e.get('status') == 'failed'])
    print(f'\n任务执行统计:')
    print(f'  总数: {total_tasks}, 成功: {completed}, 失败: {failed}')
    if total_tasks > 0:
        print(f'  成功率: {completed/total_tasks*100:.1f}%')
else:
    print('task_executions.jsonl 不存在')

# spawn_requests
spawn_file = SPAWN_REQUESTS
if spawn_file.exists():
    with open(spawn_file, 'r', encoding='utf-8') as f:
        spawns = [json.loads(line) for line in f if line.strip()]
    regen_spawns = [s for s in spawns if s.get('regeneration')]
    print(f'\nSpawn 重生请求: {len(regen_spawns)}')
    for s in regen_spawns[-5:]:
        print(f"  {s.get('task_id')} | strategy: {s.get('strategy', {}).get('type', 'N/A')}")
else:
    print('spawn_requests.jsonl 不存在')

# lessons
lessons_file = LESSONS
if lessons_file.exists():
    with open(lessons_file, 'r', encoding='utf-8') as f:
        lessons = json.load(f)
    pending = [l for l in lessons if not l.get('resolved', False)]
    resolved = [l for l in lessons if l.get('resolved', False)]
    print(f'\nLessons: 总数={len(lessons)}, 待处理={len(pending)}, 已解决={len(resolved)}')
else:
    print('lessons.json 不存在')

# experience_library
exp_file = EXPERIENCE_LIBRARY
if exp_file.exists():
    with open(exp_file, 'r', encoding='utf-8') as f:
        exps = [json.loads(line) for line in f if line.strip()]
    print(f'\n经验库条目: {len(exps)}')
    for e in exps[-3:]:
        print(f"  {e.get('task_id')} | {e.get('strategy', {}).get('type', 'N/A')} | success={e.get('success')}")
else:
    print('experience_library.jsonl 不存在')
