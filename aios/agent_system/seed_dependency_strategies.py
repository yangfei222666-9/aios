"""
seed_dependency_strategies.py
把 dependency_error 三个子类型的策略写入 experience_db_v4.jsonl（幂等）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from experience_learner_v4 import learner_v4

strategies = [
    # dependency_not_found → dependency_check
    {
        "task_id": "seed-dep-not-found",
        "error_type": "dependency_not_found",
        "strategy": "dependency_check",
        "confidence": 0.92,
        "recovery_time": 8.0,
        "strategy_version": "v4.1.0",
        "success": True,
    },
    # version_conflict → version_pin
    {
        "task_id": "seed-dep-version-conflict",
        "error_type": "version_conflict",
        "strategy": "version_pin",
        "confidence": 0.90,
        "recovery_time": 12.0,
        "strategy_version": "v4.1.0",
        "success": True,
    },
    # transient_dependency_failure → retry_with_mirror
    {
        "task_id": "seed-dep-transient",
        "error_type": "transient_dependency_failure",
        "strategy": "retry_with_mirror",
        "confidence": 0.88,
        "recovery_time": 15.0,
        "strategy_version": "v4.1.0",
        "success": True,
    },
]

print("Seeding dependency_error sub-strategies...")
for s in strategies:
    written = learner_v4.save_success(s)
    status = "written" if written else "skipped (idempotent)"
    print(f"  {s['error_type']} -> {s['strategy']}: {status}")

print("\nDone. Verifying...")
from experience_learner_v4 import ExperienceLearnerV4
l = ExperienceLearnerV4()
l.set_grayscale_ratio(1.0)

tests = [
    {"error_type": "dependency_error", "task_id": "v-001", "prompt": "no module named pandas, not found"},
    {"error_type": "dependency_error", "task_id": "v-002", "prompt": "version conflict: requires numpy>=1.24 but 1.21 installed"},
    {"error_type": "dependency_error", "task_id": "v-003", "prompt": "pip failed due to network timeout, mirror unreachable"},
    {"error_type": "dependency_error", "task_id": "v-004", "prompt": "dependency error occurred"},  # generic fallback
]

for t in tests:
    rec = l.recommend(t)
    print(f"  [{t['task_id']}] prompt='{t['prompt'][:40]}...'")
    print(f"    -> strategy={rec['recommended_strategy']} source={rec['source']} conf={rec['confidence']:.2f}")
