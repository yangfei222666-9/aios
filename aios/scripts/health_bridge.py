# aios/scripts/health_bridge.py - 运行 health_check 并记录到事件总线
"""
运行 health_check.ps1 → 解析结果 → 写入 events.jsonl
"""
import subprocess, sys, re, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.log_event import log_event

HEALTH_SCRIPT = Path(r"C:\Users\A\.openclaw\workspace\scripts\health_check.ps1")


def run_health_check() -> dict:
    """运行 health_check 并解析结果"""
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HEALTH_SCRIPT)],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    
    output = r.stdout
    checks = {}
    passed = failed = warned = 0
    
    for line in output.splitlines():
        m = re.match(r'\[(OK|FAIL|WARN)\]\s+(.+?)\s+-\s+(.+)', line)
        if m:
            status, name, detail = m.groups()
            checks[name] = {"status": status, "detail": detail.strip()}
            if status == "OK": passed += 1
            elif status == "FAIL": failed += 1
            elif status == "WARN": warned += 1
    
    ok = failed == 0
    summary = {
        "ok": ok,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "checks": checks,
    }
    
    # → aios 事件
    log_event("health", "health_check.ps1", f"{'PASS' if ok else 'FAIL'} ({passed}P/{failed}F/{warned}W)", summary)
    
    return summary


if __name__ == "__main__":
    import json
    result = run_health_check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
