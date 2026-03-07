"""Manifest 兼容层 - 新旧字段归一化。

normalize_manifest(raw) 是唯一出口，下游只认它返回的结构。
"""

from __future__ import annotations
from typing import Any

# ── 必需顶层键 ──────────────────────────────────────────────
REQUIRED_KEYS = ("name", "version")

# ── 新旧键映射表（新字段优先，旧字段回退）────────────────────
# 格式: (canonical_key, preferred_source, fallback_source, default)
_FIELD_MAP: list[tuple[str, str, str | None, Any]] = [
    ("selected_mode",     "selected_mode",     "mode",             ""),
    ("mode_reason",       "mode_reason",       "reason",           ""),
    ("uncertainty_score", "uncertainty_score",  None,               None),
    ("convergence_score", "convergence_score",  None,               None),
]

# decision 段内的映射
_DECISION_FIELD_MAP: list[tuple[str, str, str | None, Any]] = [
    ("confidence", "confidence", "confidence_score", None),
]

# ── 已知顶层段 ──────────────────────────────────────────────
_KNOWN_SECTIONS = {
    "name", "version",
    "meta", "decision", "risk", "runtime",
    # 兼容旧键（会被映射走）
    "mode", "reason", "selected_mode", "mode_reason",
    "uncertainty_score", "convergence_score",
    "confidence_score",
}


def normalize_manifest(raw: dict) -> dict:
    """将任意版本的 manifest dict 归一化为统一结构。

    Returns:
        {
            "meta":     {"name": str, "version": str, ...},
            "decision": {"confidence": float|None, "selected_mode": str, "mode_reason": str, ...},
            "risk":     {"uncertainty_score": float|None, "convergence_score": float|None, ...},
            "runtime":  {... 透传},
            "extras":   {未识别字段},
        }

    Raises:
        ValueError: 缺少 name 或 version（错误码前缀: MANIFEST_SCHEMA_ERROR）。
    """
    if not isinstance(raw, dict):
        raise ValueError(f"MANIFEST_SCHEMA_ERROR: manifest must be a dict, got {type(raw).__name__}")

    # ── 1. 校验必需键 ───────────────────────────────────────
    missing = [k for k in REQUIRED_KEYS if k not in raw]
    if missing:
        raise ValueError(f"MANIFEST_SCHEMA_ERROR: manifest missing required keys: {', '.join(missing)}")

    # ── 2. meta 段 ──────────────────────────────────────────
    meta = dict(raw.get("meta") or {})
    meta.setdefault("name", raw["name"])
    meta.setdefault("version", raw["version"])

    # ── 3. decision 段 ──────────────────────────────────────
    decision = dict(raw.get("decision") or {})
    # decision 内部映射
    for canonical, preferred, fallback, default in _DECISION_FIELD_MAP:
        if preferred in decision:
            decision[canonical] = decision[preferred]
        elif fallback and fallback in decision:
            decision[canonical] = decision.pop(fallback)
        elif fallback and fallback in raw:
            decision[canonical] = raw[fallback]
        else:
            decision.setdefault(canonical, default)

    # 顶层字段映射到 decision
    for canonical, preferred, fallback, default in _FIELD_MAP:
        if canonical in ("uncertainty_score", "convergence_score"):
            continue  # 这些归 risk 段
        # 空字符串语义：明确设置为 "" 时不回退
        if preferred in raw:
            val = raw[preferred]
        elif fallback and fallback in raw:
            val = raw[fallback]
        else:
            val = default
        decision.setdefault(canonical, val)

    # ── 4. risk 段 ──────────────────────────────────────────
    risk = dict(raw.get("risk") or {})
    for canonical, preferred, fallback, default in _FIELD_MAP:
        if canonical not in ("uncertainty_score", "convergence_score"):
            continue
        val = raw.get(preferred)
        if val is None and fallback:
            val = raw.get(fallback)
        if val is None:
            val = default
        risk.setdefault(canonical, val)

    # ── 5. runtime 段（透传）─────────────────────────────────
    runtime = dict(raw.get("runtime") or {})

    # ── 6. extras（未识别字段，不丢弃）──────────────────────
    extras = {
        k: v for k, v in raw.items()
        if k not in _KNOWN_SECTIONS
    }

    return {
        "meta": meta,
        "decision": decision,
        "risk": risk,
        "runtime": runtime,
        "extras": extras,
    }
