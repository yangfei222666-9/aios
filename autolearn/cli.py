# cli.py - autolearn CLI (v1.0)
"""
Usage:
  python -m autolearn retest [smoke|regression|full]
  python -m autolearn report [days]
  python -m autolearn proposals [window_hours]
  python -m autolearn triage
  python -m autolearn health
  python -m autolearn version
"""
import sys, os
from pathlib import Path


def main(argv=None):
    args = (argv or sys.argv)[1:]
    cmd = args[0] if args else "help"

    if cmd == "retest":
        from core.retest import run
        level = args[1] if len(args) > 1 else "smoke"
        result = run(level)
        sys.exit(0 if result["ok"] else 1)

    elif cmd == "report":
        from core.weekly_report import save_report
        days = int(args[1]) if len(args) > 1 else 7
        save_report(days)

    elif cmd == "proposals":
        from core.proposals import write_proposals
        hours = int(args[1]) if len(args) > 1 else 72
        write_proposals(hours)

    elif cmd == "triage":
        triage_path = Path(__file__).parent / "scripts" / "triage.py"
        if triage_path.exists():
            os.system(f'"{sys.executable}" "{triage_path}"')
        else:
            print("scripts/triage.py not found")

    elif cmd == "version":
        from core.version import MODULE_VERSION, SCHEMA_VERSION
        print(f"autolearn v{MODULE_VERSION} (schema {SCHEMA_VERSION})")

    elif cmd == "health":
        from core.retest import run
        result = run("smoke")
        print("\nSystem healthy." if result["ok"] else f"\nIssues: {result['failed']} failed.")
        sys.exit(0 if result["ok"] else 1)

    else:
        print("""autolearn v1.0 - Self-learning system for OpenClaw

Commands:
  retest [smoke|regression|full]  Run tests (default: smoke)
  report [days]                   Generate weekly report (default: 7)
  proposals [hours]               Generate proposals (default: 72h window)
  triage                          Process inbox.md pending entries
  health                          Quick health check (= retest smoke)
  version                         Show version info
""")
