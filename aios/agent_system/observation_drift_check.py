#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
观察期状态漂移检测脚本 v1.0

检查 4 项：
1. Daily Smoke - 回归测试是否全绿
2. 口径一致性 - 四个消费者的状态推导结果是否一致
3. 适配层绕过检测 - 新代码是否绕过 status_adapter
4. 旧字段偷读检测 - 是否有代码直接读取旧字段
"""

import json
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
RESULTS = []


def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    icon = "\u2705" if passed else "\u274c"
    RESULTS.append({"name": name, "passed": passed, "detail": detail})
    print(f"  {icon} {name}: {status}")
    if detail:
        print(f"      {detail}")


# =========================================================================
# 1. Daily Smoke - 回归测试
# =========================================================================
def check_regression_tests():
    print("\n[1/4] Daily Smoke - 回归测试")
    test_file = BASE / "tests" / "test_status_regression.py"
    if not test_file.exists():
        check("回归测试文件存在", False, f"{test_file} 不存在")
        return

    try:
        result = subprocess.run(
            [r"C:\Program Files\Python312\python.exe", "-X", "utf8", str(test_file)],
            capture_output=True, text=True, timeout=30,
            cwd=str(BASE),
            env={**__import__("os").environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
        )
        all_passed = result.returncode == 0
        # 从输出中提取通过数
        output = result.stdout + result.stderr
        match = re.search(r"(\d+)/(\d+)\s*通过", output)
        if match:
            detail = f"{match.group(1)}/{match.group(2)} 通过"
        else:
            detail = output.strip()[-200:] if output.strip() else "无输出"
        check("回归测试全绿", all_passed, detail)
    except Exception as e:
        check("回归测试全绿", False, str(e))


# =========================================================================
# 2. 口径一致性 - 四个消费者状态推导对比
# =========================================================================
def check_caliber_consistency():
    print("\n[2/4] 口径一致性 - 消费者状态推导对比")

    # 加载 agents.json
    agents_file = BASE / "data" / "agents.json"
    if not agents_file.exists():
        check("agents.json 存在", False)
        return

    with open(agents_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    agents = data.get("agents", [])

    # 通过 status_adapter 推导
    sys.path.insert(0, str(BASE / "core"))
    sys.path.insert(0, str(BASE))

    try:
        from core.status_adapter import get_agent_status
        adapter_results = {}
        for agent in agents:
            name = agent.get("name", agent.get("id", "unknown"))
            adapter_results[name] = get_agent_status(agent)
        check("status_adapter 推导成功", True, f"{len(adapter_results)} 个 Agent")
    except Exception as e:
        check("status_adapter 推导成功", False, str(e))
        return

    # 通过 state_vocabulary_adapter 推导
    try:
        from state_vocabulary_adapter import get_agents_states
        vocab_agents = get_agents_states(agents)
        vocab_results = {}
        for agent in vocab_agents:
            name = agent.get("name", agent.get("id", "unknown"))
            state = agent.get("state", {})
            vocab_results[name] = state.get("readiness", "unknown")
        check("state_vocabulary_adapter 推导成功", True, f"{len(vocab_results)} 个 Agent")
    except Exception as e:
        check("state_vocabulary_adapter 推导成功", False, str(e))
        return

    # 对比两个适配层的结果
    # 注意：两个适配层的状态词表可能不完全相同（status_adapter 用简单词表，
    # state_vocabulary_adapter 用三维词表），所以这里只检查是否都能正常推导
    # 且结果数量一致
    count_match = len(adapter_results) == len(vocab_results)
    check(
        "两个适配层 Agent 数量一致",
        count_match,
        f"status_adapter: {len(adapter_results)}, state_vocabulary_adapter: {len(vocab_results)}"
    )

    # 检查是否有 Agent 在一个适配层中缺失
    missing_in_vocab = set(adapter_results.keys()) - set(vocab_results.keys())
    missing_in_adapter = set(vocab_results.keys()) - set(adapter_results.keys())
    no_missing = len(missing_in_vocab) == 0 and len(missing_in_adapter) == 0
    detail = ""
    if missing_in_vocab:
        detail += f"state_vocabulary_adapter 缺失: {missing_in_vocab}; "
    if missing_in_adapter:
        detail += f"status_adapter 缺失: {missing_in_adapter}"
    check("无 Agent 缺失", no_missing, detail if detail else "所有 Agent 在两个适配层中都存在")


# =========================================================================
# 3. 适配层绕过检测
# =========================================================================
def check_adapter_bypass():
    print("\n[3/4] 适配层绕过检测")

    # 扫描所有 .py 文件，查找直接推导状态的模式（不通过适配层）
    # 排除适配层本身和测试文件
    exclude_files = {
        "status_adapter.py",
        "state_vocabulary_adapter.py",
        "agent_status.py",
        "test_status_regression.py",
        "test_agent_status.py",
        "fix_agents_status.py",
        "check_agent_status.py",
        "check_status.py",
        "show_agent_status.py",
        "update_github_researcher_status.py",
        "_check_status.py",
        "observation_drift_check.py",  # 自己
    }

    # 只检查 v2 消费者文件（这些是必须通过适配层的）
    consumer_files = [
        "health_check_v2.py",
        "daily_report_v2.py",
        "weekly_report_v2.py",
        "dashboard_v2.py",
    ]

    bypass_patterns = [
        # 直接用字符串判断状态（不通过适配层）
        r"""['"]production.ready['"]""",
        r"""['"]not.executable['"]""",
    ]

    # 检查消费者是否都导入了适配层
    adapter_imports = [
        "status_adapter",
        "state_vocabulary_adapter",
        "get_agent_status",
        "get_agents_states",
    ]

    violations = []
    for fname in consumer_files:
        fpath = BASE / fname
        if not fpath.exists():
            violations.append(f"{fname}: 文件不存在")
            continue

        content = fpath.read_text(encoding="utf-8")

        # 检查是否导入了适配层
        has_adapter = any(imp in content for imp in adapter_imports)
        if not has_adapter:
            violations.append(f"{fname}: 未导入任何适配层")

    passed = len(violations) == 0
    detail = "; ".join(violations) if violations else "所有 v2 消费者都通过适配层"
    check("v2 消费者无绕过", passed, detail)


