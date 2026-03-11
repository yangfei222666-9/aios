import json
from datetime import datetime

sl = json.load(open('data/selflearn-state.json', 'r', encoding='utf-8'))

# Update pending count
lessons = json.load(open('data/lessons.json', 'r', encoding='utf-8'))
items = lessons if isinstance(lessons, list) else lessons.get('lessons', [])
pending = sum(1 for l in items if l.get('status') == 'pending' or l.get('regeneration_status') == 'pending')
derived = sum(1 for l in items if l.get('status') == 'derived')
archived = sum(1 for l in items if l.get('status') == 'archived')

sl['pending_lessons'] = pending
sl['derived_lessons'] = derived
sl['archived_lessons'] = archived
sl['total_lessons'] = len(items)
sl['updated_at'] = datetime.now().isoformat()

# Add learning chain status
sl['learning_chains'] = {
    'lesson_to_rule': {
        'status': 'operational',
        'first_closed_at': '2026-03-12T00:16:19',
        'total_derivations': 1,
        'total_rules_produced': 4
    },
    'github_daily_learning': {
        'status': 'observation_period',
        'started_at': '2026-03-11',
        'observation_day': 2
    }
}

json.dump(sl, open('data/selflearn-state.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

print(f'Updated selflearn-state:')
print(f'  Pending: {pending}')
print(f'  Derived: {derived}')
print(f'  Archived: {archived}')
print(f'  Total: {len(items)}')
print(f'  Learning chains: lesson_to_rule=operational, github=observation_period')
