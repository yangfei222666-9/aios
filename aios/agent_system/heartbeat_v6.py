#!/usr/bin/env python3
"""
Heartbeat v6.0 - 集成新 Agent
- Error Pattern Learner（每天）
- Task Decomposer（按需）
- Context Manager（自动清理）
- Visualization Generator（每小时）
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def process_task_queue(max_tasks=5):
    """处理任务队列 — 直接调用 v5 的 process_task_queue"""
    try:
        from heartbeat_v5 import process_task_queue as _v5_process
        return _v5_process(max_tasks=max_tasks)
    except Exception as e:
        print(f"  [QUEUE:ERROR] {e}")
        return {"processed": 0, "success": 0, "failed": 0}
from paths import HEARTBEAT_STATE, TASK_QUEUE, TASK_EXECUTIONS, ALERTS


def process_pending_tasks(max_scan=5):
    """
    扫描主账本中 status=="pending" 的任务，推进状态。
    
    职责边界：
    - heartbeat 只做「状态推进 + 超阈值转 blocked + 写 alert」
    - heartbeat 不做真实重新执行（那是调度器的事）
    - 未超阈值的 pending 任务：写一条 enqueue_recovery 信号到 task_queue，
      由调度器在下一轮 pick up 并真正重试
    
    超阈值定义：pending_retry_count >= 3 或 pending_since > 24h
    账本语义：append-only，同 task_id 以最后一条记录为准。

    返回 {"enqueued": int, "blocked": int}
    """
    from datetime import timezone as tz

    ledger = TASK_EXECUTIONS
    if not ledger.exists():
        return {"enqueued": 0, "blocked": 0}

    # ── 读取所有记录 ──
    all_records = []
    with open(ledger, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    all_records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # ── 按 task_id 取最新记录（最后一条覆盖前面的）──
    latest_by_task = {}
    for rec in all_records:
        tid = rec.get("task_id")
        if tid:
            latest_by_task[tid] = rec

    # ── 只处理最终状态仍为 pending 的任务 ──
    pending_tasks = {
        tid: rec for tid, rec in latest_by_task.items()
        if rec.get("status") == "pending"
    }

    enqueued = 0
    blocked = 0

    now_utc = datetime.now(tz=tz.utc)

    for task_id, rec in list(pending_tasks.items())[:max_scan]:
        retry_count = rec.get("pending_retry_count", 0)
        pending_since_str = rec.get("pending_since")

        # ── 判断是否超阈值 → blocked ──
        should_block = False
        if retry_count >= 3:
            should_block = True
        elif pending_since_str:
            try:
                pending_since_dt = datetime.fromisoformat(pending_since_str)
                # 如果 pending_since 是 naive，当作 UTC 处理
                if pending_since_dt.tzinfo is None:
                    pending_since_dt = pending_since_dt.replace(tzinfo=tz.utc)
                age_hours = (now_utc - pending_since_dt).total_seconds() / 3600
                if age_hours > 24:
                    should_block = True
            except (ValueError, TypeError):
                pass

        if should_block:
            # ── 写 blocked 记录到主账本 ──
            blocked_record = dict(rec)
            blocked_record["status"] = "blocked"
            blocked_record["blocked_at"] = now_utc.isoformat()
            blocked_record["updated_at"] = now_utc.isoformat()
            with open(ledger, "a", encoding="utf-8") as f:
                f.write(json.dumps(blocked_record, ensure_ascii=False) + "\n")

            # ── 写 alert ──
            alert = {
                "timestamp": now_utc.isoformat(),
                "level": "error",
                "title": f"Task blocked: {task_id}",
                "body": (
                    f"Agent: {rec.get('agent_id', 'unknown')}\n"
                    f"Error: {rec.get('error_type', 'unknown')} - {rec.get('error_message', '')[:200]}\n"
                    f"Endpoint: {rec.get('endpoint', 'unknown')}\n"
                    f"Pending since: {pending_since_str or 'unknown'}\n"
                    f"Retry count: {retry_count}"
                ),
                "sent": False,
            }
            with open(ALERTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")

            blocked += 1
            continue

        # ── 未超阈值：写恢复信号到 task_queue ──
        recovery_entry = {
            "task_id": task_id,
            "agent_id": rec.get("agent_id", "unknown"),
            "type": rec.get("task_type", "other"),
            "description": rec.get("description", ""),
            "status": "pending_recovery",
            "source": "heartbeat_pending_scan",
            "pending_retry_count": retry_count + 1,
            "pending_since": pending_since_str,
            "enqueued_at": now_utc.isoformat(),
        }
        with open(TASK_QUEUE, "a", encoding="utf-8") as f:
            f.write(json.dumps(recovery_entry, ensure_ascii=False) + "\n")

        # ── 更新主账本的 pending_retry_count ──
        updated_record = dict(rec)
        updated_record["pending_retry_count"] = retry_count + 1
        updated_record["updated_at"] = now_utc.isoformat()
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(updated_record, ensure_ascii=False) + "\n")

        enqueued += 1

    return {"enqueued": enqueued, "blocked": blocked}

def run_error_pattern_learner():
    """运行错误模式学习器（每天一次）"""
    state_file = HEARTBEAT_STATE
    
    # 检查上次运行时间
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        last_run = state.get('error_learner_last_run')
        if last_run:
            last_run_date = datetime.fromisoformat(last_run).date()
            if last_run_date == datetime.now().date():
                return {"status": "skipped", "reason": "already_run_today"}
    else:
        state = {}
    
    # 运行分析
    result = run_command('python agents/error_pattern_learner.py analyze')
    
    if result['success']:
        # 生成修复策略
        strategy_result = run_command('python agents/error_pattern_learner.py generate')
        
        # 更新状态
        state['error_learner_last_run'] = datetime.now().isoformat()
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        return {
            "status": "success",
            "analysis": json.loads(result['output']),
            "strategies": json.loads(strategy_result['output']) if strategy_result['success'] else None
        }
    
    return {"status": "failed", "error": result.get('error')}

def cleanup_contexts():
    """清理过期上下文（每小时一次）"""
    state_file = HEARTBEAT_STATE
    
    # 检查上次清理时间
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        last_cleanup = state.get('context_cleanup_last_run')
        if last_cleanup:
            last_cleanup_time = datetime.fromisoformat(last_cleanup)
            if (datetime.now() - last_cleanup_time).seconds < 3600:
                return {"status": "skipped", "reason": "too_soon"}
    else:
        state = {}
    
    # 运行清理
    result = run_command('python agents/context_manager.py cleanup')
    
    if result['success']:
        state['context_cleanup_last_run'] = datetime.now().isoformat()
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        return {
            "status": "success",
            "result": json.loads(result['output'])
        }
    
    return {"status": "failed", "error": result.get('error')}

def generate_visualization():
    """生成可视化报告（每小时一次）"""
    state_file = HEARTBEAT_STATE
    
    # 检查上次生成时间
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        last_gen = state.get('viz_last_gen')
        if last_gen:
            last_gen_time = datetime.fromisoformat(last_gen)
            if (datetime.now() - last_gen_time).seconds < 3600:
                return {"status": "skipped", "reason": "too_soon"}
    else:
        state = {}
    
    # 生成 HTML 仪表板
    result = run_command('python agents/visualization_generator.py html')
    
    if result['success']:
        state['viz_last_gen'] = datetime.now().isoformat()
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        return {
            "status": "success",
            "result": json.loads(result['output'])
        }
    
    return {"status": "failed", "error": result.get('error')}

def calculate_health_score():
    """计算系统健康度（基于已完成任务的成功率）"""
    queue_file = TASK_QUEUE
    if not queue_file.exists():
        return 100.0  # 文件不存在 = 没任务 = 健康
    
    tasks = []
    with open(queue_file, 'r', encoding='utf-8') as f:
        for line in f:
            tasks.append(json.loads(line))
    
    if not tasks:
        return 100.0  # 空队列 = 健康
    
    completed = sum(1 for t in tasks if t.get('status') == 'completed')
    failed = sum(1 for t in tasks if t.get('status') == 'failed')
    finished = completed + failed
    
    if finished == 0:
        return 100.0  # 没有已完成任务 = 全是 pending = 健康（避免除零）
    
    return (completed / finished * 100)

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print(f"║  AIOS Heartbeat v6.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # 1. 处理任务队列
    print("[QUEUE] Processing task queue...")
    queue_result = process_task_queue(max_tasks=5)
    print(f"   Processed: {queue_result['processed']}")
    print(f"   ✅ Success: {queue_result['success']}")
    print(f"   ❌ Failed: {queue_result['failed']}")
    print()
    
    # 2. 错误模式学习（每天）
    print("[LEARN] Running error pattern learner...")
    learn_result = run_error_pattern_learner()
    if learn_result['status'] == 'success':
        analysis = learn_result.get('analysis', {})
        print(f"   Failed tasks analyzed: {analysis.get('failed_count', 0)}")
        print(f"   New patterns found: {analysis.get('new_patterns', 0)}")
    else:
        print(f"   {learn_result['status']}: {learn_result.get('reason', 'N/A')}")
    print()
    
    # 3. 上下文清理（每小时）
    print("[CONTEXT] Cleaning up expired contexts...")
    context_result = cleanup_contexts()
    if context_result['status'] == 'success':
        result = context_result.get('result', {})
        print(f"   Removed: {result.get('removed_count', 0)} expired contexts")
    else:
        print(f"   {context_result['status']}: {context_result.get('reason', 'N/A')}")
    print()
    
    # 4. 生成可视化（每小时）
    print("[VIZ] Generating visualization...")
    viz_result = generate_visualization()
    if viz_result['status'] == 'success':
        result = viz_result.get('result', {})
        print(f"   Dashboard: {result.get('dashboard_file', 'N/A')}")
    else:
        print(f"   {viz_result['status']}: {viz_result.get('reason', 'N/A')}")
    print()
    
    # 5. 系统健康度
    print("[HEALTH] Checking system health...")
    health = calculate_health_score()
    status_emoji = "🟢" if health >= 80 else "🟡" if health >= 60 else "🔴"
    status_text = "GOOD" if health >= 80 else "WARNING" if health >= 60 else "CRITICAL"
    print(f"   Health Score: {health:.2f}/100 ({status_emoji} {status_text})")
    print()

    # 6. 处理 pending 任务（主任务处理之后、收尾之前）
    print("[PENDING] Processing pending tasks...")
    try:
        pending_result = process_pending_tasks()
        print(f"   Enqueued for recovery: {pending_result['enqueued']}")
        print(f"   Blocked: {pending_result['blocked']}")
        if pending_result['blocked'] > 0:
            print(f"   ⚠️  {pending_result['blocked']} task(s) moved to BLOCKED — check alerts.jsonl")
    except Exception as e:
        print(f"   [PENDING:ERROR] {e}")
        pending_result = {"enqueued": 0, "blocked": 0}
    print()
    
    print("──────────────────────────────────────────────────────────────")
    print(f"✅ HEARTBEAT_OK | Processed: {queue_result['processed']} | Health: {health:.0f}/100")
    print("──────────────────────────────────────────────────────────────")

if __name__ == "__main__":
    main()
