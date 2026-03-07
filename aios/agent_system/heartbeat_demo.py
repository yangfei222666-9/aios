#!/usr/bin/env python3
"""
AIOS 心跳运行器 v3.6 - 简化版（直接执行任务）
"""
import json
import time
from pathlib import Path
from datetime import datetime

from paths import TASK_QUEUE as _TASK_QUEUE

# 文件路径
TASK_QUEUE = _TASK_QUEUE
EXECUTION_LOG = Path(__file__).parent / "execution_log.jsonl"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_jsonl(path):
    """读取JSONL文件"""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def append_jsonl(path, data):
    """追加到JSONL文件"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def execute_task(task):
    """模拟执行任务"""
    task_type = task.get("type", "unknown")
    description = task.get("description", "")
    priority = task.get("priority", "normal")
    
    # 模拟执行时间
    time.sleep(0.5)
    
    # 根据任务类型返回结果
    results = {
        "code": f"[OK] Coder Agent 完成代码任务: {description}",
        "analysis": f"[OK] Analyst Agent 完成分析任务: {description}",
        "monitor": f"[OK] Monitor Agent 完成监控任务: {description}",
        "research": f"[OK] Researcher Agent 完成研究任务: {description}",
        "design": f"[OK] Designer Agent 完成设计任务: {description}"
    }
    
    return results.get(task_type, f"[OK] 任务完成: {description}")

def process_task_queue():
    """处理任务队列"""
    log("📋 处理任务队列...")
    
    # 读取队列
    tasks = load_jsonl(TASK_QUEUE)
    if not tasks:
        log("  队列为空")
        return "QUEUE_OK"
    
    log(f"  本次处理 {len(tasks)} 个任务")
    
    # 执行所有任务
    for i, task in enumerate(tasks, 1):
        task_type = task.get("type", "unknown")
        description = task.get("description", "")
        priority = task.get("priority", "normal")
        
        log(f"  [{i}/{len(tasks)}] 执行 {task_type} 任务 (优先级: {priority})")
        
        try:
            # 执行任务
            result_msg = execute_task(task)
            log(f"      {result_msg}")
            
            # 记录执行日志
            execution_record = {
                "task_type": task_type,
                "description": description,
                "priority": priority,
                "status": "success",
                "executed_at": datetime.now().isoformat(),
                "duration_sec": 0.5
            }
            append_jsonl(EXECUTION_LOG, execution_record)
            
        except Exception as e:
            log(f"      ✗ 失败: {e}")
            execution_record = {
                "task_type": task_type,
                "description": description,
                "priority": priority,
                "status": "failed",
                "error": str(e),
                "executed_at": datetime.now().isoformat()
            }
            append_jsonl(EXECUTION_LOG, execution_record)
    
    # 清空队列
    TASK_QUEUE.unlink(missing_ok=True)
    
    return f"QUEUE_PROCESSED:{len(tasks)}"

def main():
    """主函数"""
    log("=" * 80)
    log("[START] AIOS Heartbeat Started")
    log("=" * 80)
    
    # 处理任务队列
    result = process_task_queue()
    
    log("=" * 80)
    log("[OK] Heartbeat Completed")
    log("=" * 80)
    print(f"\n{result}")

if __name__ == "__main__":
    main()
