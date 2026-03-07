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
    """处理任务队列（原有功能）"""
    # 直接调用 heartbeat_v5.py 的逻辑
    result = run_command('python heartbeat_v5.py')
    
    if result['success']:
        # 解析输出获取处理结果
        output = result['output']
        if 'Processed:' in output:
            import re
            match = re.search(r'Processed: (\d+)', output)
            processed = int(match.group(1)) if match else 0
            match = re.search(r'Success: (\d+)', output)
            success = int(match.group(1)) if match else 0
            match = re.search(r'Failed: (\d+)', output)
            failed = int(match.group(1)) if match else 0
            
            return {
                "processed": processed,
                "success": success,
                "failed": failed
            }
    
    return {"processed": 0, "success": 0, "failed": 0}

from paths import HEARTBEAT_STATE, TASK_QUEUE as _TASK_QUEUE_PATH

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
    """计算系统健康度"""
    queue_file = _TASK_QUEUE_PATH
    if not queue_file.exists():
        return 0.0
    
    tasks = []
    with open(queue_file, 'r', encoding='utf-8') as f:
        for line in f:
            tasks.append(json.loads(line))
    
    if not tasks:
        return 100.0
    
    completed = sum(1 for t in tasks if t.get('status') == 'completed')
    total = len(tasks)
    
    return (completed / total * 100) if total > 0 else 0.0

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
    
    print("──────────────────────────────────────────────────────────────")
    print(f"✅ HEARTBEAT_OK | Processed: {queue_result['processed']} | Health: {health:.0f}/100")
    print("──────────────────────────────────────────────────────────────")

if __name__ == "__main__":
    main()
