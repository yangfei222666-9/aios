# SKILL.md

## metadata
- name: bull_bear_debate_decision
- version: 0.1.0
- owner: aios-core
- status: active
- tags: [decision, debate, vote, strategy, adversarial-validation]

## description

A decision skill that runs Bull vs Bear analysis, then chooses debate or vote mode
based on uncertainty and convergence signals, and outputs a final actionable decision
with rationale. Powered by AIOS Adversarial Validation System v1.0 + 64卦智慧调解。

## use_when
- You need a directional decision under uncertainty.
- You want transparent reasoning from opposing views.
- You need a structured final output (decision, confidence, risks, next steps).
- High-risk tasks require dual-validation before execution.

## do_not_use_when
- Input data is missing critical fields (price/time/context).
- A hard real-time response is required below system latency budget.
- The task requires external tool execution not enabled in current runtime.

## inputs
- symbol: string
  Example: BTC, AAPL
- timeframe: string
  Example: 1h, 4h, 1d
- context: object
  - market_state: string
  - key_signals: string[]
  - constraints: string[]
- mode_hint: string (optional)
  Allowed: auto, debate, vote
  Default: auto

## outputs
- decision: string
  Allowed: bullish, bearish, neutral, no_trade
- confidence: number
  Range: 0.0 - 1.0
- selected_mode: string
  Allowed: debate, vote
- rationale: string
- risk_flags: string[]
- next_actions: string[]
- hexagram: string
  Example: 坤卦 (No.2)

## policy
- If mode_hint != auto, respect explicit mode unless safety checks fail.
- In auto mode:
  - Use debate when signals are conflicting or uncertainty is high.
  - Use vote when opinions are converging and uncertainty is moderate/low.
- Always return at least 2 risk_flags.
- If confidence < 0.55, default to neutral or no_trade.
- 64卦调解：当前卦象自动融入最终裁决，调整风险系数。

## constraints
- No fabricated data.
- No hidden chain-of-thought exposure; provide concise rationale only.
- Keep output deterministic under same input + config.
- Respect configured risk limits and banned actions.
- Evolution Score < 50 时强制拒绝高危操作。

## procedure
1. Validate required inputs.
2. Build Bull and Bear argument sets from `context.key_signals`.
3. Compute uncertainty/convergence indicators.
4. Select `debate` or `vote` (or follow `mode_hint`).
5. 64卦调解：读取当前卦象，融合风险系数。
6. Produce final decision + confidence + risks + next actions.
7. Run safety/policy checks before returning.

## examples

### example_1
input:
```json
{
  "symbol": "BTC",
  "timeframe": "4h",
  "context": {
    "market_state": "range_break_attempt",
    "key_signals": ["volume_up", "funding_neutral", "resistance_near"],
    "constraints": ["max_drawdown_2pct"]
  },
  "mode_hint": "auto"
}
```
output:
```json
{
  "decision": "bullish",
  "confidence": 0.72,
  "selected_mode": "debate",
  "rationale": "Bull: volume confirms breakout intent. Bear: resistance overhead limits upside. 坤卦调解：厚积薄发，建议轻仓试探。",
  "risk_flags": ["resistance_near", "funding_neutral_may_flip"],
  "next_actions": ["enter_small_position", "set_stop_below_range"],
  "hexagram": "坤卦 (No.2)"
}
```

### example_2
input:
```json
{
  "symbol": "AAPL",
  "timeframe": "1d",
  "context": {
    "market_state": "trend_continuation",
    "key_signals": ["higher_lows", "earnings_tailwind", "sector_strength"],
    "constraints": ["long_only"]
  },
  "mode_hint": "vote"
}
```
output:
```json
{
  "decision": "bullish",
  "confidence": 0.74,
  "selected_mode": "vote",
  "rationale": "Signals are aligned across trend, fundamentals, and sector context. 既济卦：已成之势，顺势而为。",
  "risk_flags": ["gap_down_risk", "macro_event_risk"],
  "next_actions": ["scale_in_entries", "set_trailing_risk_control"],
  "hexagram": "既济卦 (No.63)"
}
```

## integration_notes
- Keep this file stable as interface contract for skill discovery.
- Map runtime parameters from your orchestrator config to inputs.
- Log `selected_mode`, `confidence`, and `decision` for weekly review.
- Mode selector: `aios/agent_system/debate_vote_selector.py`
- Core validator: `aios/agent_system/adversarial_validator.py`

## changelog
- 0.1.0 (2026-03-06): 初始版本，基于 Adversarial Validation System v1.0
