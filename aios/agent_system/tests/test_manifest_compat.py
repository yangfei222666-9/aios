"""Manifest 兼容层测试 - 4 个核心用例。"""

import sys, os, json, tempfile, pytest

# 确保 agent_system 在 path 上
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from manifest_schema import normalize_manifest
from manifest_loader import load_manifest_compat
from adapters.manifest_adapter import to_runtime_config


# ── 1. 新版 manifest（含 4 新字段）→ 正常加载 ──────────────
def test_new_manifest_full_fields():
    raw = {
        "name": "test-agent",
        "version": "2.0.0",
        "selected_mode": "fast",
        "mode_reason": "低复杂度任务",
        "uncertainty_score": 0.12,
        "convergence_score": 0.95,
        "decision": {"confidence": 0.88},
        "runtime": {"timeout": 60},
    }
    m = normalize_manifest(raw)

    assert m["meta"]["name"] == "test-agent"
    assert m["meta"]["version"] == "2.0.0"
    assert m["decision"]["selected_mode"] == "fast"
    assert m["decision"]["mode_reason"] == "低复杂度任务"
    assert m["decision"]["confidence"] == 0.88
    assert m["risk"]["uncertainty_score"] == 0.12
    assert m["risk"]["convergence_score"] == 0.95
    assert m["runtime"]["timeout"] == 60

    # 验证 to_runtime_config 透传
    cfg = to_runtime_config(m)
    assert cfg["name"] == "test-agent"
    assert cfg["confidence"] == 0.88
    assert cfg["selected_mode"] == "fast"
    assert cfg["timeout"] == 60
    assert cfg["_obs_uncertainty_score"] == 0.12
    assert cfg["_obs_convergence_score"] == 0.95


# ── 2. 旧版 manifest（无新字段）→ 默认值补齐 ───────────────
def test_old_manifest_defaults():
    raw = {
        "name": "legacy-agent",
        "version": "1.0.0",
        "mode": "slow",
        "reason": "高风险",
        "decision": {"confidence_score": 0.75},
    }
    m = normalize_manifest(raw)

    # 旧字段回退
    assert m["decision"]["selected_mode"] == "slow"
    assert m["decision"]["mode_reason"] == "高风险"
    assert m["decision"]["confidence"] == 0.75
    # 新字段默认 None
    assert m["risk"]["uncertainty_score"] is None
    assert m["risk"]["convergence_score"] is None

    # to_runtime_config 不暴露 None 观测字段
    cfg = to_runtime_config(m)
    assert cfg["confidence"] == 0.75
    assert "_obs_uncertainty_score" not in cfg
    assert "_obs_convergence_score" not in cfg


# ── 3. 混合字段（mode + selected_mode 同时存在）→ 新字段优先 ─
def test_mixed_fields_new_wins():
    raw = {
        "name": "mixed-agent",
        "version": "1.5.0",
        "mode": "slow",
        "selected_mode": "fast",
        "reason": "旧原因",
        "mode_reason": "新原因",
        "decision": {
            "confidence_score": 0.6,
            "confidence": 0.9,
        },
    }
    m = normalize_manifest(raw)

    assert m["decision"]["selected_mode"] == "fast"   # 新优先
    assert m["decision"]["mode_reason"] == "新原因"    # 新优先
    assert m["decision"]["confidence"] == 0.9          # 新优先


# ── 4. 非法 manifest（缺 name/version）→ 明确报错 ──────────
def test_invalid_manifest_missing_keys():
    with pytest.raises(ValueError, match="MANIFEST_SCHEMA_ERROR.*missing required keys.*name"):
        normalize_manifest({"version": "1.0.0"})

    with pytest.raises(ValueError, match="MANIFEST_SCHEMA_ERROR.*missing required keys.*version"):
        normalize_manifest({"name": "x"})

    with pytest.raises(ValueError, match="MANIFEST_SCHEMA_ERROR.*missing required keys"):
        normalize_manifest({})

    with pytest.raises(ValueError, match="MANIFEST_SCHEMA_ERROR.*must be a dict"):
        normalize_manifest("not a dict")


# ── 5. 空字符串不回退（明确语义）────────────────────────────
def test_empty_string_no_fallback():
    """selected_mode="" 时不回退到 mode（空字符串是明确设置）。"""
    raw = {
        "name": "test-agent",
        "version": "1.0.0",
        "selected_mode": "",  # 明确设置为空
        "mode": "vote",       # 不应被使用
    }
    m = normalize_manifest(raw)
    assert m["decision"]["selected_mode"] == ""  # 不回退到 "vote"

    # 对比：如果 selected_mode 不存在，才回退
    raw2 = {
        "name": "test-agent",
        "version": "1.0.0",
        "mode": "vote",
    }
    m2 = normalize_manifest(raw2)
    assert m2["decision"]["selected_mode"] == "vote"  # 回退成功


# ── 额外：load_manifest_compat 文件加载验证 ────────────────
def test_load_manifest_compat_from_file():
    raw = {
        "name": "file-agent",
        "version": "1.0.0",
        "selected_mode": "balanced",
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(raw, f, ensure_ascii=False)
        tmp_path = f.name

    try:
        m = load_manifest_compat(tmp_path)
        assert m["meta"]["name"] == "file-agent"
        assert m["decision"]["selected_mode"] == "balanced"
    finally:
        os.unlink(tmp_path)


def test_load_manifest_compat_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_manifest_compat("/nonexistent/path.json")