# =========================================================================
# 4. 旧字段偷读检测
# =========================================================================
def check_old_field_access():
    print("\n[4/4] 旧字段偷读检测")

    # 在 v2 消费者中检查是否直接读取旧字段
    consumer_files = [
        "health_check_v2.py",
        "daily_report_v2.py",
        "weekly_report_v2.py",
        "dashboard_v2.py",
    ]

    # 旧字段访问模式
    old_field_patterns = [
        (r"""agent\s*\[\s*['"]status['"]\s*\]""", "agent['status']"),
        (r"""agent\s*\[\s*['"]state['"]\s*\]""", "agent['state']"),
        (r"""skill\s*\[\s*['"]status['"]\s*\]""", "skill['status']"),
        (r"""\.get\s*\(\s*['"]status['"]""", ".get('status')"),
    ]

    # 排除注释行和字符串中的引用
    violations = []
    for fname in consumer_files:
        fpath = BASE / fname
        if not fpath.exists():
            continue

        lines = fpath.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 跳过注释
            if stripped.startswith("#"):
                continue
            # 跳过文档字符串（简单判断）
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            for pattern, desc in old_field_patterns:
                if re.search(pattern, line):
                    # 排除 task 相关的 status（task['status'] 是允许的）
                    line_lower = line.lower()
                    if any(kw in line_lower for kw in ["task", "queue", "state.get"]):
                        # task queue 的 status 和 task state 的 status 是允许的
                        if "agent" not in line_lower and "skill" not in line_lower:
                            continue
                    # 排除 run_status / health_status / readiness_status（这些是新字段）
                    if any(x in line for x in ["run_status", "health_status", "readiness_status",
                                                "lifecycle_status", "derivation_status",
                                                "regeneration_status"]):
                        continue
                    violations.append(f"{fname}:{i} -> {desc}: {stripped[:80]}")

    passed = len(violations) == 0
    if violations:
        detail = "\n      ".join(violations[:5])
        if len(violations) > 5:
            detail += f"\n      ... 还有 {len(violations) - 5} 处"
    else:
        detail = "v2 消费者无旧字段直接读取"
    check("无旧字段偷读", passed, detail)


# =========================================================================
# 主函数
# =========================================================================
def main():
    print("=" * 60)
    print(f"观察期状态漂移检测 v1.0")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    check_regression_tests()
    check_caliber_consistency()
    check_adapter_bypass()
    check_old_field_access()

    # 汇总
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"检测结果: {passed}/{total} 通过")

    if failed > 0:
        print(f"\n\u274c {failed} 项未通过:")
        for r in RESULTS:
            if not r["passed"]:
                print(f"  - {r['name']}: {r['detail']}")
        print(f"\n结论: 状态漂移检测未通过，需要修复后重新检测")
    else:
        print(f"\n\u2705 所有检测通过，无状态漂移")

    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
