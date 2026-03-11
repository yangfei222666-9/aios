"""
Error_Analyzer 直接执行脚本 v1.0

最小执行链路：
1. 接收明确输入（log_source + time_range）
2. 读取错误日志
3. 执行错误分析（根因 / 影响 / 建议）
4. 写回结果（memory + execution record）
5. 输出最终 outcome
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# 项目根目录
AIOS_ROOT = Path(__file__).parent
WORKSPACE_ROOT = AIOS_ROOT.parent.parent  # .openclaw/workspace

# 数据目录
DATA_DIR = AIOS_ROOT / "data"
MEMORY_DIR = WORKSPACE_ROOT / "memory"
EXECUTION_RECORD = DATA_DIR / "agent_execution_record.jsonl"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# 已知日志源
LOG_SOURCES = {
    "skill_failure_alerts": DATA_DIR / "skill_failure_alerts.jsonl",
    "fallback_log": DATA_DIR / "fallback_log.jsonl",
    "dispatcher": AIOS_ROOT / "dispatcher.log",
    "lifecycle_check": AIOS_ROOT / "lifecycle_check.log",
    "task_traces": DATA_DIR / "task_traces.jsonl",
}


def log_execution(record: dict):
    """记录执行到 agent_execution_record.jsonl"""
    with open(EXECUTION_RECORD, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_to_memory(content: str, date_str: str) -> str:
    """写回到 memory/YYYY-MM-DD.md"""
    memory_file = MEMORY_DIR / f"{date_str}.md"
    with open(memory_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n{content}\n")
    return str(memory_file)


def load_jsonl(path: Path, max_lines: int = 500) -> list:
    """加载 JSONL 文件，返回解析后的记录列表"""
    records = []
    if not path.exists():
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(records) >= max_lines:
                break
    return records


def load_log(path: Path, max_lines: int = 500) -> list:
    """加载普通日志文件，尝试解析为 JSON，否则保留原文"""
    records = []
    if not path.exists():
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({"raw": line})
            if len(records) >= max_lines:
                break
    return records


def filter_errors(records: list) -> list:
    """从记录中筛选出错误/告警相关条目"""
    error_records = []
    for r in records:
        # 判断是否为错误记录
        is_error = False

        # 检查 alert_level
        if r.get("alert_level") in ("crit", "warn", "error"):
            is_error = True
        # 检查 level
        if r.get("level") in ("error", "warn", "critical"):
            is_error = True
        # 检查 status
        if r.get("status") in ("failed", "error"):
            is_error = True
        # 检查 outcome
        if r.get("outcome") in ("failed", "error"):
            is_error = True
        # 检查 error_type 字段存在
        if r.get("error_type"):
            is_error = True
        # 检查 last_failure_reason 字段存在
        if r.get("last_failure_reason"):
            is_error = True

        if is_error:
            error_records.append(r)

    return error_records


def analyze_errors(error_records: list, source_name: str) -> dict:
    """
    分析错误记录，输出根因 / 影响 / 建议

    Returns:
        dict: {
            "total_errors": int,
            "error_categories": {category: count},
            "findings": [
                {
                    "category": str,
                    "root_cause": str,
                    "impact": str,
                    "recommendation": str,
                    "severity": "P0" | "P1" | "P2",
                    "evidence": list[str]
                }
            ],
            "summary": str
        }
    """
    if not error_records:
        return {
            "total_errors": 0,
            "error_categories": {},
            "findings": [],
            "summary": f"在 {source_name} 中未发现错误记录"
        }

    # 1. 分类统计
    categories = Counter()
    severity_map = Counter()
    affected_components = Counter()
    error_details = {}  # category -> [records]

    for r in error_records:
        # 确定错误类别
        category = (
            r.get("error_type")
            or r.get("last_failure_reason")
            or r.get("level", "unknown")
        )
        categories[category] += 1

        # 确定严重级别
        level = r.get("alert_level") or r.get("level") or "unknown"
        severity_map[level] += 1

        # 确定受影响组件
        component = (
            r.get("skill_id")
            or r.get("agent_id")
            or r.get("task_id")
            or "unknown"
        )
        affected_components[component] += 1

        # 收集详情
        if category not in error_details:
            error_details[category] = []
        error_details[category].append(r)

    # 2. 生成分析结果
    findings = []

    for category, count in categories.most_common():
        samples = error_details[category][:3]  # 最多取 3 条样本

        # 确定严重级别
        severity = "P2"
        if count >= 5 or any(
            s.get("alert_level") == "crit" for s in samples
        ):
            severity = "P0"
        elif count >= 3 or any(
            s.get("alert_level") == "warn" for s in samples
        ):
            severity = "P1"

        # 确定根因
        root_cause = _infer_root_cause(category, samples)

        # 确定影响
        components = set()
        for s in error_details[category]:
            comp = (
                s.get("skill_id")
                or s.get("agent_id")
                or s.get("task_id")
            )
            if comp:
                components.add(comp)
        impact = f"影响 {len(components)} 个组件: {', '.join(list(components)[:5])}"
        if count > 1:
            impact += f"，共发生 {count} 次"

        # 确定建议
        recommendation = _generate_recommendation(category, samples, count)

        # 收集证据
        evidence = []
        for s in samples:
            ts = s.get("detected_at") or s.get("ts") or s.get("timestamp") or ""
            comp = (
                s.get("skill_id")
                or s.get("agent_id")
                or s.get("task_id")
                or ""
            )
            evidence.append(f"[{ts}] {comp}: {category}")

        findings.append({
            "category": category,
            "root_cause": root_cause,
            "impact": impact,
            "recommendation": recommendation,
            "severity": severity,
            "evidence": evidence,
        })

    # 按严重级别排序
    severity_order = {"P0": 0, "P1": 1, "P2": 2}
    findings.sort(key=lambda f: severity_order.get(f["severity"], 9))

    # 3. 生成摘要
    p0 = len([f for f in findings if f["severity"] == "P0"])
    p1 = len([f for f in findings if f["severity"] == "P1"])
    p2 = len([f for f in findings if f["severity"] == "P2"])

    summary = (
        f"分析 {source_name} 中 {len(error_records)} 条错误记录，"
        f"归纳为 {len(findings)} 类问题"
        f"（P0:{p0} P1:{p1} P2:{p2}），"
        f"涉及 {len(affected_components)} 个组件"
    )

    return {
        "total_errors": len(error_records),
        "error_categories": dict(categories),
        "findings": findings,
        "summary": summary,
    }


def _infer_root_cause(category: str, samples: list) -> str:
    """根据错误类别和样本推断根因"""
    cause_map = {
        "network_error": "网络连接不稳定或目标端点不可达",
        "timeout": "操作超时，可能是资源不足或任务复杂度过高",
        "resource_exhausted": "系统资源（内存/CPU/磁盘）耗尽",
        "memory_error": "内存不足或内存泄漏",
        "permission_denied": "权限不足，无法访问目标资源",
        "file_not_found": "目标文件或路径不存在",
        "parse_error": "数据格式错误，无法解析",
        "config_error": "配置错误或缺失",
    }

    if category in cause_map:
        return cause_map[category]

    # 尝试从样本中提取更多信息
    for s in samples:
        if s.get("suggested_recovery"):
            return f"错误类型 '{category}'，系统建议: {s['suggested_recovery']}"

    return f"错误类型 '{category}'，需要进一步排查具体触发条件"


def _generate_recommendation(category: str, samples: list, count: int) -> str:
    """根据错误类别生成修复建议"""
    rec_map = {
        "network_error": "检查网络连接，配置重试机制和备用端点",
        "timeout": "增加超时时间，或拆分任务降低单次执行复杂度",
        "resource_exhausted": "减小批处理大小，清理临时文件，监控资源使用",
        "memory_error": "减少并发任务数，优化内存使用，检查内存泄漏",
        "permission_denied": "检查文件/目录权限，确认执行用户权限",
        "file_not_found": "验证路径配置，添加路径存在性检查",
        "parse_error": "添加输入验证，增强错误处理",
        "config_error": "检查配置文件完整性，添加配置验证",
    }

    base_rec = rec_map.get(category, f"排查 '{category}' 类错误的具体触发条件")

    if count >= 5:
        base_rec += "。该问题频繁发生，建议优先处理"
    elif count >= 3:
        base_rec += "。该问题有重复趋势，建议关注"

    return base_rec


def format_report(
    task_id: str,
    source_name: str,
    result: dict,
    start_time: datetime,
    duration: float,
) -> str:
    """格式化分析报告为 markdown"""

    report = f"""# Error_Analyzer 分析报告

