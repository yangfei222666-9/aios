# aios/__main__.py - 统一 CLI 入口
"""
python -m aios <command> [args]

Commands:
  health              健康检查 (pass/warn/fail)
  analyze             跑学习器，生成 suggestions + report
  apply               只应用 L1 (alias)
  report              输出 daily_report
  replay --since <h>  回放验证
  tickets             列出 L2 工单 (open/done)
  score               evolution_score
  test                跑回归测试
  version             版本信息
"""
import sys, json, os

AIOS_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AIOS_ROOT)


def cmd_health():
    from core.engine import load_events
    from core.config import load, get_path
    from learning.baseline import evolution_score

    issues = []

    # config
    cfg = load()
    if not cfg:
        issues.append(("FAIL", "config.yaml empty or missing"))
    else:
        issues.append(("PASS", f"config: {len(cfg)} keys"))

    # events file
    ep = get_path("paths.events")
    if ep and ep.exists():
        events = load_events(days=1)
        issues.append(("PASS", f"events: {len(events)} (24h)"))
    else:
        issues.append(("WARN", "no events yet"))

    # aram data
    from pathlib import Path
    aram = Path(r"C:\Users\A\Desktop\ARAM-Helper\aram_data.json")
    if aram.exists():
        import json as j
        data = j.loads(aram.read_text(encoding="utf-8"))
        issues.append(("PASS", f"aram_data: {len(data)} champions"))
    else:
        issues.append(("WARN", "aram_data.json not found"))

    # evolution score
    evo = evolution_score()
    grade = evo.get("grade", "N/A")
    score = evo.get("score", 0)
    if grade in ("healthy", "ok"):
        issues.append(("PASS", f"evolution: {score} ({grade})"))
    elif grade == "N/A":
        issues.append(("WARN", "evolution: no baseline data"))
    else:
        issues.append(("FAIL", f"evolution: {score} ({grade})"))

    # output
    has_fail = any(s == "FAIL" for s, _ in issues)
    has_warn = any(s == "WARN" for s, _ in issues)

    for status, msg in issues:
        icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
        print(f"  {icon} {msg}")

    if has_fail:
        print("\nHealth: FAIL")
        return 1
    elif has_warn:
        print("\nHealth: WARN")
        return 0
    else:
        print("\nHealth: PASS")
        return 0


def cmd_analyze(days=7):
    from learning.analyze import generate_full_report
    r = generate_full_report(days)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_apply():
    from learning.apply import run
    run(mode="auto")


def cmd_report(days=1):
    from learning.analyze import generate_daily_report
    print(generate_daily_report(days))


def cmd_replay(since_hours=24):
    import time
    from scripts.replay import replay
    now = int(time.time())
    r = replay(now - since_hours * 3600, now)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_tickets():
    from learning.tickets import summary
    print(summary())


def cmd_score():
    from learning.baseline import evolution_score
    print(json.dumps(evolution_score(), ensure_ascii=False, indent=2))


def cmd_gate():
    from learning.baseline import regression_gate
    r = regression_gate()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r.get("alerts"):
        return 1
    return 0


def cmd_test():
    import subprocess
    suite = os.path.join(AIOS_ROOT, "scripts", "run_regression_suite.py")
    r = subprocess.run([sys.executable, suite])
    return r.returncode


def cmd_version():
    from learning.analyze import AIOS_VERSION, _get_git_commit
    print(f"AIOS {AIOS_VERSION} (commit: {_get_git_commit()})")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip())
        return

    cmd = args[0]

    if cmd == "health":
        sys.exit(cmd_health())
    elif cmd == "analyze":
        days = int(args[1]) if len(args) > 1 else 7
        cmd_analyze(days)
    elif cmd == "apply":
        cmd_apply()
    elif cmd == "report":
        days = int(args[1]) if len(args) > 1 else 1
        cmd_report(days)
    elif cmd == "replay":
        since = 24
        if "--since" in args:
            idx = args.index("--since")
            if idx + 1 < len(args):
                since = int(args[idx + 1])
        cmd_replay(since)
    elif cmd == "tickets":
        cmd_tickets()
    elif cmd == "score":
        cmd_score()
    elif cmd == "gate":
        sys.exit(cmd_gate())
    elif cmd == "test":
        sys.exit(cmd_test())
    elif cmd == "version":
        cmd_version()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__.strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
