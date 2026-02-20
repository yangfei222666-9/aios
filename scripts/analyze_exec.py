import sys, json
from collections import defaultdict
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\aios')
from core.engine import load_events

events = load_events(days=1)

# 找所有 exec 工具调用
exec_events = []
for e in events:
    layer = e.get('layer', '')
    if layer == 'TOOL':
        payload = e.get('payload', {})
        name = payload.get('name', '')
        if name == 'exec':
            exec_events.append(e)
    elif e.get('type') == 'tool':
        data = e.get('data', {})
        if data.get('name') == 'exec':
            exec_events.append(e)

print(f'=== exec 调用分析 (共 {len(exec_events)} 次) ===\n')

# 按命令分组
by_command = defaultdict(list)
for e in exec_events:
    payload = e.get('payload', e.get('data', {}))
    ms = payload.get('ms', payload.get('elapsed_ms', e.get('latency_ms', 0)))
    
    # 提取命令（截取前 80 字符）
    cmd = payload.get('command', payload.get('cmd', ''))
    if isinstance(cmd, str):
        cmd_short = cmd[:80]
    else:
        cmd_short = str(cmd)[:80]
    
    by_command[cmd_short].append(ms)

# 按平均耗时排序
sorted_cmds = sorted(by_command.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)

print('最慢的 10 个命令:\n')
for i, (cmd, times) in enumerate(sorted_cmds[:10], 1):
    avg = sum(times) / len(times)
    max_time = max(times)
    count = len(times)
    print(f'{i}. [{count}次] avg={int(avg)}ms max={int(max_time)}ms')
    print(f'   {cmd}')
    print()

# 统计超过 5s 的调用
slow_calls = [e for e in exec_events if (e.get('payload', e.get('data', {})).get('ms', 0) > 5000)]
print(f'\n超过 5s 的调用: {len(slow_calls)} 次')
if slow_calls:
    print('\n详细信息:')
    for e in slow_calls[:5]:
        payload = e.get('payload', e.get('data', {}))
        ms = payload.get('ms', 0)
        cmd = payload.get('command', '')[:100]
        ok = payload.get('ok', True)
        print(f'  {int(ms)}ms {"OK" if ok else "ERR"} {cmd}')
