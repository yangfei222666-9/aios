#!/usr/bin/env python3
"""
策略映射细化 - dependency_error 子类型拆分
将 dependency_error → default_recovery 细化为：
  - dependency_not_found → retry_with_mirror
  - version_conflict → version_pin
  - transient_dependency_failure → dependency_check + retry

同时为 resource_exhausted 添加初始策略
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

AIOS_DIR = Path(__file__).resolve().parent
V4_FILE = AIOS_DIR / "experience_db_v4.jsonl"
STRATEGY_VERSION = "v4.1.0"  # 策略映射升级版本


def idem_key(error_type, strategy):
    raw = f"{error_type}:{strategy}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_existing_keys():
    keys = set()
    if V4_FILE.exists():
        with open(V4_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        e = json.loads(line)
                        keys.add(e.get('idem_key', ''))
                    except:
                        pass
    return keys


def add_strategy(error_type, strategy, confidence, task_id, existing_keys):
    """幂等添加策略到经验库"""
    key = idem_key(error_type, strategy)
    if key in existing_keys:
        print(f"  [SKIP] {error_type} → {strategy} (already exists)")
        return False

    entry = {
        "idem_key": key,
        "error_type": error_type,
        "strategy": strategy,
        "strategy_version": STRATEGY_VERSION,
        "task_id": task_id,
        "confidence": confidence,
        "recovery_time": 0.0,
        "timestamp": datetime.now().isoformat(),
        "success": True,
    }

    with open(V4_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    existing_keys.add(key)
    print(f"  [ADD] {error_type} → {strategy} (conf={confidence}, v={STRATEGY_VERSION})")
    return True


def add_to_lancedb(entries):
    """同步添加到 LanceDB"""
    try:
        import lancedb
        from embedding_generator import generate_embedding

        db = lancedb.connect(str(AIOS_DIR / "experience_db.lance"))
        table = db.open_table("success_patterns")

        # 获取已有 task_id
        df = table.to_pandas()
        existing_ids = set(df['task_id'].tolist())

        new_rows = []
        for e in entries:
            if e['task_id'] in existing_ids:
                continue
            embedding = generate_embedding(f"{e['error_type']} {e['strategy']}")
            new_rows.append({
                "vector": embedding,
                "task_id": e['task_id'],
                "error_type": e['error_type'],
                "strategy_used": e['strategy'],
                "success": True,
                "timestamp": e['timestamp'],
                "regen_time": 0.0,
                "confidence": e['confidence'],
            })

        if new_rows:
            table.add(new_rows)
            print(f"\n[LANCEDB] Added {len(new_rows)} new trajectories")
        else:
            print(f"\n[LANCEDB] No new entries to add")

        print(f"[LANCEDB] Total rows: {table.count_rows()}")
    except Exception as ex:
        print(f"\n[LANCEDB] Error: {ex}")


def main():
    print("=" * 60)
    print("策略映射细化 v4.1.0")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    existing_keys = load_existing_keys()
    added_entries = []

    # ── dependency_error 子类型拆分 ──
    print("\n--- dependency_error 子类型细化 ---")

    mappings = [
        ("dependency_not_found", "retry_with_mirror", 0.90, "strategy-dep-notfound"),
        ("version_conflict", "version_pin", 0.88, "strategy-dep-verconflict"),
        ("transient_dependency_failure", "dependency_check_and_retry", 0.85, "strategy-dep-transient"),
        # 保留原始 dependency_error 但升级策略
        ("dependency_error", "dependency_check_and_retry", 0.92, "strategy-dep-generic-v41"),
    ]

    for error_type, strategy, confidence, task_id in mappings:
        entry = {
            "error_type": error_type,
            "strategy": strategy,
            "confidence": confidence,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
        }
        if add_strategy(error_type, strategy, confidence, task_id, existing_keys):
            added_entries.append(entry)

    # ── resource_exhausted 初始策略 ──
    print("\n--- resource_exhausted 初始策略 ---")

    resource_mappings = [
        ("resource_exhausted", "reduce_batch_and_retry", 0.82, "strategy-resource-batch"),
        ("resource_exhausted", "stream_processing", 0.80, "strategy-resource-stream"),
    ]

    for error_type, strategy, confidence, task_id in resource_mappings:
        entry = {
            "error_type": error_type,
            "strategy": strategy,
            "confidence": confidence,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
        }
        if add_strategy(error_type, strategy, confidence, task_id, existing_keys):
            added_entries.append(entry)

    # ── 同步到 LanceDB ──
    print("\n--- 同步到 LanceDB ---")
    if added_entries:
        add_to_lancedb(added_entries)
    else:
        print("[SKIP] No new entries to sync")

    # ── 验证 ──
    print("\n--- 验证 ---")
    with open(V4_FILE, 'r', encoding='utf-8') as f:
        all_entries = [json.loads(l) for l in f if l.strip()]

    # 按 error_type 统计
    by_type = {}
    for e in all_entries:
        et = e.get('error_type') or 'unknown'  # 防止 None
        if et not in by_type:
            by_type[et] = []
        by_type[et].append(e.get('strategy', '?'))

    print(f"\n经验库策略分布 (共 {len(all_entries)} 条):")
    for et, strategies in sorted(by_type.items(), key=lambda x: x[0] or ''):
        print(f"  {et}: {strategies}")

    # 检查 dependency_error 是否还有纯 default_recovery
    dep_strategies = by_type.get('dependency_error', [])
    has_only_default = all(s == 'default_recovery' for s in dep_strategies)
    print(f"\n  dependency_error 仍只有 default_recovery: {'是 ⚠️' if has_only_default else '否 ✅'}")

    # 检查 resource_exhausted 覆盖
    res_strategies = by_type.get('resource_exhausted', [])
    print(f"  resource_exhausted 策略数: {len(res_strategies)} {'✅' if res_strategies else '❌'}")

    print("\n" + "=" * 60)
    print(f"策略映射细化完成！新增 {len(added_entries)} 条策略")
    print("=" * 60)


if __name__ == '__main__':
    main()
