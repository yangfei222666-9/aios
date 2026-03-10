#!/usr/bin/env python3
"""
Coder-Dispatcher 澶辫触澶嶇洏琛?鎸?timeout/dependency/logic/simulation 鍒嗙被锛屽搴旇皟鍙傚缓璁?
鐢ㄦ硶锛?    python coder_failure_review.py          # 鐢熸垚澶嶇洏鎶ュ憡
    python coder_failure_review.py --fix    # 鑷姩搴旂敤璋冨弬寤鸿
"""

import json
import time
from pathlib import Path
from datetime import datetime
from collections import Counter

AIOS_DIR = Path(__file__).parent
EXECUTIONS_FILE = AIOS_DIR / TASK_EXECUTIONS
REPORT_FILE = AIOS_DIR / "reports" / "coder_failure_review.md"

# 纭繚 reports 鐩綍瀛樺湪
(AIOS_DIR / "reports").mkdir(parents=True, exist_ok=True)

# 閿欒鍒嗙被瑙勫垯
ERROR_CATEGORIES = {
    "timeout": ["timeout", "timed out", "deadline exceeded", "took too long"],
    "dependency": ["import", "module", "dependency", "not found", "no module"],
    "logic": ["assertion", "type error", "value error", "index error", "key error", "logic"],
    "resource": ["memory", "disk", "resource", "oom", "exhausted"],
    "simulation": ["simulated", "simulation"],
}

# 姣忕閿欒绫诲瀷鐨勮皟鍙傚缓璁?TUNING_ADVICE = {
    "timeout": {
        "timeout_seconds": 120,  # 浠?60 鈫?120
        "max_retries": 3,
        "advice": "澧炲姞瓒呮椂闃堝€煎埌120s锛屽惎鐢ㄤ换鍔℃媶鍒嗭紙>60s鐨勪换鍔¤嚜鍔ㄦ媶涓哄瓙浠诲姟锛?
    },
    "dependency": {
        "pre_check": True,
        "max_retries": 2,
        "advice": "浠诲姟鎵ц鍓嶈嚜鍔ㄦ鏌ヤ緷璧栵紝澶辫触鏃惰嚜鍔ㄥ畨瑁呯己澶卞寘"
    },
    "logic": {
        "max_retries": 1,
        "task_slice_size": "small",
        "advice": "鍑忓皯閲嶈瘯娆℃暟锛堥€昏緫閿欒閲嶈瘯鏃犳剰涔夛級锛岀缉灏忎换鍔＄矑搴?
    },
    "resource": {
        "max_retries": 1,
        "advice": "妫€鏌ヨ祫婧愰檺鍒讹紝鍚敤娴佸紡澶勭悊锛岄檺鍒跺苟鍙戜换鍔℃暟"
    },
    "simulation": {
        "advice": "妯℃嫙澶辫触锛屾棤闇€璋冨弬銆傚垏鎹㈠埌鐪熷疄鎵ц鍚庢绫婚敊璇秷澶?
    },
}


def classify_error(error_msg: str) -> str:
    """灏嗛敊璇秷鎭垎绫?""
    error_lower = error_msg.lower()
    for category, keywords in ERROR_CATEGORIES.items():
        if any(kw in error_lower for kw in keywords):
            return category
    return "unknown"


def load_coder_failures() -> list:
    """鍔犺浇 coder 鐩稿叧鐨勫け璐ヨ褰?""
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
    """鐢熸垚澶辫触澶嶇洏鎶ュ憡"""
    failures = load_coder_failures()
    
    if not failures:
        report = f"# Coder-Dispatcher 澶辫触澶嶇洏\n\n**鏃堕棿:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n鏃犲け璐ヨ褰曪紝涓€鍒囨甯?鉁匼n"
        REPORT_FILE.write_text(report, encoding="utf-8")
        return report
    
    # 鍒嗙被缁熻
    categories = Counter()
    categorized = {}
    for f in failures:
        error_msg = f.get("result", {}).get("error", "unknown")
        cat = classify_error(error_msg)
        categories[cat] += 1
        categorized.setdefault(cat, []).append(f)
    
    # 鐢熸垚鎶ュ憡
    report = f"""# Coder-Dispatcher 澶辫触澶嶇洏

**鏃堕棿:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**鎬诲け璐ユ暟:** {len(failures)}

## 閿欒鍒嗙被缁熻

| 绫诲瀷 | 鏁伴噺 | 鍗犳瘮 | 璋冨弬寤鸿 |
|------|------|------|----------|
"""
    
    for cat, count in categories.most_common():
        pct = count / len(failures) * 100
        advice = TUNING_ADVICE.get(cat, {}).get("advice", "闇€瑕佷汉宸ュ垎鏋?)
        report += f"| {cat} | {count} | {pct:.0f}% | {advice} |\n"
    
    # 姣忕绫诲瀷鐨勮缁嗚褰?    report += "\n## 璇︾粏璁板綍\n\n"
    for cat, items in categorized.items():
        report += f"### {cat}锛坽len(items)} 娆★級\n\n"
        tuning = TUNING_ADVICE.get(cat, {})
        if tuning.get("advice"):
            report += f"**寤鸿:** {tuning['advice']}\n\n"
        
        for item in items[-5:]:  # 鏈€杩?鏉?            tid = item.get("task_id", "?")
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


