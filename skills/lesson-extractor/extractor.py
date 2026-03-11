#!/usr/bin/env python3
"""
Lesson Extractor v1.0.0
把失败事件、状态失真、恢复演练结果，沉淀成可复用 lesson。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data")
LESSONS_FILE = DATA_DIR / "lessons.json"

# 三类事件 → lesson 模板
EVENT_TEMPLATES = {
    "timeout": {
        "false_assumption": "默认超时时间足够处理所有任务",
        "correct_model": "复杂任务需要更长超时或任务拆分",
        "preventive_rule": "根据任务复杂度动态调整超时时间",
    },
    "network_error": {
        "false_assumption": "外部服务始终可用",
        "correct_model": "外部依赖可能不可用，需要重试和降级机制",
        "preventive_rule": "所有外部调用添加重试（3次）和超时（30s）",
    },
    "resource_exhausted": {
        "false_assumption": "系统资源充足，无需监控",
        "correct_model": "资源有限，需要主动监控和预警",
        "preventive_rule": "定期检查磁盘/内存使用率，超过 80% 告警",
    },
    "agent_idle": {
        "false_assumption": "注册的 Agent 都会被触发",
        "correct_model": "部分 Agent 可能因触发条件不满足而长期 idle",
        "preventive_rule": "定期审查 idle Agent，评估保留/降级/移除",
    },
    "state_semantic_error": {
        "false_assumption": "Agent 状态标签准确反映真实状态",
        "correct_model": "状态标签可能与实际行为不一致（如 shadow 被报为 active）",
        "preventive_rule": "状态判定必须基于多维度验证，不能只看单一字段",
    },
    "trigger_precondition_error": {
        "false_assumption": "触发条件设置正确",
        "correct_model": "触发条件可能遗漏前置依赖或环境要求",
        "preventive_rule": "每个触发条件需要明确列出前置依赖",
    },
    "backup_restore_gap": {
        "false_assumption": "备份文件完整即可恢复",
        "correct_model": "恢复需要验证文件完整性、可加载性和功能等价性",
        "preventive_rule": "每次备份后执行隔离恢复演练",
    },
}


def load_json(filepath: Path) -> dict | list:
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return {}


def load_patterns(source_path: Path) -> list:
    """加载 pattern-detector 的输出"""
    if source_path.is_file():
        data = load_json(source_path)
        return data if isinstance(data, list) else []
    # 尝试默认路径
    default = Path(r"C:\Users\A\.openclaw\workspace\skills\pattern-detector\output\pattern_clusters.json")
    if default.exists():
        data = load_json(default)
        return data if isinstance(data, list) else []
    return []


def load_diagnosis(source_path: Path = None) -> dict:
    """加载 health-monitor 的诊断结果"""
    default = Path(r"C:\Users\A\.openclaw\workspace\skills\aios-health-monitor\output\diagnosis.json")
    path = source_path if source_path and source_path.exists() else default
    if path.exists():
        return load_json(path)
    return {}


def load_scorecard(source_path: Path = None) -> list:
    """加载 agent-performance-analyzer 的评分卡"""
    default = Path(r"C:\Users\A\.openclaw\workspace\skills\agent-performance-analyzer\output\agent_scorecard.json")
    path = source_path if source_path and source_path.exists() else default
    if path.exists():
        data = load_json(path)
        return data if isinstance(data, list) else []
    return []


def extract_from_patterns(patterns: list) -> list:
    """从 pattern 聚类中提取 lesson"""
    lessons = []
    now = datetime.now().strftime("%Y%m%d")

    for i, pattern in enumerate(patterns):
        ptype = pattern.get("pattern_type", "unknown")
        if ptype not in EVENT_TEMPLATES:
            continue

        template = EVENT_TEMPLATES[ptype]
        freq = pattern.get("frequency", 0)
        agents = pattern.get("affected_agents", [])
        evidence = pattern.get("evidence", [])

        lesson = {
            "lesson_id": f"les-{now}-pat-{i+1:03d}",
            "event_type": ptype,
            "trigger": f"{ptype} 模式出现 {freq} 次，影响 Agent: {', '.join(agents[:3])}",
            "false_assumption": template["false_assumption"],
            "correct_model": template["correct_model"],
            "action_taken": pattern.get("candidate_fix_direction", "待定"),
            "preventive_rule": template["preventive_rule"],
            "confidence": "high" if freq >= 5 else "medium" if freq >= 2 else "low",
            "source": "pattern-detector",
            "evidence": evidence[:3],
            "extracted_at": datetime.now().isoformat(),
        }
        lessons.append(lesson)

    return lessons


def extract_from_diagnosis(diagnosis: dict) -> list:
    """从诊断结果中提取 lesson"""
    lessons = []
    now = datetime.now().strftime("%Y%m%d")

    for i, issue in enumerate(diagnosis.get("issues", [])):
        area = issue.get("area", "unknown")
        severity = issue.get("severity", "low")

        # 映射到事件类型
        event_type = "state_semantic_error"
        if "失败" in area:
            event_type = "trigger_precondition_error"
        elif "队列" in area:
            event_type = "resource_exhausted"
        elif "idle" in area.lower():
            event_type = "agent_idle"

        template = EVENT_TEMPLATES.get(event_type, EVENT_TEMPLATES["state_semantic_error"])

        lesson = {
            "lesson_id": f"les-{now}-diag-{i+1:03d}",
            "event_type": event_type,
            "trigger": issue.get("detail", area),
            "false_assumption": template["false_assumption"],
            "correct_model": template["correct_model"],
            "action_taken": issue.get("fix", "待定"),
            "preventive_rule": template["preventive_rule"],
            "confidence": "high" if severity in ["critical", "high"] else "medium",
            "source": "aios-health-monitor",
            "extracted_at": datetime.now().isoformat(),
        }
        lessons.append(lesson)

    return lessons


def extract_from_scorecard(scorecards: list) -> list:
    """从 Agent 评分卡中提取 lesson"""
    lessons = []
    now = datetime.now().strftime("%Y%m%d")

    degraded = [c for c in scorecards if c.get("category") == "degraded"]
    for i, card in enumerate(degraded):
        lesson = {
            "lesson_id": f"les-{now}-perf-{i+1:03d}",
            "event_type": "trigger_precondition_error",
            "trigger": f"Agent {card['name']} 退化: {card.get('reason', '未知')}",
            "false_assumption": "Agent 注册后会持续正常工作",
            "correct_model": "Agent 可能因配置、依赖或负载问题退化",
            "action_taken": card.get("action", "待定"),
            "preventive_rule": "定期检查 Agent 健康度，连续失败 >= 3 次自动告警",
            "confidence": "high",
            "source": "agent-performance-analyzer",
            "extracted_at": datetime.now().isoformat(),
        }
        lessons.append(lesson)

    return lessons


def merge_to_lessons_json(new_lessons: list) -> int:
    """将新 lesson 合并到 lessons.json"""
    existing = load_json(LESSONS_FILE)
    if not isinstance(existing, dict):
        existing = {"rules_derived": [], "lessons": []}

    if "lessons" not in existing:
        existing["lessons"] = []

    # 去重（按 lesson_id）
    existing_ids = {l.get("lesson_id") for l in existing["lessons"]}
    added = 0
    for lesson in new_lessons:
        if lesson["lesson_id"] not in existing_ids:
            existing["lessons"].append(lesson)
            existing_ids.add(lesson["lesson_id"])
            added += 1

    # 写回
    LESSONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return added


def generate_reports(lessons: list, output_dir: str):
    """生成报告"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # lessons_new.json
    (out / "lessons_new.json").write_text(
        json.dumps(lessons, ensure_ascii=False, indent=2), encoding="utf-8")

    # lesson_summary.md
    md = f"""# Lesson Extraction Report

**提取时间：** {now}
**提取数量：** {len(lessons)}

## 提取的 Lessons

"""
    for lesson in lessons:
        confidence_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(lesson["confidence"], "⚪")
        md += f"""### {lesson['lesson_id']} [{confidence_icon} {lesson['confidence']}]

**事件类型：** {lesson['event_type']}
**触发条件：** {lesson['trigger']}
**误判点：** {lesson['false_assumption']}
**正确判定：** {lesson['correct_model']}
**已采取行动：** {lesson['action_taken']}
**预防规则：** {lesson['preventive_rule']}
**来源：** {lesson['source']}

---

"""

    if not lessons:
        md += "✅ 未发现需要提取的 lesson。\n"

    md += f"*Generated by lesson-extractor v1.0.0*\n"
    (out / "lesson_summary.md").write_text(md, encoding="utf-8")

    return out


