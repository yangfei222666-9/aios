#!/usr/bin/env python3
"""
Backup Restore Manager v1.0.0
统一封装：一键备份、MRS 检查、隔离恢复、Drill 报告生成。
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

AGENT_SYSTEM_DIR = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system")
WORKSPACE_DIR = Path(r"C:\Users\A\.openclaw\workspace")
BACKUP_ROOT = WORKSPACE_DIR / "aios" / "backups"
DATA_DIR = AGENT_SYSTEM_DIR / "data"

# MRS 关键文件（简化版，与 backup.py 对齐）
MRS_FILES = {
    "runtime": [
        "data/agents.json",
        "data/task_queue.jsonl",
        "data/task_executions.jsonl",
        "data/spawn_pending.jsonl",
        "data/spawn_results.jsonl",
        "data/alerts.jsonl",
    ],
    "config": [
        "heartbeat_v5.py",
        "learning_agents.py",
        "aios.py",
        "task_executor.py",
        "memory_server.py",
    ],
    "memory": [
        # workspace-level
    ],
    "recovery": [
        "backup.py",
        "restore.py",
        "MINIMUM_RECOVERABLE_SET.md",
    ],
}

WORKSPACE_FILES = ["MEMORY.md"]


def check_mrs() -> dict:
    """检查 MRS 完整性"""
    found = []
    missing = []

    for category, files in MRS_FILES.items():
        for f in files:
            path = AGENT_SYSTEM_DIR / f
            if path.exists():
                found.append(f)
            else:
                missing.append(f)

    for f in WORKSPACE_FILES:
        path = WORKSPACE_DIR / f
        if path.exists():
            found.append(f"workspace:{f}")
        else:
            missing.append(f"workspace:{f}")

    # 检查 daily logs
    memory_dir = WORKSPACE_DIR / "memory"
    daily_logs = sorted(memory_dir.glob("2026-*.md"), reverse=True) if memory_dir.exists() else []
    if daily_logs:
        found.append(f"daily_logs: {len(daily_logs)} files")
    else:
        missing.append("daily_logs: none found")

    return {
        "complete": len(missing) == 0,
        "found": found,
        "missing": missing,
        "found_count": len(found),
        "missing_count": len(missing),
    }


def do_backup() -> dict:
    """执行备份（调用现有 backup.py）"""
    print("📦 Running backup...")
    backup_script = AGENT_SYSTEM_DIR / "backup.py"
    if not backup_script.exists():
        print("❌ backup.py not found!")
        return {"status": "error", "error": "backup.py not found"}

    import subprocess
    result = subprocess.run(
        [sys.executable, str(backup_script)],
        capture_output=True, text=True, timeout=120,
        cwd=str(AGENT_SYSTEM_DIR),
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Backup failed: {result.stderr}")
        return {"status": "error", "error": result.stderr}

    # 找到最新备份目录
    if BACKUP_ROOT.exists():
        backups = sorted([d for d in BACKUP_ROOT.iterdir() if d.is_dir()], reverse=True)
        if backups:
            latest = backups[0]
            meta_file = latest / "backup_metadata.json"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)

    return {"status": "completed", "output": result.stdout}


def do_restore_drill(backup_dir: Path = None) -> dict:
    """在隔离环境执行恢复演练"""
    # 找最新备份
    if backup_dir is None:
        if not BACKUP_ROOT.exists():
            return {"status": "error", "error": "No backups found"}
        backups = sorted([d for d in BACKUP_ROOT.iterdir() if d.is_dir()], reverse=True)
        if not backups:
            return {"status": "error", "error": "No backups found"}
        backup_dir = backups[0]

    print(f"🔬 Running restore drill from: {backup_dir.name}")

    # 创建隔离恢复目录
    drill_dir = BACKUP_ROOT / "drill_temp"
    if drill_dir.exists():
        shutil.rmtree(drill_dir)
    drill_dir.mkdir(parents=True)

    # 复制备份到隔离目录
    results = {
        "backup_source": str(backup_dir),
        "drill_dir": str(drill_dir),
        "checks": {},
        "timestamp": datetime.now().isoformat(),
    }

    # 恢复文件
    restored_count = 0
    for item in backup_dir.rglob("*"):
        if item.is_file() and item.name != "backup_metadata.json":
            rel = item.relative_to(backup_dir)
            dst = drill_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst)
            restored_count += 1

    results["restored_files"] = restored_count

    # 验证 1: agents.json 可加载
    agents_file = drill_dir / "data" / "agents.json"
    if agents_file.exists():
        try:
            with open(agents_file, "r", encoding="utf-8") as f:
                agents = json.load(f)
            agent_count = len(agents.get("agents", []))
            routable = sum(1 for a in agents.get("agents", []) if a.get("routable"))
            results["checks"]["agents"] = {
                "status": "PASS",
                "total": agent_count,
                "routable": routable,
            }
        except Exception as e:
            results["checks"]["agents"] = {"status": "FAIL", "error": str(e)}
    else:
        results["checks"]["agents"] = {"status": "FAIL", "error": "agents.json not found in backup"}

    # 验证 2: MEMORY.md 可读
    memory_file = drill_dir / "workspace" / "MEMORY.md"
    if memory_file.exists():
        try:
            content = memory_file.read_text(encoding="utf-8")
            results["checks"]["memory"] = {
                "status": "PASS",
                "size_bytes": len(content.encode("utf-8")),
            }
        except Exception as e:
            results["checks"]["memory"] = {"status": "FAIL", "error": str(e)}
    else:
        results["checks"]["memory"] = {"status": "FAIL", "error": "MEMORY.md not found in backup"}

    # 验证 3: heartbeat_v5.py 存在且可解析
    hb_file = drill_dir / "heartbeat_v5.py"
    if hb_file.exists():
        try:
            content = hb_file.read_text(encoding="utf-8")
            has_main = "def " in content or "if __name__" in content
            results["checks"]["heartbeat"] = {
                "status": "PASS",
                "has_entry_point": has_main,
                "size_bytes": len(content.encode("utf-8")),
            }
        except Exception as e:
            results["checks"]["heartbeat"] = {"status": "FAIL", "error": str(e)}
    else:
        results["checks"]["heartbeat"] = {"status": "FAIL", "error": "heartbeat_v5.py not found in backup"}

    # 验证 4: 关键配置文件
    config_files = ["aios.py", "task_executor.py", "learning_agents.py", "memory_server.py"]
    config_ok = 0
    for cf in config_files:
        if (drill_dir / cf).exists():
            config_ok += 1
    results["checks"]["config"] = {
        "status": "PASS" if config_ok == len(config_files) else "PARTIAL",
        "found": config_ok,
        "expected": len(config_files),
    }

    # 验证 5: 运行时数据文件
    runtime_files = ["data/task_queue.jsonl", "data/task_executions.jsonl", "data/spawn_pending.jsonl"]
    runtime_ok = 0
    for rf in runtime_files:
        if (drill_dir / rf).exists():
            runtime_ok += 1
    results["checks"]["runtime_data"] = {
        "status": "PASS" if runtime_ok == len(runtime_files) else "PARTIAL",
        "found": runtime_ok,
        "expected": len(runtime_files),
    }

    # 综合判定
    all_pass = all(c.get("status") == "PASS" for c in results["checks"].values())
    any_fail = any(c.get("status") == "FAIL" for c in results["checks"].values())

    if all_pass:
        results["conclusion"] = "可恢复"
        results["ready_for_recovery"] = True
    elif any_fail:
        results["conclusion"] = "部分可恢复"
        results["ready_for_recovery"] = False
    else:
        results["conclusion"] = "部分可恢复"
        results["ready_for_recovery"] = False

    # 缺失项
    missing = [k for k, v in results["checks"].items() if v.get("status") != "PASS"]
    results["missing_items"] = missing
    results["next_steps"] = [f"修复 {m}" for m in missing] if missing else ["无需补项"]

    # 清理隔离目录
    shutil.rmtree(drill_dir, ignore_errors=True)

    return results


def generate_mrs_report(mrs: dict, output_dir: Path):
    """生成 MRS 检查报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# MRS 检查报告

