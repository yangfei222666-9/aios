#!/usr/bin/env python3
"""Phase 3 修复后验证"""
import json
from pathlib import Path
from paths import AIOS_ROOT, TASK_EXECUTIONS, EXPERIENCE_LIBRARY, EXPERIENCE_DB_V4

AIOS_DIR = AIOS_ROOT

print("=" * 60)
print("Phase 3 修复验证")
print("=" * 60)

# 1. 灰度配置
config = json.loads((AIOS_DIR / "learner_v4_config.json").read_text(encoding="utf-8"))
ratio = config.get("grayscale_ratio", 0)
print(f"\n[1] 灰度比例: {ratio:.0%} {'✅' if ratio >= 0.5 else '❌'}")

# 2. LanceDB 轨迹数
import lancedb
db = lancedb.connect(str(AIOS_DIR / "experience_db.lance"))
table = db.open_table("success_patterns")
lance_count = table.count_rows()
print(f"[2] LanceDB 轨迹数: {lance_count} {'✅' if lance_count >= 3 else '❌'}")
df = table.to_pandas()
for _, row in df.iterrows():
    print(f"    {row['task_id']} | {row['error_type']} | {row['strategy_used']} | conf={row['confidence']}")

# 3. experience_library 去重
with open(EXPERIENCE_LIBRARY, 'r', encoding='utf-8') as f:
    exp_entries = [json.loads(l) for l in f if l.strip()]
ids = [e.get('lesson_id', e.get('task_id', '?')) for e in exp_entries]
has_dupes = len(ids) != len(set(ids))
print(f"[3] experience_library: {len(exp_entries)} 条, 重复={'有 ❌' if has_dupes else '无 ✅'}")

# 4. experience_db_v4 幂等库
v4_file = EXPERIENCE_DB_V4
if v4_file.exists():
    with open(v4_file, 'r', encoding='utf-8') as f:
        v4_entries = [json.loads(l) for l in f if l.strip()]
    v4_keys = [e.get('idem_key') for e in v4_entries]
    v4_dupes = len(v4_keys) != len(set(v4_keys))
    print(f"[4] experience_db_v4: {len(v4_entries)} 条, 重复={'有 ❌' if v4_dupes else '无 ✅'}")

# 5. task_executions status 完整率
with open(TASK_EXECUTIONS, 'r', encoding='utf-8') as f:
    execs = [json.loads(l) for l in f if l.strip()]
total = len(execs)
with_status = sum(1 for e in execs if e.get('status') in ('completed', 'failed'))
completeness = with_status / total if total else 0
statuses = {}
for e in execs:
    s = e.get('status', 'unknown')
    statuses[s] = statuses.get(s, 0) + 1
print(f"[5] task_executions status: {with_status}/{total} ({completeness:.0%}) {'✅' if completeness >= 0.99 else '❌'}")
print(f"    分布: {statuses}")
success_rate = statuses.get('completed', 0) / total * 100 if total else 0
print(f"    真实成功率: {success_rate:.1f}%")

# 6. 推荐命中率模拟（灰度50%下）
from experience_learner_v4 import ExperienceLearnerV4
learner = ExperienceLearnerV4()
hits = 0
trials = 20
for i in range(trials):
    rec = learner.recommend({"error_type": "timeout", "task_id": f"sim-{i}"})
    if rec["source"] == "experience":
        hits += 1
hit_rate = hits / trials
print(f"[6] 推荐命中率模拟 (20次 timeout): {hits}/{trials} ({hit_rate:.0%}) {'✅' if hit_rate > 0.2 else '⚠️'}")

# 总结
print("\n" + "=" * 60)
checks = [
    ratio >= 0.5,
    lance_count >= 3,
    not has_dupes,
    completeness >= 0.99,
    hit_rate > 0.1,
]
passed = sum(checks)
print(f"验证结果: {passed}/{len(checks)} 通过 {'🎉 ALL PASS' if all(checks) else '⚠️ 部分未通过'}")
print("=" * 60)
