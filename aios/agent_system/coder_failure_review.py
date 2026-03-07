#!/usr/bin/env python3
"""
Coder-Dispatcher 失败复盘表
按 timeout/dependency/logic/simulation 分类，对应调参建议

用法：
    python coder_failure_review.py          # 生成复盘报告
    python coder_failure_review.py --fix    # 自动应用调参建议
"""

import json
import time
from pathlib import Path
from datetime import datetime
from collections import Counter

AIOS_DIR = Path(__file__).parent
EXECUTIONS_FILE = AIOS_DIR / "task_executions.jsonl"
REPORT_FILE = AIOS_DIR / "reports" / "coder_failure_review.md"

# 确保 reports 目录存在
(AIOS_DIR / "reports").mkdir(parents=True, exist_ok=True)

# 错误分类规则
ERROR_CATEGORIES = {
    "timeout": ["timeout", "timed out", "deadline exceeded", "took too long"],
    "dependency": ["import", "module", "dependency", "not found", "no module"],
    "logic": ["assertion", "type error", "value error", "index error", "key error", "logic"],
    "resource": ["memory", "disk", "resource", "oom", "exhausted"],
    "simulation": ["simulated", "simulation"],
}

# 每种错误类型的调参建议
TUNING_ADVICE = {
    "timeout": {
        "timeout_seconds": 120,  # 从 60 → 120
        "max_retries": 3,
        "advice": "增加超时阈值到120s，启用任务拆分（>60s的任务自动拆为子任务）"
    },
    "dependency": {
        "pre_check": True,
        "max_retries": 2,
        "advice": "任务执行前自动检查依赖，失败时自动安装缺失包"
    },
    "logic": {
        "max_retries": 1,
        "task_slice_size": "small",
        "advice": "减少重试次数（逻辑错误重试无意义），缩小任务粒度"
    },
    "resource": {
        "max_retries": 1,
        "advice": "检查资源限制，启用流式处理，限制并发任务数"
    },
    "simulation": {
        "advice": "模拟失败，无需调参。切换到真实执行后此类错误消失"
    },
}


def classify_error(error_msg: str) -> str:
    """将错误消息分类"""
    error_lower = error_msg.lower()
    for category, keywords in ERROR_CATEGORIES.items():
        if any(kw in error_lower for kw in keywords):
            return category
    return "unknown"


def load_coder_failures() -> list:
    """加载 coder 相关的失败记录"""
    if not EXECUTIONS_FILE.exists():
        return []
    
    failures = []
    with open(EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("task_type") not in ("code", "refactor"):
                continue
            if entry.get("result", {}).get("success", False):
                continue
            failures.append(entry)
    
    return failures


def generate_review_report() -> str:
    """生成失败复盘报告"""
    failures = load_coder_failures()
    
    if not failures:
        report = f"# Coder-Dispatcher 失败复盘\n\n**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n无失败记录，一切正常 ✅\n"
        REPORT_FILE.write_text(report, encoding="utf-8")
        return report
    
    # 分类统计
    categories = Counter()
    categorized = {}
    for f in failures:
        error_msg = f.get("result", {}).get("error", "unknown")
        cat = classify_error(error_msg)
        categories[cat] += 1
        categorized.setdefault(cat, []).append(f)
    
    # 生成报告
    report = f"""# Coder-Dispatcher 失败复盘

**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**总失败数:** {len(failures)}

## 错误分类统计

| 类型 | 数量 | 占比 | 调参建议 |
|------|------|------|----------|
"""
    
    for cat, count in categories.most_common():
        pct = count / len(failures) * 100
        advice = TUNING_ADVICE.get(cat, {}).get("advice", "需要人工分析")
        report += f"| {cat} | {count} | {pct:.0f}% | {advice} |\n"
    
    # 每种类型的详细记录
    report += "\n## 详细记录\n\n"
    for cat, items in categorized.items():
        report += f"### {cat}（{len(items)} 次）\n\n"
        tuning = TUNING_ADVICE.get(cat, {})
        if tuning.get("advice"):
            report += f"**建议:** {tuning['advice']}\n\n"
        
        for item in items[-5:]:  # 最近5条
            tid = item.get("task_id", "?")
            error = item.get("result", {}).get("error", "?")[:100]
            retries = item.get("retry_count", 0)
            ts = item.get("timestamp", 0)
            dt = datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else "?"
            report += f"- `{tid}` ({dt}): {error} (retries: {retries})\n"
        report += "\n"
    
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"[OK] Coder failure review: {REPORT_FILE}")
    print(f"  Total failures: {len(failures)}")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")
    
    return report


if __name__ == "__main__":
    import sys
    generate_review_report()
