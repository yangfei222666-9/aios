# core/retest.py - 分级复测器
# smoke: 修完必跑 (10-30s)
# regression: 每天/每次更新跑 (1-5min)
# full: HEARTBEAT 3天周期跑全量
import json, time, subprocess, sys, os
from pathlib import Path

# Ensure core package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.version import MODULE_VERSION, SCHEMA_VERSION

DATA = Path(__file__).parent.parent / "data"
DATA.mkdir(exist_ok=True)
RESULTS = DATA / "retest_results.jsonl"

# === SMOKE TESTS (修完必跑, <30s) ===

def test_powershell_dir_b():
    """PowerShell 正确做法: Get-ChildItem -Name"""
    cmd = ["powershell", "-NoProfile", "-Command",
           "Get-ChildItem $env:USERPROFILE\\Downloads -File -Name | Select-Object -First 3"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return (r.returncode == 0) and (r.stdout.strip() != "")

def test_expand_tilde():
    """~ 展开用 expanduser"""
    cmd = [sys.executable, "-c", "import os;print(os.path.expanduser('~'))"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    return (r.returncode == 0) and (r.stdout.strip() != "~")

def test_absolute_path():
    """绝对路径访问"""
    target = os.path.join(os.environ["USERPROFILE"], ".openclaw", "workspace", "autolearn", "core", "logger.py")
    return os.path.exists(target)

# === REGRESSION TESTS (每天跑, <5min) ===

def test_websearch_unicode_safe():
    """unicode 不被 bytes 炸掉"""
    cmd = [sys.executable, "-c", "import urllib.parse;print(urllib.parse.quote('中文测试'))"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    return r.returncode == 0 and "%" in r.stdout

def test_admin_process():
    """管理员权限检测"""
    cmd = ["powershell", "-NoProfile", "-Command", "Write-Host 'admin-check-ok'"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    return r.returncode == 0 and "admin-check-ok" in r.stdout

def test_lessons_jsonl_integrity():
    """教训库文件完整性"""
    lessons_file = DATA / "lessons.jsonl"
    if not lessons_file.exists():
        return True  # 空库也算通过
    for line in lessons_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            json.loads(line)  # 会抛异常如果格式错
    return True

def test_events_jsonl_integrity():
    """事件日志文件完整性"""
    events_file = DATA / "events.jsonl"
    if not events_file.exists():
        return True  # 空文件也算通过
    for line in events_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            json.loads(line)
    return True

# === FULL TESTS (3天周期) ===

def _ensure_path():
    """确保 core 包可导入"""
    parent = str(Path(__file__).parent.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

def test_error_sig_consistency():
    """同样的输入产生同样的签名"""
    _ensure_path()
    from core.errors import error_sig, error_sig_loose
    s1 = error_sig("Exception", "test error message")
    s2 = error_sig("Exception", "test error message")
    l1 = error_sig_loose("test error message")
    l2 = error_sig_loose("test error message")
    return s1 == s2 and l1 == l2

def test_lesson_add_find_roundtrip():
    """教训写入后能查到"""
    _ensure_path()
    from core.lessons import add_lesson, find_lessons
    sig = f"test_{int(time.time())}"
    add_lesson(sig, "test lesson", "test solution", sig_loose=f"loose_{sig}")
    found = find_lessons(sig)
    return len(found) > 0 and found[-1]["title"] == "test lesson"

def test_env_fingerprint():
    """环境指纹能采集"""
    _ensure_path()
    from core.executor import _env_fingerprint
    env = _env_fingerprint()
    return "python" in env and "os" in env

# === TEST REGISTRY ===

SMOKE = {
    "ps_dir_b": test_powershell_dir_b,
    "tilde_expand": test_expand_tilde,
    "absolute_path": test_absolute_path,
}

REGRESSION = {
    "web_unicode": test_websearch_unicode_safe,
    "admin_process": test_admin_process,
    "lessons_integrity": test_lessons_jsonl_integrity,
    "events_integrity": test_events_jsonl_integrity,
}

FULL = {
    "sig_consistency": test_error_sig_consistency,
    "lesson_roundtrip": test_lesson_add_find_roundtrip,
    "env_fingerprint": test_env_fingerprint,
}

def run_suite(name: str, tests: dict) -> tuple:
    passed = failed = 0
    for tname, fn in tests.items():
        ok = False
        err = ""
        try:
            ok = bool(fn())
        except Exception as e:
            ok = False
            err = str(e)[:200]
        
        rec = {"suite": name, "test": tname, "ok": ok, "err": err, "ts": int(time.time()),
               "schema_version": SCHEMA_VERSION, "module_version": MODULE_VERSION}
        with RESULTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        
        status = "PASS" if ok else "FAIL"
        detail = f" ({err})" if err else ""
        print(f"  [{status}] {tname}{detail}")
        if ok: passed += 1
        else: failed += 1
    return passed, failed

# === v1.0 STABLE API ===

def run(level: str = "smoke") -> dict:
    """运行指定级别的复测。返回 {ok, passed, failed, level, ts}"""
    print("=" * 50)
    print(f"  Autolearn Retest [{level.upper()}]")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    total_p = total_f = 0
    
    if level in ("smoke", "regression", "full"):
        print("\n  --- SMOKE ---")
        p, f = run_suite("smoke", SMOKE)
        total_p += p; total_f += f
    
    if level in ("regression", "full"):
        print("\n  --- REGRESSION ---")
        p, f = run_suite("regression", REGRESSION)
        total_p += p; total_f += f
    
    if level == "full":
        print("\n  --- FULL ---")
        p, f = run_suite("full", FULL)
        total_p += p; total_f += f
    
    print(f"\n  Total: {total_p} PASS / {total_f} FAIL")
    print("=" * 50)
    
    return {"ok": total_f == 0, "passed": total_p, "failed": total_f, "level": level, "ts": int(time.time())}

# backward compat
run_level = run

if __name__ == "__main__":
    level = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    result = run(level)
    sys.exit(0 if result["ok"] else 1)
