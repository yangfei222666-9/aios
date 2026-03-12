import json

with open('alerts.jsonl', 'r', encoding='utf-8') as f:
    alerts = [json.loads(line) for line in f if line.strip()]

for alert in alerts:
    alert['sent'] = True

with open('alerts.jsonl', 'w', encoding='utf-8') as f:
    for alert in alerts:
        f.write(json.dumps(alert, ensure_ascii=False) + '\n')

print('All alerts marked as sent')
