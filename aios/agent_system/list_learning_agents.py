"""统计学习Agent"""
from learning_agents import LEARNING_AGENTS

print('=' * 80)
print('学习 Agent 列表')
print('=' * 80)
print(f'总计: {len(LEARNING_AGENTS)} 个\n')

# 按频率分组
daily = [a for a in LEARNING_AGENTS if a.get('schedule') == 'daily']
every3days = [a for a in LEARNING_AGENTS if a.get('schedule') == 'every_3_days']
weekly = [a for a in LEARNING_AGENTS if a.get('schedule') == 'weekly']
paused = [a for a in LEARNING_AGENTS if a.get('enabled') == False]

print(f'每天运行 ({len(daily)} 个):')
for i, a in enumerate(daily, 1):
    print(f'  {i}. {a["name"]}')

print(f'\n每3天运行 ({len(every3days)} 个):')
for i, a in enumerate(every3days, len(daily)+1):
    print(f'  {i}. {a["name"]}')

print(f'\n每周运行 ({len(weekly)} 个):')
for i, a in enumerate(weekly, len(daily)+len(every3days)+1):
    print(f'  {i}. {a["name"]}')

print(f'\n已暂停 ({len(paused)} 个):')
for i, a in enumerate(paused, len(daily)+len(every3days)+len(weekly)+1):
    print(f'  {i}. {a["name"]}')

print('\n' + '=' * 80)
print(f'活跃: {len(daily) + len(every3days) + len(weekly)} 个')
print(f'暂停: {len(paused)} 个')
print('=' * 80)
