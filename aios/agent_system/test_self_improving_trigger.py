#!/usr/bin/env python3
"""测试 Self-Improving Loop - 触发自动改进"""
from src.self_improving_loop import SelfImprovingLoop
import random

loop = SelfImprovingLoop()

# 模拟任务执行（80% 失败率，触发改进）
def mock_task():
    if random.random() < 0.8:
        raise Exception('模拟错误：网络超时')
    return {'status': 'success', 'data': '任务完成'}

# 执行 10 次任务（预期会触发改进）
print('=== 执行 10 次任务（高失败率）===\n')
for i in range(10):
    result = loop.execute_with_improvement(
        agent_id='test-agent-002',
        task=f'测试任务 {i+1}',
        execute_fn=mock_task
    )
    status = '✅ 成功' if result['success'] else '❌ 失败'
    improved = '🔧 改进' if result['improvement_triggered'] else ''
    print(f'[{i+1}] {status} {improved} | 改进应用: {result["improvement_applied"]}')

# 查看统计
print('\n=== Agent 统计 ===')
stats = loop.get_improvement_stats('test-agent-002')
print(f'Agent ID: {stats["agent_id"]}')
print(f'最后改进: {stats["last_improvement"]}')
print(f'冷却剩余: {stats["cooldown_remaining_hours"]:.1f}h')

# 查看全局统计
print('\n=== 全局统计 ===')
global_stats = loop.get_improvement_stats()
print(f'总 Agent 数: {global_stats["total_agents"]}')
print(f'总改进次数: {global_stats["total_improvements"]}')
print(f'已改进 Agent: {global_stats["agents_improved"]}')
