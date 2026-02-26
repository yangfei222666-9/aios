import json
from collections import Counter

trace_file = r'C:\Users\A\.openclaw\workspace\aios\agent_system\data\traces\agent_traces.jsonl'

def classify_error(error):
    """复制 strategy_learner 的分类逻辑"""
    error_lower = error.lower()
    if any(kw in error_lower for kw in ["timeout", "timed out", "超时"]):
        return "timeout"
    if any(kw in error_lower for kw in ["permission", "denied", "权限"]):
        return "permission"
    if any(kw in error_lower for kw in ["not found", "no such", "找不到"]):
        return "not_found"
    if any(kw in error_lower for kw in ["502", "503", "rate limit"]):
        return "api_error"
    if any(kw in error_lower for kw in ["syntax", "parse", "unexpected"]):
        return "syntax"
    if any(kw in error_lower for kw in ["memory", "oom", "内存"]):
        return "resource"
    return "other"

all_errors = []
with open(trace_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            trace = json.loads(line.strip())
            if not trace.get('success', True):
                error = trace.get('error', '')
                if error:
                    error_type = classify_error(error)
                    all_errors.append({
                        'original': error,
                        'type': error_type,
                        'agent_id': trace.get('agent_id'),
                        'env': trace.get('env', 'unknown')
                    })
        except:
            continue

print(f'=== 总共 {len(all_errors)} 个错误 ===')
print()

# 按类型分组
type_counts = Counter([e['type'] for e in all_errors])
print('=== 错误类型分布 ===')
for error_type, count in type_counts.most_common():
    print(f'  {error_type}: {count} 次')
    # 显示该类型的原始错误样本
    samples = [e['original'] for e in all_errors if e['type'] == error_type]
    unique_samples = list(set(samples))[:5]
    for s in unique_samples:
        print(f'    - {s}')
    print()

# 重点分析 "other" 类型
other_errors = [e for e in all_errors if e['type'] == 'other']
print(f'=== "other" 类型详细分析（{len(other_errors)} 个）===')
print()

# 按 Agent 分组
agent_counts = Counter([e['agent_id'] for e in other_errors])
print('受影响的 Agent:')
for agent, count in agent_counts.most_common():
    print(f'  {agent}: {count} 次')

print()

# 按环境分组
env_counts = Counter([e['env'] for e in other_errors])
print('环境分布:')
for env, count in env_counts.items():
    print(f'  {env}: {count} 次')

print()

# 所有 "other" 错误的原始文本
print('所有 "other" 错误:')
other_unique = list(set([e['original'] for e in other_errors]))
for i, err in enumerate(other_unique, 1):
    print(f'  {i}. {err}')
