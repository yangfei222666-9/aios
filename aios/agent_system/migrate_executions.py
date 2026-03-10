#!/usr/bin/env python3
"""
AIOS Task Executions 杩佺Щ宸ュ叿
灏嗘棫鏍煎紡鐨勬墽琛岃褰曡浆鎹负缁熶竴鐨勬柊鏍煎紡
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 缁熶竴 Schema 瀛楁瀹氫箟
REQUIRED_FIELDS = [
    "task_id",
    "agent_id",
    "task_type",
    "status",
    "started_at",
    "finished_at",
]

OPTIONAL_FIELDS = [
    "description",
    "duration_ms",
    "success",
    "error_type",
    "error_message",
    "output_summary",
    "output_full",
    "source",
    "trace_id",
    "retry_count",
    "total_attempts",
    "tokens",
    "metadata",
]


def migrate_record(old_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    灏嗘棫鏍煎紡璁板綍杞崲涓烘柊鏍煎紡
    """
    new_record = {}
    
    # 1. task_id - 鐩存帴澶嶅埗
    new_record["task_id"] = old_record.get("task_id", "unknown")
    
    # 2. agent_id - 浠?result.agent 鎻愬彇
    result = old_record.get("result", {})
    new_record["agent_id"] = result.get("agent", "unknown")
    
    # 3. task_type - 鐩存帴澶嶅埗
    new_record["task_type"] = old_record.get("task_type", "other")
    
    # 4. status - 鏍规嵁 result.success 鍒ゆ柇
    success = result.get("success", False)
    new_record["status"] = "completed" if success else "failed"
    
    # 5. description - 鐩存帴澶嶅埗锛堝鐞嗙紪鐮侀棶棰橈級
    desc = old_record.get("description", "")
    try:
        # 灏濊瘯淇鍙兘鐨勭紪鐮侀棶棰?        if isinstance(desc, str):
            new_record["description"] = desc
        else:
            new_record["description"] = str(desc)
    except:
        new_record["description"] = "Description encoding error"
    
    # 6. started_at - 浠?timestamp 璁＄畻
    timestamp = old_record.get("timestamp", 0)
    duration = result.get("duration", 0)
    new_record["started_at"] = timestamp - duration if duration > 0 else timestamp
    
    # 7. finished_at - 浣跨敤 timestamp
    new_record["finished_at"] = timestamp
    
    # 8. duration_ms - 浠?result.duration 杞崲锛堢 -> 姣锛?    if duration > 0:
        new_record["duration_ms"] = int(duration * 1000)
    else:
        new_record["duration_ms"] = 0
    
    # 9. success - 甯冨皵鍊?    new_record["success"] = success
    
    # 10. error_type & error_message - 澶辫触鏃跺～鍏?    if not success:
        output = result.get("output", "")
        # 绠€鍗曠殑閿欒绫诲瀷鎺ㄦ柇
        if "timeout" in output.lower():
            new_record["error_type"] = "timeout"
        elif "network" in output.lower() or "connection" in output.lower():
            new_record["error_type"] = "network_error"
        elif "model" in output.lower() or "api" in output.lower():
            new_record["error_type"] = "model_error"
        else:
            new_record["error_type"] = "unknown"
        
        # 鎴彇閿欒淇℃伅锛堟渶澶?1000 瀛楃锛?        new_record["error_message"] = output[:1000] if output else "No error message"
    else:
        new_record["error_type"] = None
        new_record["error_message"] = None
    
    # 11. output_summary - 鎴愬姛鏃跺～鍏咃紙鏈€澶?500 瀛楃锛?    if success:
        output = result.get("output", "")
        if len(output) > 500:
            new_record["output_summary"] = output[:497] + "..."
        else:
            new_record["output_summary"] = output
    else:
        new_record["output_summary"] = None
    
    # 12. output_full - 瀹屾暣杈撳嚭锛堝彲閫夛級
    new_record["output_full"] = result.get("output", None)
    
    # 13. source - 鏍规嵁 task_type 鎺ㄦ柇
    task_type = new_record["task_type"]
    if task_type == "learning":
        new_record["source"] = "learning_agent"
    else:
        new_record["source"] = "other"
    
    # 14. trace_id - 鏆傛椂涓虹┖锛堟湭鏉ュ彲浠ユ坊鍔狅級
    new_record["trace_id"] = None
    
    # 15. retry_count & total_attempts - 鐩存帴澶嶅埗
    new_record["retry_count"] = old_record.get("retry_count", 0)
    new_record["total_attempts"] = old_record.get("total_attempts", 1)
    
    # 16. tokens - 鐩存帴澶嶅埗
    tokens = result.get("tokens", None)
    if tokens:
        new_record["tokens"] = {
            "input": tokens.get("input", 0),
            "output": tokens.get("output", 0),
            "total": tokens.get("input", 0) + tokens.get("output", 0),
        }
    else:
        new_record["tokens"] = None
    
    # 17. metadata - 淇濈暀鍘熷 result 涓殑鍏朵粬瀛楁
    new_record["metadata"] = {
        "migrated_from": "legacy_format",
        "migration_time": datetime.now().isoformat(),
    }
    
    return new_record


