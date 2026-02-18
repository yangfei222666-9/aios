# aios/scripts/apply_suggestions.py - 受控应用
"""
核心原则：系统可以进化，但不允许自毁。

v0.1 安全规则（锁死）:
  ✅ 允许自动应用:
    - alias 追加（只 append，不覆盖、不删除）
  
  ❌ 禁止自动应用（只能人工确认）:
    - 阈值变更
    - 模型路由变更
    - 删除已有 alias
    - 修改 config.yaml

输入: learning/suggestions.json
输出:
  - 安全建议 → 自动应用 → 记录到 events.jsonl
  - 危险建议 → 标记 pending → 等人工确认
"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.log_event import log_event

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "learning"
SUGGESTIONS_FILE = LEARNING_DIR / "suggestions.json"
PENDING_FILE = LEARNING_DIR / "pending_review.json"

# 安全白名单：只有这些类型允许自动应用
SAFE_AUTO_TYPES = {"alias_redirect"}

# 危险黑名单：这些类型必须人工确认
REQUIRES_HUMAN = {"threshold_warning", "route_suggestion", "config_change", "alias_delete"}

# learned_aliases 路径
LEARNED_FILE = Path(__file__).resolve().parent.parent.parent / "autolearn" / "data" / "learned_aliases.json"


def load_suggestions() -> list:
    if not SUGGESTIONS_FILE.exists():
        return []
    try:
        return json.loads(SUGGESTIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


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


def _is_safe(suggestion: dict) -> bool:
    """判断建议是否可以安全自动应用"""
    stype = suggestion.get("type", "")
    
    # 黑名单直接拒绝
    if stype in REQUIRES_HUMAN:
        return False
    
    # 白名单才允许
    if stype not in SAFE_AUTO_TYPES:
        return False
    
    # alias_redirect 额外检查：只允许追加，不允许覆盖已有
    if stype == "alias_redirect":
        learned = load_learned()
        inp = suggestion.get("input", "")
        if inp in learned:
            # 已有 alias，不自动覆盖
            return False
    
    return True


def apply_safe(suggestion: dict) -> dict:
    """应用一条安全建议（只做 alias 追加）"""
    stype = suggestion.get("type", "")
    
    if stype == "alias_redirect":
        learned = load_learned()
        inp = suggestion.get("input", "")
        target = suggestion.get("target", "")
        
        if not inp or not target:
            return {"applied": False, "reason": "missing input/target"}
        
        if inp in learned:
            return {"applied": False, "reason": f"alias '{inp}' already exists, skip (no overwrite)"}
        
        # 只追加
        learned[inp] = target
        save_learned(learned)
        
        # 记录事件
        log_event("suggestion_applied", "apply_suggestions", 
                  f"AUTO: alias '{inp}' → '{target}'", suggestion)
        
        return {"applied": True, "action": "alias_append", "input": inp, "target": target}
    
    return {"applied": False, "reason": f"unknown safe type: {stype}"}


def run(mode: str = "show") -> dict:
    """
    mode:
      show  - 展示所有建议，标记哪些可自动/需人工
      auto  - 自动应用安全建议，危险建议存入 pending
      force - 人工确认后应用 pending 中的指定建议
    """
    suggestions = load_suggestions()
    
    if not suggestions:
        print("No pending suggestions.")
        return {"applied": 0, "pending": 0}
    
    if mode == "show":
        print(f"=== {len(suggestions)} Suggestions ===\n")
        for i, s in enumerate(suggestions, 1):
            safe = _is_safe(s)
            tag = "✅ AUTO" if safe else "⏳ NEEDS REVIEW"
            print(f"  {i}. [{tag}] [{s.get('severity','?')}] {s.get('reason','?')}")
        return {"total": len(suggestions)}
    
    elif mode == "auto":
        applied = []
        pending = []
        
        for s in suggestions:
            if _is_safe(s):
                result = apply_safe(s)
                if result.get("applied"):
                    applied.append({"suggestion": s, "result": result})
                    print(f"  ✅ APPLIED: {s.get('reason','?')}")
                else:
                    pending.append(s)
                    print(f"  ⏭️ SKIPPED: {result.get('reason','?')}")
            else:
                pending.append(s)
                print(f"  ⏳ PENDING: {s.get('reason','?')} (needs human review)")
        
        # 更新 suggestions.json（清空已应用的）
        SUGGESTIONS_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 写入 pending_review.json
        if pending:
            PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
        
        summary = {"applied": len(applied), "pending": len(pending)}
        print(f"\nApplied: {summary['applied']}, Pending review: {summary['pending']}")
        return summary
    
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: apply_suggestions.py [show|auto]")
        return {}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "show"
    run(mode)