**Task ID:** {task_id}
**执行时间:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}
**分析对象:** {source_name}
**错误总数:** {result['total_errors']}
**耗时:** {duration:.2f}s

---

## 摘要

{result['summary']}

---

## 错误分类统计

"""
    if result["error_categories"]:
        for cat, cnt in sorted(
            result["error_categories"].items(), key=lambda x: -x[1]
        ):
            report += f"- `{cat}`: {cnt} 次\n"
    else:
        report += "无错误记录。\n"

    report += "\n---\n\n## 详细分析\n\n"

    if result["findings"]:
        for i, finding in enumerate(result["findings"], 1):
            report += f"### {i}. [{finding['severity']}] {finding['category']}\n\n"
            report += f"- **根因:** {finding['root_cause']}\n"
            report += f"- **影响:** {finding['impact']}\n"
            report += f"- **建议:** {finding['recommendation']}\n"
            if finding["evidence"]:
                report += "- **证据:**\n"
                for ev in finding["evidence"]:
                    report += f"  - {ev}\n"
            report += "\n"
    else:
        report += "未发现需要关注的问题。\n"

    report += (
        f"\n---\n\n"
        f"**报告生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    return report


def run_error_analyzer(task_input: dict) -> dict:
    """
    执行 Error_Analyzer

    Args:
        task_input: {
            "log_source": str,   # 日志源名称（见 LOG_SOURCES）或文件路径
            "max_records": int,  # 最大读取记录数（可选，默认 500）
            "task_id": str       # 可选
        }

    Returns:
        dict: {
            "outcome": "success" | "partial" | "failed",
            "duration_sec": float,
            "output_path": str,
            "total_errors": int,
            "findings_count": int,
            "error": str | None
        }
    """
    log_source = task_input["log_source"]
    max_records = task_input.get("max_records", 500)
    task_id = task_input.get("task_id") or (
        f"error-analysis-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )

    start_time = datetime.now()

    # 记录开始
    start_record = {
        "task_id": task_id,
        "agent_name": "Error_Analyzer",
        "trigger": "manual",
        "input": task_input,
        "start_time": start_time.isoformat(),
        "status": "started",
    }
    log_execution(start_record)

    print("=== Error_Analyzer 执行开始 ===")
    print(f"Task ID: {task_id}")
    print(f"Log Source: {log_source}")
    print(f"Max Records: {max_records}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 1. 确定日志路径
        print("[1/4] 定位日志源...")
        if log_source in LOG_SOURCES:
            log_path = LOG_SOURCES[log_source]
            source_name = log_source
        else:
            log_path = Path(log_source)
            source_name = log_path.name

        if not log_path.exists():
            raise FileNotFoundError(f"日志源不存在: {log_path}")

        print(f"  路径: {log_path}")
        print(f"  大小: {log_path.stat().st_size / 1024:.1f} KB")
        print()

        # 2. 加载日志
        print("[2/4] 加载日志记录...")
        if str(log_path).endswith(".jsonl"):
            records = load_jsonl(log_path, max_records)
        else:
            records = load_log(log_path, max_records)
        print(f"  加载了 {len(records)} 条记录")
        print()

        # 3. 筛选错误 + 分析
        print("[3/4] 筛选错误并分析...")
        error_records = filter_errors(records)
        print(f"  筛选出 {len(error_records)} 条错误/告警记录")

        result = analyze_errors(error_records, source_name)
        print(f"  {result['summary']}")
        print()

        # 4. 写回结果
        print("[4/4] 写回结果...")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 生成报告
        report = format_report(task_id, source_name, result, start_time, duration)

        # 写入 memory
        date_str = start_time.strftime("%Y-%m-%d")
        memory_path = write_to_memory(report, date_str)
        print(f"  写回到: {memory_path}")

        # 写入 execution record
        end_record = {
            "task_id": task_id,
            "agent_name": "Error_Analyzer",
            "trigger": "manual",
            "input": task_input,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_sec": duration,
            "outcome": "success",
            "output_path": memory_path,
            "total_errors": result["total_errors"],
            "findings_count": len(result["findings"]),
            "error": None,
        }
        log_execution(end_record)

        # 更新 selflearn-state
        from selflearn_state import update_state
        update_state(
            agent_id="Error_Analyzer",
            success=True
        )

        print()
        print("=== 执行完成 ===")
        print(f"Outcome: success")
        print(f"Duration: {duration:.2f}s")
        print(f"Total Errors: {result['total_errors']}")
        print(f"Findings: {len(result['findings'])}")
        print(f"Output: {memory_path}")

        return {
            "outcome": "success",
            "duration_sec": duration,
            "output_path": memory_path,
            "total_errors": result["total_errors"],
            "findings_count": len(result["findings"]),
            "error": None,
        }

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        error_record = {
            "task_id": task_id,
            "agent_name": "Error_Analyzer",
            "trigger": "manual",
            "input": task_input,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_sec": duration,
            "outcome": "failed",
            "output_path": None,
            "error": str(e),
        }
        log_execution(error_record)

        # 更新 selflearn-state（失败）
        from selflearn_state import update_state
        update_state(
            agent_id="Error_Analyzer",
            success=False
        )

        print()
        print("=== 执行失败 ===")
        print(f"Error: {e}")
        print(f"Duration: {duration:.2f}s")

        return {
            "outcome": "failed",
            "duration_sec": duration,
            "output_path": None,
            "total_errors": 0,
            "findings_count": 0,
            "error": str(e),
        }


if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) >= 2:
        source = sys.argv[1]
    else:
        # 默认分析 skill_failure_alerts
        source = "skill_failure_alerts"

    task_input = {"log_source": source}

    result = run_error_analyzer(task_input)

    print()
    print("=== 最终结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
