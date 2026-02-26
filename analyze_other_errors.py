import json
from collections import Counter

# 读取所有 trace 数据
trace_file = r'C:\Users\A\.openclaw\workspace\aios\agent_system\data\traces\agent_traces.jsonl'

# 已知的错误类型
known_errors = [
    'Timeout after 30s', 
    'Timeout after Ns', 
    'division by zero', 
    '模拟错误', 
    '任务失败', 
    '502 Bad Gateway'
]

other_errors = []
with open(trace_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            trace = json.loads(line.strip())
            if not trace.get('success', True):
                error = trace.get('error', '')
                # 检查是否是"其他"类型错误
                if error and error not in known_errors:
                    other_errors.append({
                        'agent_id': trace.get('agent_id'),
                        'error': error,
                        'task': trace.get('task', ''),
                        'env': trace.get('env', 'unknown')
                    })
        except Exception as e:
            continue

print(f'=== 找到 {len(other_errors)} 个 "other" 错误 ===')
print()

# 按错误类型分组
error_types = Counter([e['error'] for e in other_errors])
print('=== 错误类型分布 ===')
for error, count in error_types.most_common(10):
    print(f'  {error}: {count} 次')

print()

# 按 Agent 分组
agent_errors = Counter([e['agent_id'] for e in other_errors])
print('=== 受影响的 Agent ===')
for agent, count in agent_errors.most_common(10):
    print(f'  {agent}: {count} 次')

print()

# 按环境分组
env_errors = Counter([e['env'] for e in other_errors])
print('=== 环境分布 ===')
for env, count in env_errors.items():
    print(f'  {env}: {count} 次')

print()

# 显示前 5 个样本
print('=== 样本（前 5 个）===')
for i, e in enumerate(other_errors[:5], 1):
    print(f'{i}. Agent: {e["agent_id"]}, Error: {e["error"]}, Task: {e["task"]}')
