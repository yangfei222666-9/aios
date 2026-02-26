import json
from collections import Counter

# 读取最后 100 条事件
with open('aios/events/events.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    events = [json.loads(line) for line in lines[-100:]]

# 1. 最慢的 5 个操作（按 latency_ms 排序）
events_with_latency = [e for e in events if 'latency_ms' in e]
slowest = sorted(events_with_latency, key=lambda x: x['latency_ms'], reverse=True)[:5]

print('=' * 60)
print('最慢的 5 个操作（按耗时排序）')
print('=' * 60)
for i, e in enumerate(slowest, 1):
    print(f'\n{i}. 事件: {e["event"]}')
    print(f'   耗时: {e["latency_ms"]}ms')
    print(f'   层级: {e["layer"]}')
    print(f'   时间: {e.get("ts", "N/A")}')
    if 'payload' in e:
        print(f'   详情: {e["payload"]}')

# 2. 高频操作（出现次数最多的前 5 个）
event_names = [e['event'] for e in events]
freq = Counter(event_names).most_common(5)

print('\n' + '=' * 60)
print('高频操作 TOP 5（出现次数最多）')
print('=' * 60)
for i, (event, count) in enumerate(freq, 1):
    pct = (count / len(events)) * 100
    print(f'{i}. {event}')
    print(f'   出现次数: {count} ({pct:.1f}%)')

# 3. 按层级统计
layer_counter = Counter([e['layer'] for e in events])
print('\n' + '=' * 60)
print('按层级统计')
print('=' * 60)
for layer, count in layer_counter.most_common():
    pct = (count / len(events)) * 100
    print(f'{layer}: {count} ({pct:.1f}%)')

# 4. 统计信息
print('\n' + '=' * 60)
print('统计信息')
print('=' * 60)
print(f'总事件数: {len(events)}')
print(f'有延迟记录的事件: {len(events_with_latency)}')
if events_with_latency:
    avg_latency = sum(e['latency_ms'] for e in events_with_latency) / len(events_with_latency)
    max_latency = max(e['latency_ms'] for e in events_with_latency)
    min_latency = min(e['latency_ms'] for e in events_with_latency)
    print(f'平均延迟: {avg_latency:.2f}ms')
    print(f'最大延迟: {max_latency}ms')
    print(f'最小延迟: {min_latency}ms')

# 5. 错误和警告统计
errors = [e for e in events if e.get('severity') in ['ERR', 'CRIT', 'WARN']]
print(f'\n错误/警告事件: {len(errors)}')
if errors:
    error_types = Counter([e['event'] for e in errors])
    print('错误类型分布:')
    for err_type, count in error_types.most_common():
        print(f'  - {err_type}: {count}')

print('\n' + '=' * 60)
print('优化建议')
print('=' * 60)

# 分析最慢的操作
if slowest:
    top_slow = slowest[0]
    if top_slow['latency_ms'] > 500:
        print(f'\n1. 【高延迟优化】')
        print(f'   - {top_slow["event"]} 耗时 {top_slow["latency_ms"]}ms，建议：')
        if 'reactor.auto_fix' in top_slow['event']:
            print(f'     * 优化自动修复逻辑，减少重试次数')
            print(f'     * 考虑异步执行或超时控制')
        elif 'task' in top_slow['event']:
            print(f'     * 检查任务执行逻辑，是否有阻塞操作')
            print(f'     * 考虑任务分片或并行处理')

# 分析高频操作
if freq:
    top_freq = freq[0]
    if top_freq[1] > 20:
        print(f'\n2. 【高频操作优化】')
        print(f'   - {top_freq[0]} 出现 {top_freq[1]} 次，建议：')
        if 'resource_snapshot' in top_freq[0]:
            print(f'     * 增加快照间隔，减少采样频率')
            print(f'     * 考虑按需采样而非定时采样')
        elif 'task' in top_freq[0]:
            print(f'     * 批量处理任务，减少单次调用')
            print(f'     * 使用任务队列合并相似操作')

# 错误率分析
if errors:
    error_rate = (len(errors) / len(events)) * 100
    print(f'\n3. 【错误率优化】')
    print(f'   - 错误率: {error_rate:.1f}%，建议：')
    if error_rate > 10:
        print(f'     * 检查失败的 auto_fix 操作，优化重试策略')
        print(f'     * 增加错误预检，避免无效操作')
        print(f'     * 添加熔断机制，防止级联失败')

print(f'\n4. 【通用建议】')
print(f'   - 添加事件采样：对高频低价值事件进行采样记录')
print(f'   - 异步处理：将非关键路径操作改为异步执行')
print(f'   - 缓存优化：对重复查询结果进行缓存')
print(f'   - 监控告警：对超过阈值的延迟设置告警')
