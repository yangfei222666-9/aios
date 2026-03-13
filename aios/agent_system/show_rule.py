import json
from pathlib import Path

data_dir = Path(r'C:\Users\A\.openclaw\workspace\aios\agent_system\data')

with open(data_dir / 'rules.json', encoding='utf-8') as f:
    rules = json.load(f)

# 打印第一条完整结构
r = rules['rules'][0]
print(json.dumps(r, ensure_ascii=False, indent=2))
