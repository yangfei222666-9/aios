"""
Debate vs Vote 动态切换器
基于 NeurIPS 2025 "Debate or Vote" 论文思路
规则：
  - 信号冲突度高 / 不确定性高 → debate（对抗辩论，挖掘分歧）
  - 信号收敛 / 不确定性低   → vote（多数投票，快速收敛）
  - mode_hint != auto        → 尊重显式指定
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

ModeType = Literal["debate", "vote"]

# ── 阈值配置（可外部覆盖）──────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "uncertainty_debate_threshold": 0.55,   # 不确定性 > 此值 → debate
    "convergence_vote_threshold": 0.60,     # 收敛性   > 此值 → vote（降低阈值）
    "confidence_floor": 0.55,               # 低于此值 → neutral/no_trade
    "min_risk_flags": 2,                    # 最少风险标记数
}

# 高不确定性关键词
UNCERTAINTY_KEYWORDS = {
    "conflicting", "mixed", "unclear", "uncertain", "diverging",
    "range_break_attempt", "reversal", "volatile", "choppy",
}

# 高收敛性关键词
CONVERGENCE_KEYWORDS = {
    "trend_continuation", "aligned", "confirmed", "strong_trend",
    "breakout_confirmed", "momentum", "sector_strength",
}


@dataclass
class SelectionResult:
    mode: ModeType
    uncertainty_score: float
    convergence_score: float
    reason: str
    overridden_by_hint: bool = False


def compute_uncertainty(signals: list[str], market_state: str) -> float:
    """
    计算不确定性分数 [0, 1]
    - 信号数量越多且方向混杂，分数越高
    - market_state 含高不确定性关键词，加权
    """
    score = 0.0
    total = max(len(signals), 1)

    # 信号层：含对立词对（up/down, bull/bear, high/low）
    bull_signals = sum(1 for s in signals if any(k in s.lower() for k in
                       ["up", "bull", "long", "strength", "tailwind", "higher"]))
    bear_signals = sum(1 for s in signals if any(k in s.lower() for k in
                       ["down", "bear", "short", "weak", "headwind", "lower"]))
    neutral_signals = total - bull_signals - bear_signals

    conflict_ratio = min(bull_signals, bear_signals) / total
    score += conflict_ratio * 0.5

    # neutral 信号越多，不确定性越高
    score += (neutral_signals / total) * 0.2

    # market_state 层
    state_lower = market_state.lower().replace("_", " ")
    if any(k in state_lower for k in UNCERTAINTY_KEYWORDS):
        score += 0.3

    return min(score, 1.0)


def compute_convergence(signals: list[str], market_state: str) -> float:
    """
    计算收敛性分数 [0, 1]
    - 信号方向一致性越高，分数越高
    """
    score = 0.0
    total = max(len(signals), 1)

    bull_signals = sum(1 for s in signals if any(k in s.lower() for k in
                       ["up", "bull", "long", "strength", "tailwind", "higher", "aligned",
                        "momentum", "breakout", "continuation"]))
    bear_signals = sum(1 for s in signals if any(k in s.lower() for k in
                       ["down", "bear", "short", "weak", "headwind", "lower"]))

    dominant = max(bull_signals, bear_signals)
    score += (dominant / total) * 0.6

    state_lower = market_state.lower().replace("_", " ")
    if any(k in state_lower for k in CONVERGENCE_KEYWORDS):
        score += 0.4

    return min(score, 1.0)


def select_mode(
    signals: list[str],
    market_state: str,
    mode_hint: str = "auto",
    config: dict | None = None,
) -> SelectionResult:
    """
    主入口：根据信号和市场状态选择 debate 或 vote 模式。

    Args:
        signals:      key_signals 列表
        market_state: 市场状态字符串
        mode_hint:    "auto" | "debate" | "vote"
        config:       覆盖默认阈值

    Returns:
        SelectionResult
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}

    uncertainty = compute_uncertainty(signals, market_state)
    convergence = compute_convergence(signals, market_state)

    # 显式 hint 优先
    if mode_hint in ("debate", "vote"):
        return SelectionResult(
            mode=mode_hint,
            uncertainty_score=round(uncertainty, 3),
            convergence_score=round(convergence, 3),
            reason=f"mode_hint='{mode_hint}' explicitly set",
            overridden_by_hint=True,
        )

    # 自动选择
    if uncertainty >= cfg["uncertainty_debate_threshold"]:
        mode: ModeType = "debate"
        reason = (
            f"uncertainty={uncertainty:.2f} >= threshold={cfg['uncertainty_debate_threshold']} "
            f"→ signals conflicting, debate needed"
        )
    elif convergence >= cfg["convergence_vote_threshold"]:
        mode = "vote"
        reason = (
            f"convergence={convergence:.2f} >= threshold={cfg['convergence_vote_threshold']} "
            f"→ signals aligned, vote sufficient"
        )
    else:
        # 默认保守：debate
        mode = "debate"
        reason = (
            f"uncertainty={uncertainty:.2f}, convergence={convergence:.2f} "
            f"→ ambiguous, defaulting to debate (conservative)"
        )

    return SelectionResult(
        mode=mode,
        uncertainty_score=round(uncertainty, 3),
        convergence_score=round(convergence, 3),
        reason=reason,
    )


# ── CLI 快速测试 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cases = [
        {
            "label": "BTC range_break_attempt (auto)",
            "signals": ["volume_up", "funding_neutral", "resistance_near"],
            "market_state": "range_break_attempt",
            "mode_hint": "auto",
        },
        {
            "label": "AAPL trend_continuation (vote hint)",
            "signals": ["higher_lows", "earnings_tailwind", "sector_strength"],
            "market_state": "trend_continuation",
            "mode_hint": "vote",
        },
        {
            "label": "ETH mixed signals (auto)",
            "signals": ["volume_down", "bull_divergence", "bear_cross", "funding_high"],
            "market_state": "volatile",
            "mode_hint": "auto",
        },
        {
            "label": "SPY strong trend (auto)",
            "signals": ["ma_aligned", "sector_strength", "higher_lows", "momentum"],
            "market_state": "trend_continuation",
            "mode_hint": "auto",
        },
    ]

    print("=" * 60)
    print("Debate vs Vote Selector — Test Cases")
    print("=" * 60)
    for c in cases:
        r = select_mode(c["signals"], c["market_state"], c["mode_hint"])
        hint_tag = " [hint override]" if r.overridden_by_hint else ""
        print(f"\n[{c['label']}]")
        print(f"  mode     : {r.mode.upper()}{hint_tag}")
        print(f"  uncertainty: {r.uncertainty_score}  convergence: {r.convergence_score}")
        print(f"  reason   : {r.reason}")
    print("\n" + "=" * 60)
