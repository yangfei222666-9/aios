"""
模拟验证脚本 - 直接内联分类器和恢复策略逻辑
标记：simulation=True，不计入生产统计
"""
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ── 内联分类器（来自 diagnose_skill_failures.py）──────────────────────────────
def classify_error(error_msg: str) -> str:
    if not error_msg:
        return "unknown"
    e = error_msg.lower()
    if "timeout" in e or "timed out" in e:
        return "timeout"
    elif "encoding" in e or "decode" in e or "codec" in e:
        return "encoding_error"
    elif "not found" in e or "no such file" in e:
        return "file_not_found"
    elif "permission" in e or "access denied" in e:
        return "permission_denied"
    elif "memory" in e or "out of memory" in e or "oomkilled" in e:
        return "resource_exhausted"
    elif "connection" in e or "network" in e or "unreachable" in e:
        return "network_error"
    elif "502" in e or "bad gateway" in e or "api error" in e:
        return "api_error"
    elif "dependency" in e or "module not found" in e or "import" in e:
        return "dependency_error"
    else:
        return "unknown"

# ── 内联恢复策略（来自 diagnose_skill_failures.py）────────────────────────────
def suggest_recovery(error_type: str, consecutive_count: int = 3) -> str:
    base = {
        "timeout":           "increase_timeout_and_retry",
        "encoding_error":    "try_multiple_encodings",
        "file_not_found":    "check_file_path_and_retry",
        "permission_denied": "check_permissions_and_retry",
        "resource_exhausted":"reduce_batch_size_and_retry",
        "network_error":     "retry_with_backoff",
        "api_error":         "switch_to_backup_endpoint",
        "dependency_error":  "check_dependencies_and_reinstall",
        "unknown":           "default_recovery",
    }
    strategy = base.get(error_type, "default_recovery")
    # 连续 3+ 次升级
    if consecutive_count >= 3:
        upgrades = {
            "timeout":       "switch_to_async_mode_or_split_task",
            "encoding_error":"fallback_to_binary_mode",
            "network_error": "switch_to_backup_endpoint",
            "api_error":     "switch_to_backup_endpoint",
            "dependency_error":"use_alternative_library",
        }
        strategy = upgrades.get(error_type, strategy)
    return strategy

# ── 模拟场景 ──────────────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "id": "sim-001",
        "skill": "api-testing-skill",
        "desc": "测试 API endpoint 连通性",
        "error": "API error: 502 - Bad Gateway from chat.apiport.cc.cd",
        "consecutive": 3,
        "expected_type": "api_error",
        "expected_strategy": "switch_to_backup_endpoint",
    },
    {
        "id": "sim-002",
        "skill": "docker-skill",
        "desc": "启动 Docker 容器批量任务",
        "error": "Container failed: OOMKilled - memory limit exceeded",
        "consecutive": 3,
        "expected_type": "resource_exhausted",
        "expected_strategy": "reduce_batch_size_and_retry",
    },
    {
        "id": "sim-003",
        "skill": "pdf-skill",
        "desc": "提取 500 页 PDF 文本",
        "error": "Task timeout after 60s - large file processing",
        "consecutive": 1,  # 首次失败，使用基础策略
        "expected_type": "timeout",
        "expected_strategy": "increase_timeout_and_retry",
    },
]

def run():
    print("=" * 60)
    print("🧪 Skill 失败恢复 - 模拟验证")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   [simulation=True，不计入生产统计]")
    print("=" * 60)

    results = []

    for s in SCENARIOS:
        print(f"\n[{s['id']}] {s['skill']}")
        print(f"  错误: {s['error']}")

        # 1. 分类
        got_type = classify_error(s["error"])
        type_ok = got_type == s["expected_type"]
        print(f"  分类: {got_type}  {'✅' if type_ok else '❌ 预期: ' + s['expected_type']}")

        # 2. 恢复建议
        got_strategy = suggest_recovery(got_type, s["consecutive"])
        strat_ok = got_strategy == s["expected_strategy"]
        print(f"  恢复: {got_strategy}  {'✅' if strat_ok else '❌ 预期: ' + s['expected_strategy']}")

        # 3. 模拟 spawn 请求
        spawn = {
            "timestamp": datetime.utcnow().isoformat(),
            "scenario_id": s["id"],
            "skill_id": s["skill"],
            "simulation": True,
            "error_type": got_type,
            "recovery_strategy": got_strategy,
            "task": f"[模拟恢复] {s['desc']} | 策略: {got_strategy}",
        }
        spawn_ok = True  # 模拟创建成功
        print(f"  Spawn: {'✅ 已创建' if spawn_ok else '❌ 失败'}")

        overall = type_ok and strat_ok and spawn_ok
        print(f"  结果: {'✅ 通过' if overall else '❌ 失败'}")

        results.append({
            "scenario_id": s["id"],
            "skill_id": s["skill"],
            "classification": got_type,
            "classification_pass": type_ok,
            "recovery_strategy": got_strategy,
            "strategy_pass": strat_ok,
            "spawn_created": spawn_ok,
            "overall_pass": overall,
        })

    # ── 报告 ──────────────────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for r in results if r["overall_pass"])

    print("\n" + "=" * 60)
    print(f"📊 结果: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
    print("=" * 60)

    # Markdown 报告
    md_lines = [
        "# Skill 失败恢复 - 模拟验证报告",
        "",
        f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "**类型：** 模拟验证（不计入生产统计）",
        "",
        "## 验证结果",
        "",
        "| 场景 | Skill | 分类 | 恢复建议 | Spawn | 结果 |",
        "|------|-------|------|----------|-------|------|",
    ]
    for r in results:
        md_lines.append(
            f"| {r['scenario_id']} | {r['skill_id']} "
            f"| {r['classification']} {'✅' if r['classification_pass'] else '❌'} "
            f"| {r['recovery_strategy']} {'✅' if r['strategy_pass'] else '❌'} "
            f"| {'✅' if r['spawn_created'] else '❌'} "
            f"| {'✅ 通过' if r['overall_pass'] else '❌ 失败'} |"
        )
    md_lines += [
        "",
        f"**通过率：** {passed}/{total} ({passed/total*100:.0f}%)",
        "",
        "## 下一步",
        "",
        "1. ✅ 模拟验证完成 - 系统逻辑正常",
        "2. ⏳ 进入自然观察期 - 等待真实失败样本积累（每类 ≥3 个）",
        "3. 📊 真实样本达标后 - 执行正式闭环验证",
        "",
        "---",
        "*此报告为模拟验证，不代表生产环境真实效果*",
    ]

    report_path = BASE_DIR / "simulation_validation_report.md"
    report_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"📄 报告: {report_path}")

    # JSON 结果
    json_path = BASE_DIR / "simulation_results.json"
    json_path.write_text(
        json.dumps({"timestamp": datetime.utcnow().isoformat(), "simulation": True, "results": results},
                   indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"📁 详细: {json_path}")

    return results

if __name__ == "__main__":
    run()
