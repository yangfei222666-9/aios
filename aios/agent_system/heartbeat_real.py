#!/usr/bin/env python3
"""
AIOS Heartbeat - Real Execution Mode
真实执行模式：调用 Claude API 生成并执行代码
集成 DataCollector 自动收集数据
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from real_coder import execute_code_task
from data_collector import DataCollector, collect_task, collect_api_call, collect_execution
from paths import TASK_QUEUE as _TASK_QUEUE

# 文件路径
TASK_QUEUE = _TASK_QUEUE
EXECUTION_LOG = Path(__file__).parent / "execution_log_real.jsonl"

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

def process_task_queue():
    """处理任务队列（真实执行）"""
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
            if task_type == "code":
                # 生成 trace_id
                trace_id = DataCollector.generate_trace_id("task")
                start_time = time.time()
                
                # 真实执行代码任务
                result = execute_code_task(description)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                # 收集任务事件
                collect_task(
                    task_id=trace_id,
                    task_type=task_type,
                    description=description,
                    priority=priority,
                    status="success" if result["success"] else "failed",
                    duration_ms=duration_ms,
                    model="claude-sonnet-4-6",
                    error_type=None if result["success"] else "execution_error",
                    error_message=result.get("error") or result["execution"].get("stderr"),
                    metadata={
                        "filepath": result.get("filepath"),
                        "agent": "coder-agent"
                    },
                    trace_id=trace_id
                )
                
                if result["success"]:
                    log(f"      [OK] Coder Agent 完成代码任务")
                    log(f"      📁 代码文件: {result['filepath']}")
                    if result['execution']['stdout']:
                        log(f"      📤 输出: {result['execution']['stdout'][:100]}")
                else:
                    log(f"      [FAIL] 任务失败")
                    if result.get('error'):
                        log(f"      错误: {result['error']}")
                    elif result['execution']['stderr']:
                        log(f"      错误: {result['execution']['stderr'][:100]}")
                
                # 记录执行日志
                execution_record = {
                    "task_type": task_type,
                    "description": description,
                    "priority": priority,
                    "status": "success" if result["success"] else "failed",
                    "filepath": result.get("filepath"),
                    "executed_at": datetime.now().isoformat()
                }
                append_jsonl(EXECUTION_LOG, execution_record)
            
            else:
                # 其他类型任务（暂时模拟）
                log(f"      [WARN] {task_type} 任务暂不支持真实执行，跳过")
            
        except Exception as e:
            log(f"      ✗ 失败: {e}")
    
    # 清空队列
    TASK_QUEUE.unlink(missing_ok=True)
    
    return f"QUEUE_PROCESSED:{len(tasks)}"

def main():
    """主函数"""
    log("=" * 80)
    log("[START] AIOS Heartbeat Started (Real Execution Mode)")
    log("=" * 80)
    
    # 处理任务队列
    result = process_task_queue()
    
    log("=" * 80)
    log("[OK] Heartbeat Completed")
    log("=" * 80)
    print(f"\n{result}")

if __name__ == "__main__":
    main()
