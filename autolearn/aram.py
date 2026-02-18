from __future__ import annotations
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# Ensure autolearn is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

# --- Autolearn integration ---
try:
    from core.executor import run as autolearn_run
except Exception:
    autolearn_run = None

try:
    from core.retest import run as autolearn_retest
except Exception:
    autolearn_retest = None

from aram.modules.env_check import env_check
from aram.modules.reporter import write_report

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)
ARAM_DIR = Path(r"C:\Users\A\Desktop\ARAM-Helper")


def now_iso():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _tooling_status():
    return {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "root": str(ROOT),
        "has_autolearn_executor": bool(autolearn_run),
        "has_autolearn_retest": bool(autolearn_retest),
    }


# -------------------- ARAM core steps (v0.1) --------------------

def step_build(intent, payload):
    """构建/刷新 172 英雄数据库"""
    ok, detail = env_check()
    if not ok:
        return {"ok": False, "error": f"env_check failed: {json.dumps(detail, ensure_ascii=False)}"}

    r = subprocess.run(
        [sys.executable, str(ARAM_DIR / "fetch_real_data.py")],
        capture_output=True, text=True, timeout=120,
        cwd=str(ARAM_DIR), encoding="utf-8", errors="replace"
    )
    if r.returncode == 0:
        return {"ok": True, "result": f"build ok — {r.stdout[-300:].strip()}"}
    return {"ok": False, "error": r.stderr[-300:].strip() or f"exit {r.returncode}"}


def step_update(intent, payload):
    """检查数据质量"""
    data_file = ARAM_DIR / "aram_data.json"
    if not data_file.exists():
        return {"ok": False, "error": "aram_data.json not found"}

    data = json.loads(data_file.read_text(encoding="utf-8"))
    total = len(data) if isinstance(data, list) else len(data)
    items = data if isinstance(data, list) else list(data.values())
    empty = sum(1 for c in items if isinstance(c, dict) and not (c.get("builds") or c.get("items") or c.get("recommended_items")))
    coverage = ((total - empty) / total * 100) if total > 0 else 0

    if coverage < 80:
        return {"ok": False, "error": f"Coverage {coverage:.1f}% ({empty} missing)"}
    return {"ok": True, "result": f"update check ok — {total} champions, {coverage:.1f}% coverage"}


def step_report(intent, payload):
    """report 步骤本身只是标记"""
    return {"ok": True, "result": "report generated"}


def _run_with_autolearn(intent, tool, payload, do_task):
    if autolearn_run:
        return autolearn_run(intent=intent, tool=tool, payload=payload, do_task=do_task)
    return do_task(intent, payload)


def _smoke():
    if autolearn_retest:
        return autolearn_retest(level="smoke")
    return {"ok": False, "error": "autolearn retest not available"}


def run_command(cmd):
    run_id = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    base = {
        "run_id": run_id,
        "ts": now_iso(),
        "cmd": cmd,
        "tooling": _tooling_status(),
    }
    steps = []
    smoke = None

    # 1) env check
    ok, env_detail = env_check()
    steps.append({"name": "env_check", "ok": ok, "detail": env_detail})
    if not ok:
        out_path = REPORT_DIR / "latest.md"
        write_report(out_path, base, steps, smoke)
        return 1

    # 2) main step
    if cmd == "build":
        out = _run_with_autolearn("aram_build", "fetch_real_data", {}, step_build)
        steps.append({"name": "build", **out})
        if not out.get("ok"):
            smoke = _smoke()

    elif cmd == "update":
        out = _run_with_autolearn("aram_update", "aram_data", {}, step_update)
        steps.append({"name": "update", **out})
        if not out.get("ok"):
            smoke = _smoke()

    elif cmd == "report":
        out = _run_with_autolearn("aram_report", "reporter", {}, step_report)
        steps.append({"name": "report", **out})

    elif cmd == "status":
        steps.append({"name": "status", "ok": True, "detail": _tooling_status()})

    else:
        print(f"Unknown command: {cmd}")
        return 1

    # 3) write report
    out_path = REPORT_DIR / "latest.md"
    write_report(out_path, base, steps, smoke)
    print(f"\n[ARAM] report: {out_path}")
    return 0 if all(s.get("ok") for s in steps if s["name"] != "status") else 2


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(
        prog="aram",
        description="ARAM v0.1 — build/update/report + autolearn integration"
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("build", "update", "report", "status"):
        sub.add_parser(name)
    args = p.parse_args(argv)
    return run_command(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
