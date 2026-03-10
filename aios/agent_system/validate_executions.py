#!/usr/bin/env python3
"""
验证 task_executions_v2.jsonl 是否符合统一 Schema
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "schemas" / "task_execution_schema.json"
EXECUTIONS_PATH = BASE_DIR / "task_executions_v2.jsonl"

# 必填字段
REQUIRED_FIELDS = [
    "task_id",
    "agent_id",
    "task_type",
    "status",
    "started_at",
    "finished_at",
]

# 枚举值
VALID_STATUS = ["completed", "failed", "timeout", "cancelled"]
VALID_TASK_TYPES = ["code", "analysis", "monitor", "learning", "improvement", "cleanup", "other"]
VALID_ERROR_TYPES = ["timeout", "network_error", "model_error", "validation_error", "resource_exhausted", "unknown", None]
VALID_SOURCES = ["heartbeat", "user_request", "cron", "self_improving", "learning_agent", "manual", "other"]


def validate_record(record: Dict[str, Any], line_num: int) -> Tuple[bool, List[str]]:
    """
    验证单条记录
    
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    # 1. 检查必填字段
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Line {line_num}: Missing required field '{field}'")
    
    # 2. 检查枚举值
    if "status" in record and record["status"] not in VALID_STATUS:
        errors.append(f"Line {line_num}: Invalid status '{record['status']}', must be one of {VALID_STATUS}")
    
    if "task_type" in record and record["task_type"] not in VALID_TASK_TYPES:
        errors.append(f"Line {line_num}: Invalid task_type '{record['task_type']}', must be one of {VALID_TASK_TYPES}")
    
    if "error_type" in record and record["error_type"] not in VALID_ERROR_TYPES:
        errors.append(f"Line {line_num}: Invalid error_type '{record['error_type']}', must be one of {VALID_ERROR_TYPES}")
    
    if "source" in record and record["source"] not in VALID_SOURCES:
        errors.append(f"Line {line_num}: Invalid source '{record['source']}', must be one of {VALID_SOURCES}")
    
    # 3. 检查时间戳逻辑
    if "started_at" in record and "finished_at" in record:
        if record["finished_at"] < record["started_at"]:
            errors.append(f"Line {line_num}: finished_at ({record['finished_at']}) < started_at ({record['started_at']})")
    
    # 4. 检查条件字段
    status = record.get("status")
    
    if status == "failed":
        if not record.get("error_type"):
            errors.append(f"Line {line_num}: Failed task must have error_type")
        if not record.get("error_message"):
            errors.append(f"Line {line_num}: Failed task must have error_message")
    
    if status == "completed":
        if not record.get("output_summary") and not record.get("output_full"):
            errors.append(f"Line {line_num}: Completed task should have output_summary or output_full")
    
    # 5. 检查字段长度
    if "description" in record and len(record["description"]) > 500:
        errors.append(f"Line {line_num}: description too long ({len(record['description'])} > 500)")
    
    if "output_summary" in record and record["output_summary"] and len(record["output_summary"]) > 500:
        errors.append(f"Line {line_num}: output_summary too long ({len(record['output_summary'])} > 500)")
    
    if "error_message" in record and record["error_message"] and len(record["error_message"]) > 1000:
        errors.append(f"Line {line_num}: error_message too long ({len(record['error_message'])} > 1000)")
    
    # 6. 检查数值范围
    if "duration_ms" in record and record["duration_ms"] < 0:
        errors.append(f"Line {line_num}: duration_ms must be >= 0")
    
    if "retry_count" in record and record["retry_count"] < 0:
        errors.append(f"Line {line_num}: retry_count must be >= 0")
    
    if "total_attempts" in record and record["total_attempts"] < 1:
        errors.append(f"Line {line_num}: total_attempts must be >= 1")
    
    return len(errors) == 0, errors


def validate_file(file_path: Path) -> Dict[str, Any]:
    """
    验证整个文件
    
    Returns:
        {
            "total": int,
            "valid": int,
            "invalid": int,
            "errors": List[str],
            "stats": Dict[str, Any]
        }
    """
    if not file_path.exists():
        return {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "errors": [f"File not found: {file_path}"],
            "stats": {},
        }
    
    total = 0
    valid = 0
    invalid = 0
    all_errors = []
    
    # 统计信息
    stats = {
        "by_status": {},
        "by_task_type": {},
        "by_agent": {},
        "by_source": {},
        "success_rate": 0.0,
        "avg_duration_ms": 0.0,
    }
    
    durations = []
    success_count = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                total += 1
                
                # 验证记录
                is_valid, errors = validate_record(record, line_num)
                
                if is_valid:
                    valid += 1
                    
                    # 收集统计
                    status = record.get("status", "unknown")
                    stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                    
                    task_type = record.get("task_type", "unknown")
                    stats["by_task_type"][task_type] = stats["by_task_type"].get(task_type, 0) + 1
                    
                    agent_id = record.get("agent_id", "unknown")
                    stats["by_agent"][agent_id] = stats["by_agent"].get(agent_id, 0) + 1
                    
                    source = record.get("source", "unknown")
                    stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
                    
                    if record.get("duration_ms"):
                        durations.append(record["duration_ms"])
                    
                    if record.get("success"):
                        success_count += 1
                else:
                    invalid += 1
                    all_errors.extend(errors)
            
            except json.JSONDecodeError as e:
                total += 1
                invalid += 1
                all_errors.append(f"Line {line_num}: JSON decode error: {e}")
    
    # 计算平均值
    if durations:
        stats["avg_duration_ms"] = sum(durations) / len(durations)
    
    if total > 0:
        stats["success_rate"] = (success_count / total) * 100
    
    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "errors": all_errors,
        "stats": stats,
    }


def main():
    """
    主函数
    """
    print("🔍 验证 task_executions_v2.jsonl Schema\n")
    
    result = validate_file(EXECUTIONS_PATH)
    
    print(f"📊 验证结果:")
    print(f"  总记录数: {result['total']}")
    print(f"  有效记录: {result['valid']} ✅")
    print(f"  无效记录: {result['invalid']} ❌")
    
    if result['invalid'] > 0:
        print(f"\n❌ 发现 {result['invalid']} 条无效记录:\n")
        for error in result['errors'][:20]:  # 只显示前 20 个错误
            print(f"  - {error}")
        
        if len(result['errors']) > 20:
            print(f"\n  ... 还有 {len(result['errors']) - 20} 个错误未显示")
        
        sys.exit(1)
    else:
        print("\n✅ 所有记录都符合 Schema！")
    
    # 打印统计信息
    stats = result['stats']
    
    print(f"\n📈 统计信息:")
    print(f"  成功率: {stats['success_rate']:.1f}%")
    print(f"  平均执行时长: {stats['avg_duration_ms']:.0f} ms")
    
    print(f"\n  按状态分布:")
    for status, count in sorted(stats['by_status'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {status}: {count}")
    
    print(f"\n  按任务类型分布:")
    for task_type, count in sorted(stats['by_task_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {task_type}: {count}")
    
    print(f"\n  按 Agent 分布:")
    for agent, count in sorted(stats['by_agent'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {agent}: {count}")
    
    print(f"\n  按来源分布:")
    for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {source}: {count}")


if __name__ == "__main__":
    main()
