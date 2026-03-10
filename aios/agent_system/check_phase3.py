import json
from pathlib import Path
from paths import TASK_EXECUTIONS, SPAWN_REQUESTS, LESSONS, EXPERIENCE_LIBRARY, DATA_DIR

# LanceDB 鐘舵€?db_path = Path('lancedb_trajectories')
if db_path.exists():
    try:
        import lancedb
        db = lancedb.connect(str(db_path))
        table = db.open_table('trajectories')
        total = table.count_rows()
        print(f'LanceDB 杞ㄨ抗鎬绘暟: {total}')
        rows = table.to_pandas()
        print(rows[['task_id', 'strategy', 'success']].to_string())
    except Exception as e:
        print(f'LanceDB 璇诲彇澶辫触: {e}')
else:
    print('LanceDB 鏁版嵁搴撲笉瀛樺湪')

# 浠诲姟鎵ц璁板綍
exec_file = TASK_EXECUTIONS
if exec_file.exists():
    with open(exec_file, 'r', encoding='utf-8') as f:
        execs = [json.loads(line) for line in f if line.strip()]
    total_tasks = len(execs)
    completed = len([e for e in execs if e.get('status') == 'completed'])
    failed = len([e for e in execs if e.get('status') == 'failed'])
    print(f'\n浠诲姟鎵ц缁熻:')
    print(f'  鎬绘暟: {total_tasks}, 鎴愬姛: {completed}, 澶辫触: {failed}')
    if total_tasks > 0:
        print(f'  鎴愬姛鐜? {completed/total_tasks*100:.1f}%')
else:
    print('task_executions_v2.jsonl 涓嶅瓨鍦?)

# spawn_requests
spawn_file = SPAWN_REQUESTS
if spawn_file.exists():
    with open(spawn_file, 'r', encoding='utf-8') as f:
        spawns = [json.loads(line) for line in f if line.strip()]
    regen_spawns = [s for s in spawns if s.get('regeneration')]
    print(f'\nSpawn 閲嶇敓璇锋眰: {len(regen_spawns)}')
    for s in regen_spawns[-5:]:
        print(f"  {s.get('task_id')} | strategy: {s.get('strategy', {}).get('type', 'N/A')}")
else:
    print('spawn_requests.jsonl 涓嶅瓨鍦?)

# lessons
lessons_file = LESSONS
if lessons_file.exists():
    with open(lessons_file, 'r', encoding='utf-8') as f:
        lessons = json.load(f)
    pending = [l for l in lessons if not l.get('resolved', False)]
    resolved = [l for l in lessons if l.get('resolved', False)]
    print(f'\nLessons: 鎬绘暟={len(lessons)}, 寰呭鐞?{len(pending)}, 宸茶В鍐?{len(resolved)}')
else:
    print('lessons.json 涓嶅瓨鍦?)

# experience_library
exp_file = EXPERIENCE_LIBRARY
if exp_file.exists():
    with open(exp_file, 'r', encoding='utf-8') as f:
        exps = [json.loads(line) for line in f if line.strip()]
    print(f'\n缁忛獙搴撴潯鐩? {len(exps)}')
    for e in exps[-3:]:
        print(f"  {e.get('task_id')} | {e.get('strategy', {}).get('type', 'N/A')} | success={e.get('success')}")
else:
    print('experience_library.jsonl 涓嶅瓨鍦?)