**检查时间：** {now}
**完整性：** {'✅ 完整' if mrs['complete'] else '❌ 不完整'}
**已找到：** {mrs['found_count']} 项
**缺失：** {mrs['missing_count']} 项

## 已找到的文件

"""
    for f in mrs["found"]:
        md += f"- ✅ {f}\n"

    if mrs["missing"]:
        md += "\n## 缺失的文件\n\n"
        for f in mrs["missing"]:
            md += f"- ❌ {f}\n"

    md += f"\n---\n*Generated by backup-restore-manager v1.0.0*\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "mrs_check_report.md").write_text(md, encoding="utf-8")


def generate_drill_report(drill: dict, output_dir: Path):
    """生成 Drill 报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# 恢复演练报告（Restore Drill）

**演练时间：** {now}
**备份源：** {drill.get('backup_source', '?')}
**恢复文件数：** {drill.get('restored_files', 0)}

## 验证结果

| 检查项 | 状态 | 详情 |
|--------|------|------|
"""
    for check_name, check_result in drill.get("checks", {}).items():
        status = check_result.get("status", "?")
        icon = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
        detail = json.dumps({k: v for k, v in check_result.items() if k != "status"}, ensure_ascii=False)
        md += f"| {check_name} | {icon} {status} | {detail} |\n"

    md += f"""
