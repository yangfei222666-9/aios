# aram/modules/reporter.py - 报告生成器
import time
from pathlib import Path


def write_report(out_path: Path, base: dict, steps: list, smoke: dict = None):
    """生成 markdown 报告"""
    lines = [
        f"# ARAM v0.1 Report",
        f"Run: {base.get('run_id', '?')} | {base.get('ts', '?')}",
        f"Command: `{base.get('cmd', '?')}`\n",
    ]

    # Tooling
    tooling = base.get("tooling", {})
    if tooling:
        lines.append("## Environment")
        for k, v in tooling.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    # Steps
    lines.append("## Steps")
    all_ok = True
    for s in steps:
        name = s.get("name", "?")
        ok = s.get("ok", False)
        icon = "PASS" if ok else "FAIL"
        lines.append(f"- [{icon}] {name}")

        if not ok:
            all_ok = False

        # detail
        detail = s.get("detail") or s.get("result") or s.get("error")
        if detail:
            if isinstance(detail, dict):
                for dk, dv in detail.items():
                    lines.append(f"  - {dk}: {dv}")
            else:
                lines.append(f"  - {detail}")

        # tips from autolearn
        tips = s.get("tips")
        if tips:
            lines.append(f"  - Autolearn tips ({len(tips)}):")
            for t in tips[:3]:
                lines.append(f"    - [{t.get('status','?')}] {t.get('title','?')}: {t.get('solution','?')}")

        # tripped
        if s.get("tripped"):
            lines.append(f"  - CIRCUIT BREAKER TRIPPED")

    lines.append("")

    # Smoke
    if smoke:
        lines.append("## Smoke Test (post-failure)")
        lines.append(f"- Passed: {smoke.get('passed', '?')}")
        lines.append(f"- Failed: {smoke.get('failed', '?')}")
        lines.append(f"- Status: {'PASS' if smoke.get('ok') else 'FAIL'}")
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append(f"- Overall: {'ALL PASS' if all_ok else 'ISSUES FOUND'}")
    lines.append(f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    report = "\n".join(lines)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    return report
