#!/usr/bin/env python3
"""Memory Server 性能基准测试"""

import time
import requests
import statistics

# Memory Server 基准测试
url = 'http://127.0.0.1:7788/query'

# 测试查询
queries = [
    'AIOS 核心能力',
    'Agent 系统架构',
    'Skill 自动创建',
    '备份恢复机制',
    '太极OS 理念'
]

print('🔍 Memory Server 性能测试\n')
print('=' * 50)

results = []
for i, query in enumerate(queries, 1):
    start = time.time()
    try:
        resp = requests.post(url, json={'query': query, 'top_k': 5}, timeout=10)
        elapsed = (time.time() - start) * 1000
        results.append(elapsed)
        status = '✅' if resp.status_code == 200 else '❌'
        print(f'{status} Query {i}: {elapsed:.0f}ms - "{query}"')
    except Exception as e:
        print(f'❌ Query {i}: FAILED - {str(e)[:50]}')

if results:
    print('\n' + '=' * 50)
    print(f'📊 统计结果:')
    print(f'   平均响应: {statistics.mean(results):.0f}ms')
    print(f'   最快: {min(results):.0f}ms')
    print(f'   最慢: {max(results):.0f}ms')
    print(f'   中位数: {statistics.median(results):.0f}ms')
    
    avg = statistics.mean(results)
    if avg < 500:
        print(f'\n✅ 性能优秀 - 平衡模式足够')
    elif avg < 1000:
        print(f'\n⚠️  性能一般 - 可考虑高性能模式')
    else:
        print(f'\n❌ 性能较慢 - 建议切换高性能模式')
else:
    print('\n❌ 所有查询失败 - Memory Server 可能未启动')