## 最终判定

**最终结论：** {drill.get('conclusion', '未知')}
**是否具备立即用于故障恢复的条件：** {'是' if drill.get('ready_for_recovery') else '否'}
**缺失项：** {', '.join(drill.get('missing_items', [])) or '无'}
**下一步补项：** {', '.join(drill.get('next_steps', [])) or '无'}

---
*Generated by backup-restore-manager v1.0.0*
"""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "restore_drill_report.md").write_text(md, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Backup Restore Manager v1.0.0")
    parser.add_argument("action", choices=["backup", "check-mrs", "drill", "full"],
                        help="backup: 一键备份 | check-mrs: MRS检查 | drill: 恢复演练 | full: 完整流程")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()

    out = Path(args.output)
    print("🛡️ Backup Restore Manager v1.0.0\n")

    if args.action == "check-mrs":
        mrs = check_mrs()
        icon = "✅" if mrs["complete"] else "❌"
        print(f"{icon} MRS: {mrs['found_count']} found, {mrs['missing_count']} missing")
        if mrs["missing"]:
            for m in mrs["missing"]:
                print(f"  ❌ {m}")
        generate_mrs_report(mrs, out)
        print(f"\n📁 Report: {out / 'mrs_check_report.md'}")

    elif args.action == "backup":
        mrs = check_mrs()
        if not mrs["complete"]:
            print(f"⚠️ MRS incomplete ({mrs['missing_count']} missing), proceeding anyway...")
        result = do_backup()
        print(f"\n📦 Backup result: {result.get('status', 'unknown')}")

    elif args.action == "drill":
        drill = do_restore_drill()
        icon = "✅" if drill.get("ready_for_recovery") else "⚠️"
        print(f"\n{icon} Conclusion: {drill.get('conclusion', '?')}")
        print(f"  Ready for recovery: {drill.get('ready_for_recovery', False)}")
        if drill.get("missing_items"):
            print(f"  Missing: {', '.join(drill['missing_items'])}")
        generate_drill_report(drill, out)
        print(f"\n📁 Report: {out / 'restore_drill_report.md'}")

    elif args.action == "full":
        print("=" * 50)
        print("[1/3] MRS Check")
        print("=" * 50)
        mrs = check_mrs()
        icon = "✅" if mrs["complete"] else "❌"
        print(f"{icon} MRS: {mrs['found_count']} found, {mrs['missing_count']} missing")
        generate_mrs_report(mrs, out)

        print(f"\n{'=' * 50}")
        print("[2/3] Backup")
        print("=" * 50)
        backup_result = do_backup()

        print(f"\n{'=' * 50}")
        print("[3/3] Restore Drill")
        print("=" * 50)
        drill = do_restore_drill()
        icon = "✅" if drill.get("ready_for_recovery") else "⚠️"
        print(f"\n{icon} Conclusion: {drill.get('conclusion', '?')}")
        print(f"  Ready for recovery: {drill.get('ready_for_recovery', False)}")
        generate_drill_report(drill, out)

        print(f"\n{'=' * 50}")
        print("Summary")
        print("=" * 50)
        print(f"  MRS: {'Complete' if mrs['complete'] else 'Incomplete'}")
        print(f"  Backup: {backup_result.get('status', 'unknown')}")
        print(f"  Drill: {drill.get('conclusion', '?')}")
        print(f"  Recovery Ready: {drill.get('ready_for_recovery', False)}")
        print(f"\n📁 Reports: {out}")


if __name__ == "__main__":
    main()
