#!/usr/bin/env python3
"""
task_executions.jsonl 数据清洗脚本
目标：统一字段、补齐缺失值、标准化格式
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 标准字段定义
STANDARD_FIELDS = {
    "timestamp": float,          # Unix 时间戳
    "task_id": str,              # 任务 ID
    "task_type": str,            # 任务类型 (learning/code/analysis/monitor)
    "description": str,          # 任务描述
    "agent_id": str,             # 执行的 Agent ID
    "priority": str,             # 优先级 (high/normal/low)
    "status": str,               # 状态 (completed/failed)
    "result": dict,              # 执行结果
    "retry_count": int,          # 重试次数
    "total_attempts": int,       # 总尝试次数
    "duration": float,           # 执行时长（秒）
    "tokens": dict,              # Token 使用量 {input, output}
    "error": str,                # 错误信息（如果失败）
}

def infer_agent_id(task_id: str, task_type: str) -> str:
    """从 task_id 或 task_type 推断 agent_id"""
    if "GitHub_Researcher" in task_id:
        return "GitHub_Researcher"
    elif "GitHub_Issue_Tracker" in task_id:
        return "GitHub_Issue_Tracker"
    elif "Architecture_Analyst" in task_id:
        return "Architecture_Analyst"
    elif task_type == "learning":
        return "learning-agent"
    elif task_type == "code":
        return "coder-dispatcher"
    elif task_type == "analysis":
        return "analyst-dispatcher"
    elif task_type == "monitor":
        return "monitor-dispatcher"
    else:
        return "unknown-agent"

def infer_priority(task_type: str, description: str) -> str:
    """推断任务优先级"""
    desc_lower = description.lower()
    
    # 高优先级关键词
    if any(kw in desc_lower for kw in ["urgent", "critical", "紧急", "严重", "致命"]):
        return "high"
    
    # 低优先级关键词
    if any(kw in desc_lower for kw in ["cleanup", "清理", "归档", "优化"]):
        return "low"
    
    # 默认 normal
    return "normal"

def extract_duration(result: Dict[str, Any]) -> float:
    """从 result 中提取执行时长"""
    if isinstance(result, dict):
        if "duration" in result:
            return float(result["duration"])
        elif "execution_time" in result:
            return float(result["execution_time"])
    return 0.0

def extract_tokens(result: Dict[str, Any]) -> Dict[str, int]:
    """从 result 中提取 token 使用量"""
    if isinstance(result, dict) and "tokens" in result:
        tokens = result["tokens"]
        if isinstance(tokens, dict):
            return {
                "input": tokens.get("input", 0),
                "output": tokens.get("output", 0)
            }
    return {"input": 0, "output": 0}

def extract_error(result: Dict[str, Any]) -> str:
    """从 result 中提取错误信息"""
    if isinstance(result, dict):
        if "error" in result:
            return str(result["error"])
        elif "error_message" in result:
            return str(result["error_message"])
        elif not result.get("success", True):
            return result.get("output", "Unknown error")
    return ""

def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """清洗单条记录"""
    
    # 1. 提取基础字段
    timestamp = record.get("timestamp", time.time())
    task_id = record.get("task_id", f"task-{int(timestamp)}")
    task_type = record.get("task_type", "unknown")
    description = record.get("description", "No description")
    
    # 2. 推断缺失字段
    agent_id = record.get("agent_id", infer_agent_id(task_id, task_type))
    priority = record.get("priority", infer_priority(task_type, description))
    
    # 3. 处理 result 字段
    result = record.get("result", {})
    success = result.get("success", True) if isinstance(result, dict) else True
    status = "completed" if success else "failed"
    
    # 4. 提取执行信息
    duration = extract_duration(result)
    tokens = extract_tokens(result)
    error = extract_error(result) if not success else ""
    
    # 5. 重试信息
    retry_count = record.get("retry_count", 0)
    total_attempts = record.get("total_attempts", retry_count + 1)
    
    # 6. 构建标准记录
    cleaned = {
        "timestamp": timestamp,
        "task_id": task_id,
        "task_type": task_type,
        "description": description,
        "agent_id": agent_id,
        "priority": priority,
        "status": status,
        "result": result,
        "retry_count": retry_count,
        "total_attempts": total_attempts,
        "duration": duration,
        "tokens": tokens,
        "error": error,
    }
    
    return cleaned

def validate_record(record: Dict[str, Any]) -> bool:
    """验证记录是否符合标准"""
    required_fields = ["timestamp", "task_id", "task_type", "status"]
    
    for field in required_fields:
        if field not in record:
            return False
    
    # 验证字段类型
    if not isinstance(record["timestamp"], (int, float)):
        return False
    if record["status"] not in ["completed", "failed", "pending", "running"]:
        return False
    
    return True

def clean_task_executions(input_file: str, output_file: str, backup: bool = True):
    """清洗 task_executions.jsonl"""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_file}")
        return
    
    # 备份原文件
    if backup:
        backup_path = input_path.with_suffix(f".jsonl.bak.{int(time.time())}")
        input_path.rename(backup_path)
        print(f"✓ 已备份原文件: {backup_path}")
        # 恢复原文件用于读取
        backup_path.rename(input_path)
    
    # 读取并清洗
    cleaned_records: List[Dict[str, Any]] = []
    invalid_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                cleaned = clean_record(record)
                
                if validate_record(cleaned):
                    cleaned_records.append(cleaned)
                else:
                    print(f"⚠️  行 {line_num} 验证失败，已跳过")
                    invalid_count += 1
                    
            except json.JSONDecodeError as e:
                print(f"❌ 行 {line_num} JSON 解析失败: {e}")
                invalid_count += 1
    
    # 写入清洗后的数据
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in cleaned_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # 统计报告
    print(f"\n{'='*60}")
    print(f"数据清洗完成")
    print(f"{'='*60}")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"总记录数: {len(cleaned_records) + invalid_count}")
    print(f"有效记录: {len(cleaned_records)}")
    print(f"无效记录: {invalid_count}")
    print(f"{'='*60}\n")
    
    # 显示字段统计
    if cleaned_records:
        print("字段统计:")
        sample = cleaned_records[0]
        for field, value in sample.items():
            print(f"  - {field}: {type(value).__name__}")
        
        print(f"\n任务类型分布:")
        type_counts = {}
        for r in cleaned_records:
            t = r["task_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  - {t}: {count}")
        
        print(f"\nAgent 分布:")
        agent_counts = {}
        for r in cleaned_records:
            a = r["agent_id"]
            agent_counts[a] = agent_counts.get(a, 0) + 1
        for a, count in sorted(agent_counts.items(), key=lambda x: -x[1]):
            print(f"  - {a}: {count}")
        
        print(f"\n状态分布:")
        status_counts = {}
        for r in cleaned_records:
            s = r["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        for s, count in status_counts.items():
            print(f"  - {s}: {count}")

def main():
    import sys
    
    # 默认路径
    base_dir = Path(__file__).parent
    input_file = base_dir / "task_executions.jsonl"
    output_file = base_dir / "task_executions_cleaned.jsonl"
    
    # 命令行参数
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    print(f"开始清洗数据...")
    print(f"输入: {input_file}")
    print(f"输出: {output_file}\n")
    
    clean_task_executions(str(input_file), str(output_file), backup=True)
    
    # 询问是否替换原文件
    print("\n是否用清洗后的数据替换原文件？(y/N): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y':
        output_file.replace(input_file)
        print(f"✓ 已替换原文件: {input_file}")
    else:
        print(f"✓ 清洗后的数据保存在: {output_file}")

if __name__ == "__main__":
    main()
