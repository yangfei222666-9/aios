# scripts/ops_weekly.py - 运营期周报生成器
"""
每周生成运营期验收指标报告。

输出格式：
- Markdown（保存到 reports/ops_week_N.md）
- Telegram 精简版（直接输出）
"""
import json, sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from ops_metrics import load_metrics_history

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def generate_weekly_report(week_num: int = None) -> dict:
    """
    生成周报。
    
    week_num: 第几周（1-2），None = 自动判断
    """
    history = load_metrics_history(14)
    if not history:
        return {"error": "无数据"}
    
    # 自动判断周数
    if week_num is None:
        start_date = datetime.fromisoformat("2026-02-19")
        days_since_start = (datetime.now() - start_date).days
        week_num = (days_since_start // 7) + 1
    
    # 取本周数据
    week_data = history[-7:] if len(history) >= 7 else history
    
    report = {
        "week": week_num,
        "period": f"{week_data[0]['date']} ~ {week_data[-1]['date']}",
        "days_count": len(week_data),
        "metrics": {},
    }
    
    # MTTR
    mttr_vals = [m["mttr"].get("mttr_minutes") for m in week_data if m["mttr"].get("mttr_minutes") is not None]
    if mttr_vals:
        report["metrics"]["mttr"] = {
            "avg": round(sum(mttr_vals) / len(mttr_vals), 1),
            "min": round(min(mttr_vals), 1),
            "max": round(max(mttr_vals), 1),
            "trend": "↓" if len(mttr_vals) > 1 and mttr_vals[-1] < mttr_vals[0] else "→",
        }
    else:
        report["metrics"]["mttr"] = {"status": "无故障"}
    
    # Noise Rate
    noise_vals = [m["noise_rate"].get("noise_rate") for m in week_data if m["noise_rate"].get("noise_rate") is not None]
    if noise_vals:
        avg_noise = sum(noise_vals) / len(noise_vals)
        report["metrics"]["noise_rate"] = {
            "avg": round(avg_noise, 2),
            "target": 0.70,
            "pass": avg_noise >= 0.70,
            "trend": "↑" if len(noise_vals) > 1 and noise_vals[-1] > noise_vals[0] else "→",
        }
    else:
        report["metrics"]["noise_rate"] = {"status": "无告警"}
    
    # Retry Yield
    retry_vals = [m["retry_yield"].get("retry_yield") for m in week_data if m["retry_yield"].get("retry_yield") is not None]
    if retry_vals:
        avg_retry = sum(retry_vals) / len(retry_vals)
        report["metrics"]["retry_yield"] = {
            "avg": round(avg_retry, 2),
            "trend": "↑" if len(retry_vals) > 1 and retry_vals[-1] > retry_vals[0] else "→",
        }
    else:
        report["metrics"]["retry_yield"] = {"status": "无重试"}
    
    # Rollback Safety
    rollback_vals = [m["rollback_safety"].get("rollback_safety") for m in week_data if m["rollback_safety"].get("rollback_safety") is not None]
    if rollback_vals:
        avg_rollback = sum(rollback_vals) / len(rollback_vals)
        report["metrics"]["rollback_safety"] = {
            "avg": round(avg_rollback, 2),
            "target": 1.0,
            "pass": avg_rollback >= 1.0,
        }
    else:
        report["metrics"]["rollback_safety"] = {"status": "无回滚"}
    
    return report


def format_markdown(report: dict) -> str:
    """生成 Markdown 格式周报"""
    lines = [
        f"# 运营期周报 - Week {report['week']}",
        f"",
        f"**期间**: {report['period']} ({report['days_count']} 天)",
        f"",
        f"## 验收指标",
        f"",
    ]
    
    m = report["metrics"]
    
    # MTTR
    if "avg" in m.get("mttr", {}):
        lines.append(f"### MTTR (故障平均恢复时长)")
        lines.append(f"- 平均: {m['mttr']['avg']} 分钟 {m['mttr']['trend']}")
        lines.append(f"- 范围: {m['mttr']['min']} ~ {m['mttr']['max']} 分钟")
        lines.append(f"- 目标: 逐周下降")
        lines.append("")
    else:
        lines.append(f"### MTTR: {m['mttr']['status']}")
        lines.append("")
    
    # Noise Rate
    if "avg" in m.get("noise_rate", {}):
        status = "✅ 达标" if m['noise_rate']['pass'] else "❌ 未达标"
        lines.append(f"### Noise Rate (告警噪音率) {status}")
        lines.append(f"- 平均: {m['noise_rate']['avg']:.1%} {m['noise_rate']['trend']}")
        lines.append(f"- 目标: ≥ 70%")
        lines.append("")
    else:
        lines.append(f"### Noise Rate: {m['noise_rate']['status']}")
        lines.append("")
    
    # Retry Yield
    if "avg" in m.get("retry_yield", {}):
        lines.append(f"### Retry Yield (重试挽回率)")
        lines.append(f"- 平均: {m['retry_yield']['avg']:.1%} {m['retry_yield']['trend']}")
        lines.append(f"- 目标: 稳定上升")
        lines.append("")
    else:
        lines.append(f"### Retry Yield: {m['retry_yield']['status']}")
        lines.append("")
    
    # Rollback Safety
    if "avg" in m.get("rollback_safety", {}):
        status = "✅ 达标" if m['rollback_safety']['pass'] else "❌ 未达标"
        lines.append(f"### Rollback Safety (回滚成功率) {status}")
        lines.append(f"- 平均: {m['rollback_safety']['avg']:.1%}")
        lines.append(f"- 目标: 100%")
        lines.append("")
    else:
        lines.append(f"### Rollback Safety: {m['rollback_safety']['status']}")
        lines.append("")
    
    return "\n".join(lines)


def format_telegram(report: dict) -> str:
    """生成 Telegram 精简版"""
    lines = [f"📊 运营期周报 Week {report['week']}"]
    lines.append(f"{report['period']} ({report['days_count']}天)")
    lines.append("")
    
    m = report["metrics"]
    
    if "avg" in m.get("mttr", {}):
        lines.append(f"MTTR: {m['mttr']['avg']}min {m['mttr']['trend']}")
    else:
        lines.append(f"MTTR: {m['mttr']['status']}")
    
    if "avg" in m.get("noise_rate", {}):
        icon = "✅" if m['noise_rate']['pass'] else "❌"
        lines.append(f"Noise Rate: {m['noise_rate']['avg']:.0%} {icon} {m['noise_rate']['trend']}")
    else:
        lines.append(f"Noise Rate: {m['noise_rate']['status']}")
    
    if "avg" in m.get("retry_yield", {}):
        lines.append(f"Retry Yield: {m['retry_yield']['avg']:.0%} {m['retry_yield']['trend']}")
    else:
        lines.append(f"Retry Yield: {m['retry_yield']['status']}")
    
    if "avg" in m.get("rollback_safety", {}):
        icon = "✅" if m['rollback_safety']['pass'] else "❌"
        lines.append(f"Rollback Safety: {m['rollback_safety']['avg']:.0%} {icon}")
    else:
        lines.append(f"Rollback Safety: {m['rollback_safety']['status']}")
    
    return "\n".join(lines)


def save_report(report: dict, markdown: str):
    """保存周报到文件"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"ops_week_{report['week']}.md"
    path = REPORTS_DIR / filename
    path.write_text(markdown, encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    action = sys.argv[1] if len(sys.argv) > 1 else "telegram"
    
    report = generate_weekly_report()
    
    if "error" in report:
        print(report["error"])
        sys.exit(1)
    
    if action == "markdown":
        md = format_markdown(report)
        path = save_report(report, md)
        print(f"周报已保存: {path}")
        print()
        print(md)
    elif action == "telegram":
        print(format_telegram(report))
    elif action == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Usage: ops_weekly.py [markdown|telegram|json]")
