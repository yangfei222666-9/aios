import sys, json
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\aios')
from core.engine import load_events

events = load_events(days=1)

# 1. 查 SEC 层的 critical 事件
sec_events = [e for e in events if e.get('layer') == 'SEC']
critical = [e for e in sec_events if any(k in str(e.get('event', '')) for k in ('system_crash', 'circuit_breaker'))]

print('=== SEC 层致命事件 ===')
print(f'SEC 总数: {len(sec_events)}')
print(f'Critical 数量: {len(critical)}')
for e in critical[:3]:
    print(json.dumps(e, ensure_ascii=False, indent=2))

# 2. 查死循环：连续 KERNEL 事件
print('\n=== 死循环检测 ===')
consecutive_kernel = 0
deadlock_count = 0
deadlock_positions = []
for i, e in enumerate(events):
    layer = e.get('layer', '')
    if not layer:
        # v0.1 兼容
        t = e.get('type', '')
        if t in ('tool', 'task'):
            layer = 'TOOL'
        elif t in ('health', 'deploy'):
            layer = 'KERNEL'
    
    if layer == 'KERNEL':
        consecutive_kernel += 1
    elif layer == 'TOOL':
        consecutive_kernel = 0
    
    if consecutive_kernel >= 5:
        deadlock_count += 1
        deadlock_positions.append(i)
        consecutive_kernel = 0

print(f'疑似死循环次数: {deadlock_count}')
print(f'位置: {deadlock_positions[:5]}')
if deadlock_positions:
    pos = deadlock_positions[0]
    print(f'\n第一次死循环前后事件:')
    for e in events[max(0, pos-3):pos+2]:
        print(f"  {e.get('ts', '')} {e.get('layer', e.get('type', ''))} {e.get('event', e.get('type', ''))}")
