import json

with open(r'C:\Users\A\.openclaw\workspace\aios\agent_system\lessons.json', encoding='utf-8') as f:
    lessons = json.load(f)

print(f'Total lessons: {len(lessons)}')
print()

for l in lessons:
    if 'docker' in str(l).lower():
        print(f"lesson_id: {l['lesson_id']}")
        print(f"error_type: {l['error_type']}")
        print(f"error_message: {l['error_message'][:200]}")
        print()
