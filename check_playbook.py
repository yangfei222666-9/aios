import json

with open('aios/data/playbooks.json', encoding='utf-8') as f:
    data = json.load(f)

pb = [p for p in data if p['id'] == 'pb-021-file-not-found-fix'][0]
print(f"ID: {pb['id']}")
print(f"Name: {pb['name']}")
print(f"Success: {pb['success_count']}")
print(f"Fail: {pb['fail_count']}")
print(f"Enabled: {pb['enabled']}")
