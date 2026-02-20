import sys, json
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\aios')
from core.engine import load_events

# 1. 查致命事件
events = load_events(days=1)
crit_events = [e for e in events if e.get('severity') == 'CRIT']
print('=== 致命事件 ===')
print(f'数量: {len(crit_events)}')
for e in crit_events[:3]:
    print(json.dumps(e, ensure_ascii=False, indent=2))

# 2. 查死循环
from learning.insight import detect_loops
loops = detect_loops(events)
print('\n=== 疑似死循环 ===')
print(f'数量: {len(loops)}')
for sig, count in loops[:3]:
    print(f'{sig}: {count} 次')
    matching = [e for e in events if e.get('signature') == sig][:2]
    for m in matching:
        ts = m.get('ts', '')
        layer = m.get('layer', '')
        ok = m.get('ok', '')
        err = m.get('err', '')[:80]
        print(f'  {ts} {layer} ok={ok} err={err}')

