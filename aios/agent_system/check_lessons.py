import json

with open('lessons.json', 'r', encoding='utf-8') as f:
    lessons = json.load(f)

for l in lessons:
    print(f"lesson_id: {l.get('lesson_id')}")
    print(f"error_type: {l.get('error_type')}")
    print(f"error_message: {l.get('error_message','')[:100]}")
    print(f"regeneration_status: {l.get('regeneration_status')}")
    print()
