# aios/__main__.py - 统一 CLI 入口 (argparse)
from __future__ import annotations
import argparse
import json
import sys
import os

AIOS_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AIOS_ROOT)


def cmd_health(args) -> int:
    from core.engine import load_events
    from core.config import load, get_path
    from learning.baseline import evolution_score

    issues = []

    cfg = load()
    if not cfg:
        issues.append(("FAIL", "config.yaml empty or missing"))
    else:
        issues.append(("PASS", f"config: {len(cfg)} keys"))

    ep = get_path("paths.events")
    if ep and ep.exists():
        events = load_events(days=1)
        issues.append(("PASS", f"events: {len(events)} (24h)"))
    else:
        issues.append(("WARN", "no events yet"))

    from pathlib import Path
    aram = Path(r"C:\Users\A\Desktop\ARAM-Helper\aram_data.json")
    if aram.exists():
        data = json.loads(aram.read_text(encoding="utf-8"))
        issues.append(("PASS", f"aram_data: {len(data)} champions"))
    else:
        issues.append(("WARN", "aram_data.json not found"))

    evo = evolution_score()
    grade = evo.get("grade", "N/A")
    score = evo.get("score", 0)
    if grade in ("healthy", "ok"):
        issues.append(("PASS", f"evolution: {score} ({grade})"))
    elif grade == "N/A":
        issues.append(("WARN", "evolution: no baseline data"))
    else:
        issues.append(("FAIL", f"evolution: {score} ({grade})"))

    for status, msg in issues:
        icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
        print(f"  {icon} {msg}")

    has_fail = any(s == "FAIL" for s, _ in issues)
    has_warn = any(s == "WARN" for s, _ in issues)
    print(f"\nHealth: {'FAIL' if has_fail else 'WARN' if has_warn else 'PASS'}")
    return 1 if has_fail else 0


def _parse_since(since: str) -> int:
    """'24h' -> 1, '7d' -> 7, 'all' -> 365"""
    if since == "all":
        return 365
    if since.endswith("h"):
        return max(1, int(since[:-1]) // 24) or 1
    if since.endswith("d"):
        return int(since[:-1])
    return 1


def cmd_analyze(args) -> int:
    days = _parse_since(args.since)
    from learning.analyze import generate_full_report
    r = generate_full_report(days)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def cmd_report(args) -> int:
    days = _parse_since(args.since)
    from learning.analyze import generate_daily_report
    print(generate_daily_report(days))
    return 0


def cmd_apply(args) -> int:
    if args.dry_run:
        from learning.apply import run
        run(mode="show")
    else:
        from learning.apply import run
        run(mode="auto")
    return 0


def cmd_replay(args) -> int:
    import time
    hours = int(args.since.rstrip("h")) if args.since.endswith("h") else int(args.since.rstrip("d")) * 24
    from scripts.replay import replay
    now = int(time.time())
    r = replay(now - hours * 3600, now)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def cmd_tickets(args) -> int:
    from learning.tickets import load_tickets, summary
    if args.status == "all":
        for t in load_tickets():
            print(json.dumps(t, ensure_ascii=False))
    elif args.status in ("open", "done", "wontfix"):
        for t in load_tickets(status=args.status):
            print(json.dumps(t, ensure_ascii=False))
    else:
        print(summary())
    return 0


def cmd_score(args) -> int:
    from learning.baseline import evolution_score
    print(json.dumps(evolution_score(), ensure_ascii=False, indent=2))
    return 0


def cmd_gate(args) -> int:
    from learning.baseline import regression_gate
    r = regression_gate()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 1 if r.get("alerts") else 0


def cmd_test(args) -> int:
    import subprocess
    suite = os.path.join(AIOS_ROOT, "scripts", "run_regression_suite.py")
    return subprocess.call([sys.executable, suite])


def cmd_version(args) -> int:
    from learning.analyze import AIOS_VERSION, _get_git_commit
    print(f"AIOS {AIOS_VERSION} (commit: {_get_git_commit()})")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aios", description="AIOS — 个人 AI 操作系统")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("health", help="健康检查 (pass/warn/fail)")

    pa = sub.add_parser("analyze", help="跑学习器，生成 suggestions + report")
    pa.add_argument("--since", default="24h", help="时间窗口: 24h, 7d, all")

    pr = sub.add_parser("report", help="输出 daily report")
    pr.add_argument("--since", default="24h", help="时间窗口: 24h, 7d, all")

    pap = sub.add_parser("apply", help="应用 L1 建议 (alias)")
    pap.add_argument("--dry-run", action="store_true", help="只显示不应用")

    prel = sub.add_parser("replay", help="回放验证")
    prel.add_argument("--since", default="24h", help="回放窗口: 24h, 48h")

    pt = sub.add_parser("tickets", help="列出 L2 工单")
    pt.add_argument("--status", default="open", choices=["open", "done", "wontfix", "all"])

    sub.add_parser("score", help="evolution_score 进化评分")
    sub.add_parser("gate", help="门禁检测 (退化报警)")
    sub.add_parser("test", help="跑回归测试 (15 cases)")
    sub.add_parser("version", help="版本信息")

    args = p.parse_args(argv)

    if not args.cmd:
        p.print_help()
        return 0

    dispatch = {
        "health": cmd_health,
        "analyze": cmd_analyze,
        "report": cmd_report,
        "apply": cmd_apply,
        "replay": cmd_replay,
        "tickets": cmd_tickets,
        "score": cmd_score,
        "gate": cmd_gate,
        "test": cmd_test,
        "version": cmd_version,
    }

    return dispatch[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
