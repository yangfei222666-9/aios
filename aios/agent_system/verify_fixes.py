import json

agents = json.load(open('agents.json', encoding='utf-8'))
dispatchers = [a for a in agents if 'dispatcher' in a['agent_id']]

print('Dispatcher stats:')
for a in dispatchers:
    stats = a['stats']
    print(f"  {a['agent_id']}: {stats['tasks_completed']}/{stats['tasks_total']} tasks ({stats['tasks_completed']/stats['tasks_total']*100:.1f}%)")

print(f"\nEvolution Score:")
from evolution_fusion import get_evolution_score
print(f"  {get_evolution_score():.1f}/100")

print(f"\nLessons:")
lessons = json.load(open('lessons.json', encoding='utf-8'))
print(f"  Total: {len(lessons)} real failures")
for l in lessons:
    print(f"    {l['lesson_id'][:12]}: {l['error_type']}")
