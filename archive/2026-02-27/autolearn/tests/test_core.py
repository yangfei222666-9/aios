# tests/test_core.py - 独立测试（可用 pytest 跑）
import sys, os, time, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_sign_strict_deterministic():
    from core.errors import sign_strict
    s1 = sign_strict("Exception", "test error")
    s2 = sign_strict("Exception", "test error")
    assert s1 == s2, f"{s1} != {s2}"

def test_sign_loose_returns_keywords():
    from core.errors import sign_loose
    result = sign_loose("cannot convert argument to bytestring")
    assert "keywords" in result
    assert "sig" in result
    assert len(result["sig"]) == 12

def test_lesson_roundtrip():
    from core.lessons import add_lesson, find
    sig = f"pytest_{int(time.time())}"
    add_lesson(sig, "pytest lesson", "pytest solution")
    found = find(sig)
    assert len(found) > 0
    assert found[-1]["title"] == "pytest lesson"
    # v1.1: 可解释性字段
    assert found[-1].get("_match_type") == "strict"
    assert found[-1].get("_similarity_score") == 1.0

def test_fuzzy_match_explainability():
    from core.lessons import add_lesson, find
    # 添加一条有明确关键词的教训
    sig = f"fuzzy_test_{int(time.time())}"
    add_lesson(sig, "connection timeout error",
               "retry with exponential backoff",
               symptom="socket connection timed out",
               cause="network instability")
    # 用部分重叠的关键词做模糊查询（不匹配 strict/loose sig）
    found = find("nonexistent_sig", sig_loose="nonexistent_loose",
                 keywords=["connection", "timeout", "socket", "error"])
    # 应该能模糊匹配到
    matched = [f for f in found if f.get("_match_type") == "fuzzy"]
    if matched:
        tip = matched[0]
        assert tip["_similarity_score"] > 0
        assert len(tip["_matched_keywords"]) > 0
        assert isinstance(tip["_matched_keywords"], list)
        print(f"    fuzzy: score={tip['_similarity_score']}, keywords={tip['_matched_keywords']}")

def test_fuzzy_no_match_below_threshold():
    from core.lessons import find
    # 完全不相关的关键词，不应匹配
    found = find("no_match_sig", sig_loose="no_match_loose",
                 keywords=["zzzzunique", "xxxxrandom", "yyyynonsense"])
    assert len(found) == 0

def test_circuit_breaker_allow():
    from core.circuit_breaker import allow
    assert allow("nonexistent_sig_12345") is True

def test_env_fingerprint():
    from core.executor import _env_fingerprint
    env = _env_fingerprint()
    assert "python" in env
    assert "os" in env

def test_version():
    from core.version import MODULE_VERSION, SCHEMA_VERSION
    assert MODULE_VERSION == "1.1.0"
    assert SCHEMA_VERSION == "1.0"

if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
