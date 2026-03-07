"""Manifest → Runtime Config 适配器。

to_runtime_config(manifest) 接收 normalize_manifest 的输出，
转换为当前执行器已有的配置结构，不改现有接口。
"""

from __future__ import annotations
from typing import Any


def to_runtime_config(manifest: dict) -> dict:
    """将归一化 manifest 转为执行器运行时配置。

    Args:
        manifest: normalize_manifest() 的返回值。

    Returns:
        执行器可直接消费的 config dict，结构兼容现有调用路径。
        新增字段仅作为观测/日志用途，不影响旧逻辑。
    """
    meta = manifest.get("meta", {})
    decision = manifest.get("decision", {})
    risk = manifest.get("risk", {})
    runtime = manifest.get("runtime", {})

    # ── 基础配置（与现有执行器接口一致）────────────────────
    config: dict[str, Any] = {
        "name": meta.get("name", ""),
        "version": meta.get("version", ""),
        "confidence": decision.get("confidence"),
    }

    # 透传 runtime 段的所有字段
    config.update(runtime)

    # ── 新增透传（仅日志/观测，旧调用路径不感知）──────────
    if decision.get("selected_mode"):
        config["selected_mode"] = decision["selected_mode"]

    mode_hint = decision.get("mode_hint") or runtime.get("mode_hint")
    if mode_hint:
        config["mode_hint"] = mode_hint

    # risk 指标透传（观测用）
    if risk.get("uncertainty_score") is not None:
        config["_obs_uncertainty_score"] = risk["uncertainty_score"]
    if risk.get("convergence_score") is not None:
        config["_obs_convergence_score"] = risk["convergence_score"]

    return config
