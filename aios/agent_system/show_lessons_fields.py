import json
from pathlib import Path

data_dir = Path(r'C:\Users\A\.openclaw\workspace\aios\agent_system\data')

with open(data_dir / 'lessons.json', encoding='utf-8') as f:
    lessons = json.load(f)

# 找有 trigger_pattern 字段的 lesson
for l in lessons['lessons']:
    if l.get('trigger_pattern') or l.get('correct_model'):
        print(json.dumps(l, ensure_ascii=False, indent=2))
        print('---')
        break

# 如果没有，打印所有 lesson 的 key
print('\n=== 所有 lesson 的字段 ===')
for l in lessons['lessons']:
    print(f"{l.get('lesson_id')}: {list(l.keys())}")
