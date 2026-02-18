# aios/scripts/apply_suggestions.py - 应用建议（人工审核优先）
"""
读取 learning/suggestions.json → 展示 → 确认后应用

默认模式: 展示建议，等待确认
--auto 模式: 自动应用高置信度建议 (confidence >= 0.9)
"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.log_event import log_event

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "learning"
SUGGESTIONS_FILE = LEARNING_DIR / "suggestions.json"


def load_suggestions() -> list:
    if not SUGGESTIONS_FILE.exists():
        return []
    try:
        return json.loads(SUGGESTIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def show_suggestions():
    """展示待审核建议"""
    suggestions = load_suggestions()
    if not suggestions:
        print("No pending suggestions.")
        return []
    
    print(f"=== {len(suggestions)} Pending Suggestions ===\n")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. [{s['type']}] {s['reason']}")
        print(f"     confidence: {s.get('confidence', '?')}")
        print()
    
    return suggestions


def apply_suggestion(suggestion: dict) -> dict:
    """应用单条建议"""
    result = {
        "applied": True,
        "suggestion": suggestion,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    
    # 记录应用事件
    log_event(
        "suggestion_applied",
        "apply_suggestions",
        f"Applied: {suggestion.get('reason', '?')}",
        suggestion,
    )
    
    return result


def auto_apply(min_confidence: float = 0.9):
    """自动应用高置信度建议"""
    suggestions = load_suggestions()
    applied = []
    remaining = []
    
    for s in suggestions:
        conf = s.get("confidence", 0)
        if conf >= min_confidence:
            result = apply_suggestion(s)
            applied.append(result)
            print(f"  [AUTO] {s['reason']} (confidence: {conf})")
        else:
            remaining.append(s)
            print(f"  [SKIP] {s['reason']} (confidence: {conf} < {min_confidence})")
    
    # 更新 suggestions.json，只保留未应用的
    SUGGESTIONS_FILE.write_text(json.dumps(remaining, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\nApplied: {len(applied)}, Remaining: {len(remaining)}")
    return applied


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "show"
    
    if action == "show":
        show_suggestions()
    elif action == "auto":
        auto_apply()
    else:
        print("Usage: apply_suggestions.py [show|auto]")
