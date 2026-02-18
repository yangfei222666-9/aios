# aram.py - ARAM 助手 CLI (对接 autolearn v1.0)
"""
Usage:
  python aram.py build     # 构建/刷新英雄数据库
  python aram.py check     # 检查数据质量
  python aram.py report    # 生成今日报告
  python aram.py status    # 查看当前状态
"""
import sys, os, json, time
from pathlib import Path

ARAM_DIR = Path(r"C:\Users\A\Desktop\ARAM-Helper")
AUTOLEARN = Path(r"C:\Users\A\.openclaw\workspace\autolearn")
REPORTS = AUTOLEARN / "reports"

# 接入 autolearn
sys.path.insert(0, str(AUTOLEARN))
from core.executor import run as al_run
from core.errors import sign_strict, sign_loose
from core.lessons import find as al_find, add_lesson
from core.retest import run as al_retest

def _build_task(intent, payload):
    """执行 fetch_real_data.py 刷新数据"""
    import subprocess
    r = subprocess.run(
        [sys.executable, str(ARAM_DIR / "fetch_real_data.py")],
        capture_output=True, text=True, timeout=120,
        cwd=str(ARAM_DIR), encoding="utf-8", errors="replace"
    )
    if r.returncode == 0:
        return {"ok": True, "result": r.stdout[-500:] if r.stdout else "done"}
    return {"ok": False, "error": r.stderr[-500:] if r.stderr else f"exit {r.returncode}"}

def _check_task(intent, payload):
    """检查 aram_data.json 数据质量"""
    data_file = ARAM_DIR / "aram_data.json"
    if not data_file.exists():
        return {"ok": False, "error": "aram_data.json not found"}
    
    data = json.loads(data_file.read_text(encoding="utf-8"))
    
    total = len(data) if isinstance(data, list) else len(data.get("champions", data))
    empty_builds = 0
    
    items = data if isinstance(data, list) else list(data.values()) if isinstance(data, dict) else []
    for champ in items:
        if isinstance(champ, dict):
            builds = champ.get("builds") or champ.get("items") or champ.get("recommended_items")
            if not builds:
                empty_builds += 1
    
    coverage = ((total - empty_builds) / total * 100) if total > 0 else 0
    
    result = {
        "ok": True,
        "result": {
            "total_champions": total,
            "with_builds": total - empty_builds,
            "empty_builds": empty_builds,
            "coverage": f"{coverage:.1f}%",
        }
    }
    
    if coverage < 80:
        result["ok"] = False
        result["error"] = f"Coverage too low: {coverage:.1f}% ({empty_builds} champions missing builds)"
    
    return result

def cmd_build():
    print("Building ARAM database...")
    result = al_run("aram_build", "fetch_real_data.py", {}, _build_task)
    if result["ok"]:
        print("Build successful.")
        print(result.get("result", "")[:300])
    else:
        print(f"Build failed: {result.get('error', 'unknown')[:200]}")
        if result.get("tips"):
            print(f"\nTip: {result['tips'][0]['solution']}")
        if result.get("tripped"):
            print(result["checklist"])

def cmd_check():
    print("Checking ARAM data quality...")
    result = al_run("aram_check", "aram_data.json", {}, _check_task)
    if result["ok"]:
        r = result["result"]
        print(f"Champions: {r['total_champions']}")
        print(f"With builds: {r['with_builds']}")
        print(f"Coverage: {r['coverage']}")
    else:
        print(f"Check failed: {result.get('error', 'unknown')[:200]}")
        if result.get("tips"):
            print(f"\nTip: {result['tips'][0]['solution']}")

def cmd_report():
    print("Generating ARAM report...")
    
    # 数据质量
    dq = al_run("aram_check", "aram_data.json", {}, _check_task)
    
    # smoke 测试
    smoke = al_retest("smoke")
    
    # 组装报告
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# ARAM Helper Report",
        f"Generated: {ts}\n",
        f"## Data Quality",
    ]
    
    if dq["ok"]:
        r = dq["result"]
        lines.append(f"- Champions: {r['total_champions']}")
        lines.append(f"- With builds: {r['with_builds']}")
        lines.append(f"- Coverage: {r['coverage']}")
        lines.append(f"- Status: PASS")
    else:
        lines.append(f"- Status: FAIL — {dq.get('error', '?')[:100]}")
    
    lines.append(f"\n## System Health (smoke)")
    lines.append(f"- Passed: {smoke['passed']}")
    lines.append(f"- Failed: {smoke['failed']}")
    lines.append(f"- Status: {'PASS' if smoke['ok'] else 'FAIL'}")
    
    # 最近教训
    from core.lessons import active_lessons
    recent = [l for l in active_lessons() if l.get("tags") and any(t in l["tags"] for t in ["aram", "data", "powershell", "path"])]
    if recent:
        lines.append(f"\n## Relevant Lessons ({len(recent)})")
        for l in recent[-5:]:
            lines.append(f"- [{l.get('status')}] {l.get('title')}")
    
    report = "\n".join(lines)
    
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"aram_{time.strftime('%Y-%m-%d')}.md"
    path.write_text(report, encoding="utf-8")
    
    print(report)
    print(f"\nSaved to {path}")

def cmd_status():
    data_file = ARAM_DIR / "aram_data.json"
    if data_file.exists():
        size = data_file.stat().st_size
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(data_file.stat().st_mtime))
        print(f"Data: {size:,} bytes, last updated {mtime}")
    else:
        print("Data: not found")
    
    from core.version import MODULE_VERSION
    print(f"Autolearn: v{MODULE_VERSION}")
    
    from core.lessons import all_lessons
    lessons = all_lessons()
    print(f"Lessons: {len(lessons)} total")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if cmd == "build":
        cmd_build()
    elif cmd == "check":
        cmd_check()
    elif cmd == "report":
        cmd_report()
    elif cmd == "status":
        cmd_status()
    else:
        print("""aram.py - ARAM Helper CLI (powered by autolearn v1.0)

Commands:
  build    Build/refresh champion database
  check    Check data quality
  report   Generate today's report (DQ + health + lessons)
  status   Show current status
""")

if __name__ == "__main__":
    main()
