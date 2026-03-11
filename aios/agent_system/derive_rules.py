"""
Lesson -> Rule 提炼器
从 lessons.json 中提取高质量 lesson，生成 rules_derived，写回文件。
太极OS 学习闭环关键步骤。
"""
import json
import os
from datetime import datetime

DATA_DIR = 'data'
LESSONS_PATH = os.path.join(DATA_DIR, 'lessons.json')
SELFLEARN_PATH = os.path.join(DATA_DIR, 'selflearn-state.json')

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def derive_rules():
    now = datetime.now().isoformat()
    
    # Load lessons
    lessons_data = load_json(LESSONS_PATH)
    items = lessons_data if isinstance(lessons_data, list) else lessons_data.get('lessons', [])
    
    new_rules = []
    updated_lessons = []
    
    for lesson in items:
        lid = lesson.get('lesson_id', '')
        
        # Skip already derived
        if lesson.get('regeneration_status') == 'derived' or lesson.get('status') == 'derived':
            updated_lessons.append(lesson)
            continue
        
        # Only derive from lessons that have recommended_rule and high confidence
        recommended = lesson.get('recommended_rule', '')
        correct_model = lesson.get('correct_model', '')
        confidence = lesson.get('confidence', 0)
        
        if recommended and correct_model and confidence >= 0.8:
            # Create rule
            rule = {
                'rule_id': f'rule_from_{lid}',
                'source_lesson_id': lid,
                'lesson_type': lesson.get('lesson_type', 'unknown'),
                'rule_text': recommended,
                'correct_model': correct_model,
                'trigger_pattern': lesson.get('trigger_pattern', ''),
                'consumer_modules': lesson.get('consumer_modules', []),
                'confidence': confidence,
                'derived_at': now,
                'status': 'active',
                'applied_count': 0,
                'last_applied': None
            }
            new_rules.append(rule)
            
            # Mark lesson as derived
            lesson['regeneration_status'] = 'derived'
            lesson['status'] = 'derived'
            lesson['derived_at'] = now
            lesson['derived_rule_id'] = rule['rule_id']
            print(f'  DERIVED: {lid} -> {rule["rule_id"]}')
            print(f'    Rule: {recommended}')
        elif lesson.get('error_message', '') == 'Simulated failure':
            # Mark simulated failures as archived
            lesson['regeneration_status'] = 'archived'
            lesson['status'] = 'archived'
            lesson['archive_reason'] = 'simulated_failure_no_real_learning'
            print(f'  ARCHIVED: {lid} (simulated failure, no real learning value)')
        elif 'API error: 502' in lesson.get('error_message', ''):
            # Real API error - derive a retry rule
            rule = {
                'rule_id': f'rule_from_{lid}',
                'source_lesson_id': lid,
                'lesson_type': 'api_resilience',
                'rule_text': 'API 502 errors should trigger exponential backoff retry (max 3), then fallback to cached/local data',
                'correct_model': 'transient API failures are normal; system should be resilient with retry + fallback',
                'trigger_pattern': 'API error: 502',
                'consumer_modules': ['task-executor', 'api-client'],
                'confidence': 0.85,
                'derived_at': now,
                'status': 'active',
                'applied_count': 0,
                'last_applied': None
            }
            new_rules.append(rule)
            lesson['regeneration_status'] = 'derived'
            lesson['status'] = 'derived'
            lesson['derived_at'] = now
            lesson['derived_rule_id'] = rule['rule_id']
            print(f'  DERIVED: {lid} -> {rule["rule_id"]}')
            print(f'    Rule: {rule["rule_text"]}')
        
        updated_lessons.append(lesson)
    
    # Save updated lessons
    if isinstance(lessons_data, dict):
        lessons_data['lessons'] = updated_lessons
        if 'rules_derived' not in lessons_data:
            lessons_data['rules_derived'] = []
        lessons_data['rules_derived'].extend(new_rules)
        lessons_data['last_derivation'] = now
    else:
        lessons_data = {
            'lessons': updated_lessons,
            'rules_derived': new_rules,
            'last_derivation': now
        }
    
    save_json(LESSONS_PATH, lessons_data)
    
    # Update selflearn-state
    sl = load_json(SELFLEARN_PATH)
    sl['rules_derived_count'] = sl.get('rules_derived_count', 0) + len(new_rules)
    sl['last_derivation'] = now
    sl['updated_at'] = now
    if 'derivation_history' not in sl:
        sl['derivation_history'] = []
    sl['derivation_history'].append({
        'timestamp': now,
        'new_rules': len(new_rules),
        'archived': sum(1 for l in updated_lessons if l.get('status') == 'archived'),
        'total_rules': sl['rules_derived_count']
    })
    save_json(SELFLEARN_PATH, sl)
    
    return new_rules

if __name__ == '__main__':
    print('=== Lesson -> Rule Derivation ===')
    print(f'Time: {datetime.now().isoformat()}')
    print()
    
    rules = derive_rules()
    
    print()
    print(f'=== Result ===')
    print(f'New rules derived: {len(rules)}')
    for r in rules:
        print(f'  [{r["rule_id"]}] {r["rule_text"][:80]}')
    print()
    print('Done.')
