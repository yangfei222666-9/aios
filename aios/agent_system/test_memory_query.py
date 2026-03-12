import requests

r = requests.post('http://127.0.0.1:7788/query', json={'query': 'AIOS 系统架构', 'top_k': 3})
print('Status:', r.status_code)
results = r.json().get('results', [])
print('Results:', len(results), 'items')
for item in results[:3]:
    print(f"  - {item['text'][:80]}...")
