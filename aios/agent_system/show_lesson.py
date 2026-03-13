import json
from pathlib import Path

data_dir = Path(r'C:\Users\A\.openclaw\workspace\aios\agent_system\data')

with open(data_dir / 'lessons.json', encoding='utf-8') as f:
    lessons = json.load(f)

# 打印第一条完整结构
l = lessons['lessons'][0]
print(json.dumps(l, ensure_ascii=False, indent=2))
