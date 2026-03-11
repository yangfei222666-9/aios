#!/usr/bin/env python3
"""
检查文档 Agent smoke test 结果

从 task_queue.jsonl 和 task_executions.jsonl 中提取结果
"""

import json
from pathlib import Path
from datetime import datetime

def check_smoke_test_results():
    """检查 smoke test 结果"""
    print("=" * 60)
    print("文档 Agent Smoke Test 结果")
    print("=" * 60)
    print(f"检查时间: {datetime.now().isoformat()}\n")
    
    # 1. 检查任务队列状态
    queue_file = Path("data/task_queue.jsonl")
    smoke_tasks = []
    
    if queue_file.exists():
        with open(queue_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    if task.get('task_id', '').startswith('smoke-Docs_'):
                        smoke_tasks.append(task)
    
    print(f"队列中的 smoke test 任务: {len(smoke_tasks)}")
    for task in smoke_tasks:
        print(f"  - {task['agent_id']}: {task['status']}")
    print()
    
    # 2. 检查执行记录
    exec_file = Path("data/task_executions.jsonl")
    smoke_executions = []
    
    if exec_file.exists():
        with open(exec_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if record.get('task_id', '').startswith('smoke-Docs_'):
                            smoke_executions.append(record)
                    except:
                        continue
    
    print(f"执行记录: {len(smoke_executions)}")
    
    if not smoke_executions:
        print("  ⚠️  尚无执行记录，任务可能还在队列中或正在执行")
        print("\n建议:")
        print("  1. 等待 heartbeat 完成")
        print("  2. 或手动触发: python heartbeat_v5.py")
        return
    
    # 3. 分析执行结果
    print("\n" + "=" * 60)
    print("执行结果详情")
    print("=" * 60)
    
    results = {}
    for record in smoke_executions:
        agent_id = record.get('agent_id', 'unknown')
        status = record.get('status', 'unknown')
        duration_ms = record.get('duration_ms', 0)
        duration_s = duration_ms / 1000
        
        if agent_id not in results:
            results[agent_id] = {
                'status': status,
                'duration_s': duration_s,
                'error': record.get('result', {}).get('error', None)
            }
    
    # 按耗时排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]['duration_s'], reverse=True)
    
    for agent_id, result in sorted_results:
        print(f"\n{agent_id}:")
        print(f"  状态: {result['status']}")
        print(f"  耗时: {result['duration_s']:.1f}s")
        
        if result['duration_s'] >= 50:
            print(f"  ⚠️  接近 60s 阈值")
        elif result['duration_s'] >= 60:
            print(f"  ❌ 超过 60s 阈值")
        else:
            print(f"  ✅ 在 60s 内完成")
        
        if result['error']:
            print(f"  错误: {result['error']}")
    
    # 4. 总结
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    
    total = len(results)
    success = sum(1 for r in results.values() if r['status'] == 'completed')
    failed = sum(1 for r in results.values() if r['status'] == 'failed')
    timeout = sum(1 for r in results.values() if r['duration_s'] >= 60)
    near_timeout = sum(1 for r in results.values() if 50 <= r['duration_s'] < 60)
    
    print(f"总任务数: {total}")
    print(f"成功: {success}")
    print(f"失败: {failed}")
    print(f"超时 (≥60s): {timeout}")
    print(f"接近超时 (50-60s): {near_timeout}")
    
    if total > 0:
        avg_duration = sum(r['duration_s'] for r in results.values()) / total
        max_duration = max(r['duration_s'] for r in results.values())
        print(f"\n平均耗时: {avg_duration:.1f}s")
        print(f"最长耗时: {max_duration:.1f}s")
    
    # 5. 建议
    print("\n" + "=" * 60)
    print("建议")
    print("=" * 60)
    
    if timeout > 0:
        print("❌ 仍有任务超时，需要进一步拆分或增加 timeout")
    elif near_timeout > 0:
        print("⚠️  有任务接近超时，建议继续优化或监控")
    else:
        print("✅ 所有任务都在 60s 内完成，拆分有效")

if __name__ == '__main__':
    check_smoke_test_results()
