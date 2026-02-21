# tg-gateway/router.py - 快车道/慢车道路由判断
"""
判断消息走快车道（本地执行）还是慢车道（OpenClaw LLM）。
"""
import sys
from pathlib import Path

# 加载 aios 的 app_alias
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "aios"))
from core.app_alias import resolve, needs_confirmation, RISK_LEVELS

from config import FAST_TRACK_PREFIXES


def classify(text: str) -> dict:
    """
    分类消息：
    返回:
    {
        "track": "fast" | "slow",
        "resolve_result": {...} | None,  # 快车道时有值
    }
    """
    text = text.strip()
    if not text:
        return {"track": "slow", "resolve_result": None}

    # 检查是否以快车道前缀开头
    for prefix in FAST_TRACK_PREFIXES:
        if text.startswith(prefix):
            result = resolve(text)
            # 只有匹配到已知应用 + 低风险才走快车道
            if result["matched"] and result["risk"] == "low":
                return {"track": "fast", "resolve_result": result}
            # 高风险命令走慢车道（让 LLM 确认）
            if result["risk"] == "high":
                return {"track": "slow", "resolve_result": result}
            # 未匹配的命令也走慢车道
            break

    return {"track": "slow", "resolve_result": None}
