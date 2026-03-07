"""
Learnings Extractor v1.0
从 lessons.json + task_executions.jsonl 中提炼通用规则（黄金法则）
自动分类错误类型，生成可执行的知识摘要

灵感来源：铀构网络 UGO 第14集 - "交互式纠正变成训练数据"
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path(__file__).parent
LESSONS_FILE = BASE / "lessons.json"
EXECUTIONS_FILE = BASE / "task_executions.jsonl"
RULES_OUTPUT = BASE / "golden_rules.md"
ERRORS_SUMMARY = BASE / "errors_summary.json"


def load_lessons():
    """加载 lessons.json"""
    if not LESSONS_FILE.exists():
        return {"lessons": [], "rules_derived": []}
    with open(LESSONS_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_executions():
    """加载 task_executions.jsonl"""
    results = []
    if not EXECUTIONS_FILE.exists():
        return results
    with open(EXECUTIONS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results


def analyze_errors(executions):
    """分析错误类型分布"""
    error_types = Counter()
    error_details = {}

    for ex in executions:
        result = ex.get("result", {})
        if not result.get("success", True):
            error = result.get("error", "unknown")
            agent = result.get("agent", "unknown")
            task_type = ex.get("task_type", "unknown")
            desc = ex.get("description", "")

            # 分类错误
            error_cat = categorize_error(error)
            error_types[error_cat] += 1

            if error_cat not in error_details:
                error_details[error_cat] = []
            error_details[error_cat].append({
                "task_id": ex.get("task_id", "?"),
                "agent": agent,
                "task_type": task_type,
                "description": desc[:100],
                "error": error[:200],
            })

    return error_types, error_details


def categorize_error(error_msg):
    """将错误消息分类"""
    error_lower = error_msg.lower()
    if "timeout" in error_lower or "timed out" in error_lower:
        return "timeout"
    elif "dependency" in error_lower or "import" in error_lower or "module" in error_lower:
        return "dependency_error"
    elif "memory" in error_lower or "resource" in error_lower or "oom" in error_lower:
        return "resource_exhausted"
    elif "permission" in error_lower or "access" in error_lower:
        return "permission_error"
    elif "syntax" in error_lower or "parse" in error_lower:
        return "syntax_error"
    elif "network" in error_lower or "connection" in error_lower or "http" in error_lower:
        return "network_error"
    elif "logic" in error_lower or "division" in error_lower or "zero" in error_lower:
        return "logic_error"
    elif "simulated" in error_lower:
        return "simulated_failure"
    else:
        return "unknown"


# 黄金法则模板：每种错误类型对应的通用规则
GOLDEN_RULE_TEMPLATES = {
    "timeout": {
        "rule": "复杂任务先评估耗时，超过60s的任务自动拆分为子任务",
        "prevention": "执行前检查任务复杂度，设置合理超时，预留缓冲时间",
        "recovery": "增加超时 → 拆分任务 → 简化逻辑",
    },
    "dependency_error": {
        "rule": "执行前验证所有依赖是否可用，缺失时自动安装",
        "prevention": "维护依赖清单，执行前预检，使用虚拟环境隔离",
        "recovery": "检查依赖 → 自动安装 → 切换备选方案",
    },
    "resource_exhausted": {
        "rule": "大文件/大数据处理必须使用流式处理，监控内存使用",
        "prevention": "预估数据量，设置内存上限，使用分块处理",
        "recovery": "释放资源 → 分块处理 → 降低并发",
    },
    "permission_error": {
        "rule": "操作前检查权限，敏感操作需要确认",
        "prevention": "预检文件/目录权限，使用最小权限原则",
        "recovery": "请求权限 → 切换路径 → 人工介入",
    },
    "syntax_error": {
        "rule": "生成代码后必须语法检查，使用AST解析验证",
        "prevention": "代码生成后自动lint，使用模板减少手写",
        "recovery": "语法修复 → 重新生成 → 人工审查",
    },
    "network_error": {
        "rule": "网络请求必须有重试机制和超时设置",
        "prevention": "设置重试次数(3次)，指数退避，备用端点",
        "recovery": "重试 → 切换端点 → 离线模式",
    },
    "logic_error": {
        "rule": "关键计算必须有输入验证和边界检查",
        "prevention": "空值检查，除零保护，范围验证",
        "recovery": "添加验证 → 修复逻辑 → 增加测试",
    },
    "simulated_failure": {
        "rule": "测试用模拟失败，不计入真实统计",
        "prevention": "N/A",
        "recovery": "N/A",
    },
    "unknown": {
        "rule": "未知错误必须记录完整上下文，便于后续分析",
        "prevention": "增加日志级别，捕获完整堆栈",
        "recovery": "记录日志 → 人工分析 → 补充分类规则",
    },
}


def extract_golden_rules(error_types, lessons_data):
    """提炼黄金法则"""
    rules = []
    existing_rules = set(lessons_data.get("rules_derived", []))

    for error_cat, count in error_types.most_common():
        if error_cat == "simulated_failure":
            continue
        template = GOLDEN_RULE_TEMPLATES.get(error_cat, GOLDEN_RULE_TEMPLATES["unknown"])
        rules.append({
            "category": error_cat,
            "occurrences": count,
            "rule": template["rule"],
            "prevention": template["prevention"],
            "recovery": template["recovery"],
            "is_new": template["rule"] not in existing_rules,
        })

    return rules


def generate_golden_rules_md(rules, error_types, total_tasks, success_rate):
    """生成 golden_rules.md"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 黄金法则 (Golden Rules)",
        f"",
        f"> 自动提炼自 lessons.json + task_executions.jsonl",
        f"> 最后更新: {now}",
        f"> 总任务: {total_tasks} | 成功率: {success_rate:.1%}",
        f"",
        f"---",
        f"",
    ]

    # 错误分布概览
    lines.append("## 错误分布")
    lines.append("")
    for cat, count in error_types.most_common():
        if cat == "simulated_failure":
            continue
        pct = count / sum(error_types.values()) * 100 if sum(error_types.values()) > 0 else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"- {cat}: {count}次 ({pct:.0f}%) {bar}")
    lines.append("")

    # 黄金法则
    lines.append("## 规则清单")
    lines.append("")
    for i, r in enumerate(rules, 1):
        new_tag = " 🆕" if r["is_new"] else ""
        lines.append(f"### {i}. [{r['category']}] ({r['occurrences']}次){new_tag}")
        lines.append(f"")
        lines.append(f"**规则:** {r['rule']}")
        lines.append(f"")
        lines.append(f"**预防:** {r['prevention']}")
        lines.append(f"")
        lines.append(f"**恢复:** {r['recovery']}")
        lines.append(f"")

    # 行动指南
    lines.append("---")
    lines.append("")
    lines.append("## 行动指南")
    lines.append("")
    lines.append("1. 每个 Agent 执行任务前，检查对应错误类型的预防措施")
    lines.append("2. 任务失败时，按恢复步骤自动重试")
    lines.append("3. 新错误类型出现时，自动补充规则")
    lines.append("4. 每周复盘：哪些规则有效降低了错误率")
    lines.append("")

    return "\n".join(lines)


