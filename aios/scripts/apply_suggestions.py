# aios/scripts/apply_suggestions.py - 受控应用
"""
核心原则：系统可以进化，但不允许自毁。

v0.1 安全规则（锁死）:
  ✅ 允许自动应用: alias 追加（只 append，不覆盖、不删除）
  ❌ 禁止自动应用: 阈值变更、模型路由变更、删除已有 alias、修改 config.yaml
"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.log_event import log_event
from scripts.config_loader import get_path, get_float, get_bool, CONFIG_PATH

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "learning"

SUGGESTIONS_FILE = get_path("paths.suggestions") or (LEARNING_DIR / "suggestions.json")
APPLIED_LOG = get_path("paths.applied_log") or (LEARNING_DIR / "applied_log.json")
PENDING_FILE = LEARNING_DIR / "pending_review.json"

alias_path_cfg = get_path("paths.alias")
if alias_path_cfg is None:
    raise FileNotFoundError(f"alias file not configured (set paths.alias in {CONFIG_PATH})")
LEARNED_FILE = alias_path_cfg

MIN_CONF = get_float("policy.alias_min_confidence", 0.80)
NO_OVERWRITE = get_bool("policy.alias_no_overwrite", True)


def load_suggestions() -> dict:
    if not SUGGESTIONS_FILE.exists():
        return {}
    try:
        return json.loads(SUGGESTIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_learned() -> dict:
    if not LEARNED_FILE.exists():
        return {}
    try:
        return json.loads(LEARNED_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_learned(aliases: dict):
    LEARNED_FILE.parent.mkdir(exist_ok=True)
    LEARNED_FILE.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")


def run(mode: str = "show") -> dict:
    data = load_suggestions()
    if not data:
        print("No pending suggestions.")
        return {"applied": 0, "pending": 0}

    alias_sug = data.get("alias_suggestions", [])
    threshold_warn = data.get("threshold_warnings", [])
    route_sug = data.get("route_suggestions", [])

    total = len(alias_sug) + len(threshold_warn) + len(route_sug)
    if total == 0:
        print("No pending suggestions.")
        return {"applied": 0, "pending": 0}

    if mode == "show":
        print(f"=== {total} Suggestions ===\n")
        for s in alias_sug:
            learned = load_learned()
            safe = s["input"] not in learned
            tag = "AUTO" if safe else "EXISTS"
            print(f"  [{tag}] alias: \"{s['input']}\" -> \"{s['suggested']}\" (confidence: {s['confidence']})")
        for s in threshold_warn:
            print(f"  [NEEDS REVIEW] threshold: {s['field']} {s['current']} -> {s['suggested']}")
        for s in route_sug:
            print(f"  [NEEDS REVIEW] route: HTTP {s['status_code']} x{s['count']}")
        return {"total": total}

    elif mode == "auto":
        applied = []
        pending_alias = []

        for s in alias_sug:
            learned = load_learned()
            conf = s.get("confidence", 0)

            if conf < MIN_CONF:
                pending_alias.append(s)
                print(f"  LOW CONF: \"{s['input']}\" (confidence {conf} < {MIN_CONF})")
                continue

            if NO_OVERWRITE and s["input"] in learned:
                pending_alias.append(s)
                print(f"  EXISTS: \"{s['input']}\" already in aliases")
                continue

            # safe: append only
            learned[s["input"]] = s["suggested"]
            save_learned(learned)

            record = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "alias": {s["input"]: s["suggested"]},
                "confidence": conf,
                "reason": s.get("reason", ""),
            }
            applied.append(record)

            log_event("suggestion_applied", "apply_suggestions",
                      f"alias: {s['input']} -> {s['suggested']}",
                      {"input": s["input"], "applied": s["suggested"]})
            print(f"  APPLIED: \"{s['input']}\" -> \"{s['suggested']}\" (confidence: {conf})")

        # threshold + route -> pending
        pending = {
            "generated_at": data.get("generated_at", ""),
            "alias_suggestions": pending_alias,
            "threshold_warnings": threshold_warn,
            "route_suggestions": route_sug,
        }

        for s in threshold_warn:
            print(f"  PENDING: threshold {s['field']} (needs human review)")
        for s in route_sug:
            print(f"  PENDING: route HTTP {s['status_code']} (needs human review)")

        has_pending = pending_alias or threshold_warn or route_sug
        if has_pending:
            PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")

        SUGGESTIONS_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")

        # write applied_log.json
        if applied:
            APPLIED_LOG.write_text(json.dumps(applied, ensure_ascii=False, indent=2), encoding="utf-8")

        pending_count = len(pending_alias) + len(threshold_warn) + len(route_sug)
        print(f"\nApplied: {len(applied)}, Pending review: {pending_count}")
        return {"applied": len(applied), "pending": pending_count}

    else:
        print(f"Unknown mode: {mode}")
        print("Usage: apply_suggestions.py [show|auto]")
        return {}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "show"
    run(mode)
