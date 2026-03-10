#!/usr/bin/env python3
"""
Phase 3 淇鑴氭湰 - 涓€娆℃€ф墽琛?1. 娓呯悊 experience_library.jsonl 閲嶅椤?2. 鎵归噺瀵煎叆鍘婚噸鍚庣殑缁忛獙鍒?LanceDB (experience_db.lance)
3. 鍥炲～ task_executions_v2.jsonl 鐨?status 瀛楁
"""
import json
from pathlib import Path
from datetime import datetime

AIOS_DIR = Path(__file__).resolve().parent

def fix_experience_library():
    """娓呯悊 experience_library.jsonl 閲嶅椤?""
    exp_file = AIOS_DIR / "experience_library.jsonl"
    if not exp_file.exists():
        print("[SKIP] experience_library.jsonl not found")
        return []

    with open(exp_file, 'r', encoding='utf-8') as f:
        entries = [json.loads(l) for l in f if l.strip()]

    print(f"[FIX] experience_library: {len(entries)} entries before dedup")

    # 鍘婚噸锛氭寜 (lesson_id, error_type) 淇濈暀鏈€鏂扮殑
    seen = {}
    for e in entries:
        key = (e.get('lesson_id', e.get('task_id', '?')), e.get('error_type', '?'))
        if key not in seen or e.get('timestamp', '') > seen[key].get('timestamp', ''):
            seen[key] = e

    deduped = list(seen.values())
    print(f"[FIX] experience_library: {len(deduped)} entries after dedup (removed {len(entries) - len(deduped)})")

    # 鍐欏洖
    with open(exp_file, 'w', encoding='utf-8') as f:
        for e in deduped:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')

    return deduped


def import_to_lancedb(deduped_entries):
    """灏嗗幓閲嶅悗鐨勭粡楠屾壒閲忓鍏?LanceDB experience_db.lance"""
    try:
        import lancedb
    except ImportError:
        print("[SKIP] lancedb not installed")
        return

    db_path = str(AIOS_DIR / "experience_db.lance")
    db = lancedb.connect(db_path)

    table_name = "success_patterns"
    if table_name in db.table_names():
        table = db.open_table(table_name)
        existing_count = table.count_rows()
    else:
        existing_count = 0
        table = None

    print(f"[FIX] LanceDB {table_name}: {existing_count} existing rows")

    # 鑾峰彇宸叉湁 task_id 閬垮厤閲嶅
    existing_ids = set()
    if table and existing_count > 0:
        df = table.to_pandas()
        existing_ids = set(df['task_id'].tolist())

    # 鍑嗗瀵煎叆鏁版嵁
    try:
        from embedding_generator import generate_embedding
    except ImportError:
        print("[SKIP] embedding_generator not available, using zero vectors")
        generate_embedding = lambda x: [0.0] * 384

    new_rows = []
    for e in deduped_entries:
        if not e.get('success', False):
            continue

        lesson_id = e.get('lesson_id', e.get('task_id', '?'))
        if lesson_id in existing_ids:
            continue

        error_type = e.get('error_type', 'unknown')
        # 浠?strategy.actions 鎻愬彇绛栫暐鍚?        actions = e.get('strategy', {}).get('actions', [])
        if actions:
            strategy_name = '+'.join(a.get('type', '?') for a in actions)
        else:
            strategy_name = 'default_recovery'

        desc = e.get('feedback', {}).get('context', lesson_id)
        embedding = generate_embedding(desc)

        new_rows.append({
            "vector": embedding,
            "task_id": lesson_id,
            "error_type": error_type,
            "strategy_used": strategy_name,
            "success": True,
            "timestamp": e.get('timestamp', datetime.now().isoformat()),
            "regen_time": 0.0,
            "confidence": 0.95,
        })

    if new_rows:
        if table is None:
            import pyarrow as pa
            schema = pa.schema([
                pa.field("vector", pa.list_(pa.float32(), 384)),
                pa.field("task_id", pa.string()),
                pa.field("error_type", pa.string()),
                pa.field("strategy_used", pa.string()),
                pa.field("success", pa.bool_()),
                pa.field("timestamp", pa.string()),
                pa.field("regen_time", pa.float64()),
                pa.field("confidence", pa.float64())
            ])
            table = db.create_table(table_name, schema=schema)

        table.add(new_rows)
        print(f"[FIX] LanceDB: imported {len(new_rows)} new trajectories")
    else:
        print(f"[FIX] LanceDB: no new entries to import (all already exist)")

    # 楠岃瘉
    final_count = table.count_rows() if table else 0
    print(f"[FIX] LanceDB {table_name}: {final_count} total rows now")


def import_to_experience_db_v4(deduped_entries):
    """鍚屾瀵煎叆鍒?experience_db_v4.jsonl锛坴4 骞傜瓑缁忛獙搴擄級"""
    v4_file = AIOS_DIR / "experience_db_v4.jsonl"

    # 璇诲彇宸叉湁
    existing_keys = set()
    if v4_file.exists():
        with open(v4_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        existing_keys.add(entry.get('idem_key', ''))
                    except:
                        pass

    import hashlib
    new_count = 0
    with open(v4_file, 'a', encoding='utf-8') as f:
        for e in deduped_entries:
            if not e.get('success', False):
                continue

            error_type = e.get('error_type', 'unknown')
            actions = e.get('strategy', {}).get('actions', [])
            strategy = '+'.join(a.get('type', '?') for a in actions) if actions else 'default_recovery'

            raw = f"{error_type}:{strategy}"
            idem_key = hashlib.sha256(raw.encode()).hexdigest()[:16]

            if idem_key in existing_keys:
                continue

            entry = {
                "idem_key": idem_key,
                "error_type": error_type,
                "strategy": strategy,
                "strategy_version": "v4.0.0",
                "task_id": e.get('lesson_id', e.get('task_id', 'unknown')),
                "confidence": 0.95,
                "recovery_time": 0.0,
                "timestamp": e.get('timestamp', datetime.now().isoformat()),
                "success": True,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            existing_keys.add(idem_key)
            new_count += 1

    print(f"[FIX] experience_db_v4: imported {new_count} new entries")


def fix_task_executions():
    """鍥炲～ task_executions_v2.jsonl 鐨?status 瀛楁"""
    exec_file = AIOS_DIR / "task_executions_v2.jsonl"
    if not exec_file.exists():
        print("[SKIP] task_executions_v2.jsonl not found")
        return

    with open(exec_file, 'r', encoding='utf-8') as f:
        entries = [json.loads(l) for l in f if l.strip()]

    fixed = 0
    for e in entries:
        if 'status' not in e or e['status'] is None:
            result = e.get('result', {})
            if isinstance(result, dict):
                if result.get('success', False):
                    e['status'] = 'completed'
                elif result.get('error'):
                    e['status'] = 'failed'
                else:
                    e['status'] = 'completed' if result.get('success') else 'unknown'
            else:
                e['status'] = 'unknown'
            fixed += 1

    print(f"[FIX] task_executions: backfilled {fixed}/{len(entries)} status fields")

    # 缁熻
    statuses = {}
    for e in entries:
        s = e.get('status', 'unknown')
        statuses[s] = statuses.get(s, 0) + 1
    print(f"[FIX] task_executions status distribution: {statuses}")

    # 鍐欏洖
    with open(exec_file, 'w', encoding='utf-8') as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')

    return statuses


def main():
    print("=" * 60)
    print("Phase 3 淇鑴氭湰 - 寮€濮嬫墽琛?)
    print(f"鏃堕棿: {datetime.now().isoformat()}")
    print("=" * 60)

    # Step 1: 娓呯悊閲嶅
    print("\n--- Step 1: 娓呯悊 experience_library 閲嶅椤?---")
    deduped = fix_experience_library()

    # Step 2: 瀵煎叆 LanceDB
    print("\n--- Step 2: 鎵归噺瀵煎叆 LanceDB ---")
    import_to_lancedb(deduped)

    # Step 2b: 鍚屾鍒?v4 缁忛獙搴?    print("\n--- Step 2b: 鍚屾鍒?experience_db_v4 ---")
    import_to_experience_db_v4(deduped)

    # Step 3: 鍥炲～ status
    print("\n--- Step 3: 鍥炲～ task_executions status ---")
    statuses = fix_task_executions()

    # 鎬荤粨
    print("\n" + "=" * 60)
    print("淇瀹屾垚锛?)
    print(f"  experience_library: 鍘婚噸鍚?{len(deduped)} 鏉?)
    print(f"  task_executions status: {statuses}")
    print("=" * 60)


if __name__ == '__main__':
    main()