def update_lessons_rules(lessons_data, rules):
    """更新 lessons.json 的 rules_derived"""
    existing = set(lessons_data.get("rules_derived", []))
    new_rules = []
    for r in rules:
        if r["rule"] not in existing:
            new_rules.append(r["rule"])
            existing.add(r["rule"])

    if new_rules:
        lessons_data["rules_derived"] = list(existing)
        with open(LESSONS_FILE, "w", encoding="utf-8") as f:
            json.dump(lessons_data, f, ensure_ascii=False, indent=2)

    return new_rules


def run():
    """主流程"""
    print("=" * 60)
    print(f"  Learnings Extractor v1.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 1. 加载数据
    lessons_data = load_lessons()
    executions = load_executions()
    print(f"[LOAD] Lessons: {len(lessons_data.get('lessons', []))} | Executions: {len(executions)}")

    # 2. 分析错误
    total = len(executions)
    success = sum(1 for e in executions if e.get("result", {}).get("success", False))
    failed = total - success
    success_rate = success / total if total > 0 else 0
    print(f"[STATS] Total: {total} | Success: {success} | Failed: {failed} | Rate: {success_rate:.1%}")

    error_types, error_details = analyze_errors(executions)
    print(f"[ERRORS] Types: {dict(error_types)}")

    # 3. 提炼黄金法则
    rules = extract_golden_rules(error_types, lessons_data)
    print(f"[RULES] Extracted: {len(rules)} rules")

    # 4. 生成 golden_rules.md
    md_content = generate_golden_rules_md(rules, error_types, total, success_rate)
    with open(RULES_OUTPUT, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Golden rules saved: {RULES_OUTPUT.name}")

    # 5. 保存错误摘要
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tasks": total,
        "success_rate": round(success_rate, 4),
        "error_distribution": dict(error_types),
        "error_details": {k: v[:3] for k, v in error_details.items()},  # 每类最多3条
    }
    with open(ERRORS_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[OK] Error summary saved: {ERRORS_SUMMARY.name}")

    # 6. 更新 lessons.json 的 rules_derived
    new_rules = update_lessons_rules(lessons_data, rules)
    if new_rules:
        print(f"[NEW] {len(new_rules)} new rules added to lessons.json:")
        for r in new_rules:
            print(f"  + {r}")
    else:
        print(f"[OK] No new rules (all {len(rules)} already in lessons.json)")

    print()
    print("=" * 60)
    print(f"  Done! {len(rules)} rules | {len(new_rules)} new")
    print("=" * 60)

    return {
        "rules_total": len(rules),
        "rules_new": len(new_rules),
        "error_types": dict(error_types),
        "success_rate": success_rate,
    }


if __name__ == "__main__":
    run()
