#!/usr/bin/env python3
"""测试 Self-Improving Loop"""
from src.self_improving_loop import SelfImprovingLoop
import random

loop = SelfImprovingLoop()

# 模拟任务执行（30% 失败率）
def mock_task():
    if random.random() < 0.3:
        raise Exception('模拟错误：网络超时')
    return {'status': 'success', 'data': '任务完成'}

# 执行 5 次任务
print('=== 执行 5 次任务 ===\n')
for i in range(5):
    result = loop.execute_with_improvement(
        agent_id='test-agent-001',
        task=f'测试任务 {i+1}',
        execute_fn=mock_task
    )
    status = '✅ 成功' if result['success'] else '❌ 失败'
    print(f'[{i+1}] {status} | 改进触发: {result["improvement_triggered"]} | 改进应用: {result["improvement_applied"]}')

# 查看统计
print('\n=== Agent 统计 ===')
stats = loop.get_improvement_stats('test-agent-001')
print(f'Agent ID: {stats["agent_id"]}')
print(f'最后改进: {stats["last_improvement"]}')
print(f'冷却剩余: {stats["cooldown_remaining_hours"]:.1f}h')
