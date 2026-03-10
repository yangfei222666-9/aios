import json
data = json.load(open('lessons.json', encoding='utf-8'))
print(f'类型: {type(data).__name__}')
if isinstance(data, list):
    print(f'经验条目: {len(data)}')
    for item in data[-3:]:
        print(json.dumps(item, ensure_ascii=False)[:120])
elif isinstance(data, dict):
    print(f'keys: {list(data.keys())}')
    for k, v in data.items():
        if isinstance(v, list):
            print(f'  {k}: {len(v)} items')
        else:
            print(f'  {k}: {v}')
