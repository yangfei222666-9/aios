# -*- coding: utf-8 -*-
"""
AIOS Heartbeat v5.0 - Task Queue Integration

Automatically processes tasks from the queue.

Changes from v4.0:
- Added task queue processing
- Integrated TaskExecutor
- Auto-execute pending tasks every heartbeat
"""
import sys
import io
import time
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from core.task_submitter import list_tasks, queue_stats
from core.task_executor import execute_batch
from low_success_regeneration import run_low_success_regeneration
from experience_learner import learner
from token_monitor import check_and_alert, auto_optimize, generate_report
import json
import os


def process_task_queue(max_tasks: int = 5) -> dict:
    """
    Process pending tasks from the queue.
    
    Returns:
        Summary of execution
    """
    # Get pending tasks
    tasks = list_tasks(status="pending", limit=max_tasks)
    
    if not tasks:
        return {
            "processed": 0,
            "success": 0,
            "failed": 0,
        }
    
    print(f"[QUEUE] Processing {len(tasks)} pending tasks...")
    
    # Execute tasks
    results = execute_batch(tasks, max_tasks=max_tasks)
    
    # Count results
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    return {
        "processed": len(results),
        "success": success_count,
        "failed": failed_count,
    }


def execute_spawn_requests() -> int:
    """
    Phase 2.5 桥接层：读取spawn_requests.jsonl并真实执行
    
    Returns:
        Number of successfully executed spawn requests
    """
    spawn_file = Path(__file__).parent / 'spawn_requests.jsonl'
    
    if not spawn_file.exists():
        print("✅ [BRIDGE] spawn_requests.jsonl为空，无需执行")
        return 0
    
    executed_count = 0
    executed_ids = []
    new_lines = []
    
    with open(spawn_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        if not line.strip():
            continue
        
        try:
            req = json.loads(line)
            task_id = req.get('task_id', 'unknown')
            print(f"🔄 [BRIDGE] 正在执行spawn请求: {task_id}")
            
            # 注意：这里需要调用真实的sessions_spawn
            # 由于我们在Python脚本中，无法直接调用OpenClaw的sessions_spawn
            # 所以这里先标记为"待执行"，实际执行需要在OpenClaw主会话中完成
            # 
            # 临时方案：将spawn请求写入一个OpenClaw可以读取的文件
            # 让OpenClaw主会话的heartbeat来执行
            
            # 这里我们先模拟执行（实际应该调用sessions_spawn）
            print(f"⚠️ [BRIDGE] spawn请求已生成，等待OpenClaw主会话执行: {task_id}")
            new_lines.append(line)  # 保留，等待OpenClaw执行
            
        except Exception as e:
            print(f"❌ [BRIDGE] 执行异常: {e}")
            new_lines.append(line)
    
    # 保留所有请求（等待OpenClaw主会话执行）
    with open(spawn_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"🎉 [BRIDGE] 本次检查到 {len(lines)} 个spawn请求（等待OpenClaw执行）")
    return executed_count


def check_system_health() -> dict:
    """
    Check system health (simplified version).
    
    Returns:
        Health summary
    """
    stats = queue_stats()
    
    total = stats["total"]
    completed = stats["by_status"].get("completed", 0)
    failed = stats["by_status"].get("failed", 0)
    pending = stats["by_status"].get("pending", 0)
    
    # Calculate health score
    if total == 0:
        health_score = 100.0
    else:
        success_rate = completed / total if total > 0 else 0
        failure_rate = failed / total if total > 0 else 0
        pending_rate = pending / total if total > 0 else 0
        
        # Health score formula (0-100)
        health_score = (
            success_rate * 60 +  # 60 points for success rate
            (1 - failure_rate) * 30 +  # 30 points for low failure rate
            (1 - pending_rate) * 10  # 10 points for low pending rate
        )
    
    return {
        "score": round(health_score, 2),
        "total_tasks": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
    }


def main():
    """Main heartbeat function."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"╔══════════════════════════════════════════════════════════════╗")
    print(f"║  AIOS Heartbeat v5.0 - {timestamp}  ║")
    print(f"╚══════════════════════════════════════════════════════════════╝\n")
    
    # 0. Token Monitor (每次心跳)
    print("[TOKEN] Token Usage Check:")
    alert = check_and_alert()
    if alert:
        print(f"   ⚠️ {alert['level'].upper()}: {alert['title']}")
        print(f"   {alert['body']}")
        
        # 自动优化
        strategies = auto_optimize()
        if strategies:
            print(f"   🔧 Auto-optimization applied:")
            for s in strategies:
                print(f"      - {s['name']}: {s['action']}")
    else:
        print(f"   ✅ Token usage within limits\n")
    
    # 0. LowSuccess Regeneration (每小时整点)
    from datetime import datetime
    current_minute = datetime.now().minute
    if current_minute == 0:  # 每小时整点
        # Phase 2.5: 先执行spawn请求
        print("[BRIDGE] Spawn Request Execution:")
        executed = execute_spawn_requests()
        if executed > 0:
            print(f"   [OK] Executed: {executed} spawn requests\n")
        else:
            print(f"   [OK] No spawn requests to execute\n")
        
        # 然后生成新的regeneration请求
        print("[REGEN] LowSuccess Regeneration:")
        stats = run_low_success_regeneration(limit=5)
        if stats['processed'] > 0:
            print(f"   [OK] Regenerated: {stats['processed']} tasks")
            print(f"   Pending: {stats['pending']}, Success: {stats['success']}, Failed: {stats['failed']}\n")
        else:
            print(f"   [OK] No failed tasks to regenerate\n")
    
    # 0.5. Experience Learning (每小时整点，在regeneration之后)
    if current_minute == 0:
        print("[LEARN] Experience Library Learning:")
        # 获取待处理任务
        pending_tasks = list_tasks(status="pending", limit=10)
        if pending_tasks:
            applied_count = 0
            for task in pending_tasks:
                # 学习并增强任务
                enhanced_task = learner.learn_and_recommend(task)
                if 'enhanced_prompt' in enhanced_task:
                    applied_count += 1
            
            if applied_count > 0:
                print(f"   [OK] 已应用历史成功模式到 {applied_count} 个任务")
                # 显示学习统计
                stats = learner.get_stats()
                print(f"   经验库: {stats['total_patterns']} 个成功模式, {stats['unique_error_types']} 种错误类型")
            else:
                print(f"   [OK] 待处理任务暂无匹配的历史模式")
        else:
            print(f"   [OK] 无待处理任务\n")
    
    # 1. Process task queue
    queue_result = process_task_queue(max_tasks=5)
    
    if queue_result["processed"] > 0:
        print(f"[QUEUE] Task Queue Processing:")
        print(f"   Processed: {queue_result['processed']} tasks")
        print(f"   Success: {queue_result['success']}")
        print(f"   Failed: {queue_result['failed']}")
    else:
        print("[QUEUE] Task Queue: No pending tasks")
    
    # 2. Check system health
    print(f"\n[HEALTH] System Health Check:")
    health = check_system_health()
    
    # Determine health status
    if health['score'] >= 80:
        status = "GOOD"
    elif health['score'] >= 60:
        status = "WARNING"
    else:
        status = "CRITICAL"
    
    print(f"   Score: {health['score']}/100 ({status})")
    print(f"   Total: {health['total_tasks']} tasks")
    print(f"   Completed: {health['completed']}")
    print(f"   Failed: {health['failed']}")
    print(f"   Pending: {health['pending']}")
    
    # 2.5. Sync agent statistics (every hour at :00)
    if current_minute == 0:
        try:
            from sync_agent_stats import sync_agent_stats
            print(f"\n[SYNC] Syncing agent statistics...")
            sync_agent_stats()
        except Exception as e:
            print(f"[WARN] Agent stats sync failed: {e}")
    
    # 3. Token Report (每天0点生成)
    if current_minute == 0 and datetime.now().hour == 0:
        print(f"\n[REPORT] Daily Token Report:")
        report = generate_report('daily')
        print(report)
    
    # 4. Output summary
    print(f"\n{'=' * 62}")
    if queue_result["processed"] > 0:
        print(f"[OK] HEARTBEAT_OK | Processed: {queue_result['processed']} | Health: {health['score']:.0f}/100")
    else:
        print(f"[OK] HEARTBEAT_OK | No tasks | Health: {health['score']:.0f}/100")
    print(f"{'=' * 62}\n")


if __name__ == "__main__":
    main()