def main():
    parser = argparse.ArgumentParser(description="Lesson Extractor v1.0.0")
    parser.add_argument("--source", default=None, help="Pattern clusters JSON path")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--write-back", action="store_true", help="Write lessons back to lessons.json")
    args = parser.parse_args()

    print("📚 Lesson Extractor v1.0.0\n")

    all_lessons = []

    # 1. 从 pattern-detector 提取
    source = Path(args.source) if args.source else None
    patterns = load_patterns(source) if source else load_patterns(Path(""))
    if patterns:
        pattern_lessons = extract_from_patterns(patterns)
        all_lessons.extend(pattern_lessons)
        print(f"  📊 From patterns: {len(pattern_lessons)} lessons")

    # 2. 从 health-monitor 诊断提取
    diagnosis = load_diagnosis()
    if diagnosis:
        diag_lessons = extract_from_diagnosis(diagnosis)
        all_lessons.extend(diag_lessons)
        print(f"  🏥 From diagnosis: {len(diag_lessons)} lessons")

    # 3. 从 agent-performance-analyzer 提取
    scorecards = load_scorecard()
    if scorecards:
        perf_lessons = extract_from_scorecard(scorecards)
        all_lessons.extend(perf_lessons)
        print(f"  📊 From scorecards: {len(perf_lessons)} lessons")

    print(f"\n  📚 Total: {len(all_lessons)} lessons extracted")

    # 生成报告
    out = generate_reports(all_lessons, args.output)

    # 写回 lessons.json
    if args.write_back and all_lessons:
        added = merge_to_lessons_json(all_lessons)
        print(f"  ✅ Written {added} new lessons to {LESSONS_FILE}")
    elif all_lessons:
        print(f"  ℹ️ Use --write-back to merge into lessons.json")

    print(f"\n  📁 Reports: {out}")


if __name__ == "__main__":
    main()