def validate_record(record: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    楠岃瘉璁板綍鏄惁绗﹀悎鏂?Schema
    """
    # 妫€鏌ュ繀濉瓧娈?    for field in REQUIRED_FIELDS:
        if field not in record:
            return False, f"Missing required field: {field}"
    
    # 妫€鏌?status 鏋氫妇鍊?    if record["status"] not in ["completed", "failed", "timeout", "cancelled"]:
        return False, f"Invalid status: {record['status']}"
    
    # 妫€鏌?task_type 鏋氫妇鍊?    valid_types = ["code", "analysis", "monitor", "learning", "improvement", "cleanup", "other"]
    if record["task_type"] not in valid_types:
        return False, f"Invalid task_type: {record['task_type']}"
    
    # 妫€鏌ユ椂闂存埑閫昏緫
    if record["finished_at"] < record["started_at"]:
        return False, "finished_at must be >= started_at"
    
    return True, None


def migrate_file(input_path: Path, output_path: Path, backup: bool = True):
    """
    杩佺Щ鏁翠釜鏂囦欢
    """
    print(f"馃攧 寮€濮嬭縼绉? {input_path}")
    
    # 1. 澶囦唤鍘熸枃浠?    if backup:
        backup_path = input_path.with_suffix(".jsonl.backup")
        if input_path.exists():
            import shutil
            shutil.copy2(input_path, backup_path)
            print(f"鉁?宸插浠藉埌: {backup_path}")
    
    # 2. 璇诲彇鏃ц褰?    old_records = []
    if input_path.exists():
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        old_records.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"鈿狅笍  璺宠繃鏃犳晥璁板綍: {e}")
    
    print(f"馃搳 璇诲彇鍒?{len(old_records)} 鏉℃棫璁板綍")
    
    # 3. 杩佺Щ璁板綍
    new_records = []
    failed_count = 0
    
    for i, old_record in enumerate(old_records, 1):
        try:
            new_record = migrate_record(old_record)
            
            # 楠岃瘉鏂拌褰?            valid, error = validate_record(new_record)
            if not valid:
                print(f"鉂?璁板綍 {i} 楠岃瘉澶辫触: {error}")
                failed_count += 1
                continue
            
            new_records.append(new_record)
        except Exception as e:
            print(f"鉂?璁板綍 {i} 杩佺Щ澶辫触: {e}")
            failed_count += 1
    
    print(f"鉁?鎴愬姛杩佺Щ {len(new_records)} 鏉¤褰?)
    if failed_count > 0:
        print(f"鈿狅笍  澶辫触 {failed_count} 鏉¤褰?)
    
    # 4. 鍐欏叆鏂版枃浠?    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in new_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"馃捑 宸插啓鍏? {output_path}")
    
    # 5. 鐢熸垚杩佺Щ鎶ュ憡
    report = {
        "migration_time": datetime.now().isoformat(),
        "input_file": str(input_path),
        "output_file": str(output_path),
        "total_old_records": len(old_records),
        "total_new_records": len(new_records),
        "failed_records": failed_count,
        "success_rate": f"{len(new_records) / len(old_records) * 100:.1f}%" if old_records else "N/A",
    }
    
    report_path = output_path.parent / "migration_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"馃搫 杩佺Щ鎶ュ憡: {report_path}")
    print("\n鉁?杩佺Щ瀹屾垚锛?)


def main():
    """
    涓诲嚱鏁?    """
    base_dir = Path(__file__).parent
    
    # 榛樿璺緞
    input_file = base_dir / "task_executions_v2.jsonl"
    output_file = base_dir / "task_executions_v2.jsonl"
    
    # 鏀寔鍛戒护琛屽弬鏁?    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    # 鎵ц杩佺Щ
    migrate_file(input_file, output_file, backup=True)


if __name__ == "__main__":
    main()

