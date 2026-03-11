"""
Recalculate evolution score based on current system state.
"""
import json
from datetime import datetime

def recalc():
    # Load current data
    lessons = json.load(open('data/lessons.json', 'r', encoding='utf-8'))
    items = lessons if isinstance(lessons, list) else lessons.get('lessons', [])
    rules = lessons.get('rules_derived', []) if isinstance(lessons, dict) else []
    sl = json.load(open('data/selflearn-state.json', 'r', encoding='utf-8'))
    
    # Score components (0-100 each, weighted)
    scores = {}
    
    # 1. Lesson processing rate (30%)
    total_lessons = len(items)
    processed = sum(1 for l in items if l.get('status') in ('derived', 'archived'))
    scores['lesson_processing'] = (processed / max(total_lessons, 1)) * 100
    
    # 2. Rule derivation (25%)
    total_rules = len(rules)
    scores['rule_derivation'] = min(total_rules * 25, 100)  # 4 rules = 100
    
    # 3. Learning chain health (25%)
    chains = sl.get('learning_chains', {})
    chain_score = 0
    for name, chain in chains.items():
        if chain.get('status') == 'operational':
            chain_score += 50
        elif chain.get('status') == 'observation_period':
            chain_score += 30
    scores['learning_chains'] = min(chain_score, 100)
    
    # 4. System freshness (20%)
    last_run = sl.get('last_run', '')
    last_deriv = sl.get('last_derivation', '')
    freshness = 80  # base
    if last_deriv:
        try:
            dt = datetime.fromisoformat(last_deriv.replace('+08:00', ''))
            hours_ago = (datetime.now() - dt).total_seconds() / 3600
            if hours_ago < 2:
                freshness = 100
            elif hours_ago < 24:
                freshness = 80
            else:
                freshness = 50
        except:
            pass
    scores['freshness'] = freshness
    
    # Weighted total
    weights = {
        'lesson_processing': 0.30,
        'rule_derivation': 0.25,
        'learning_chains': 0.25,
        'freshness': 0.20
    }
    
    total = sum(scores[k] * weights[k] for k in weights)
    
    # Save
    result = {
        'score': round(total, 1),
        'components': {k: round(v, 1) for k, v in scores.items()},
        'lessons_learned': total_lessons,
        'rules_derived': total_rules,
        'last_update': datetime.now().isoformat()
    }
    
    json.dump(result, open('data/evolution_score.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    
    print(f'Evolution Score: {result["score"]}/100')
    print(f'  Lesson Processing: {scores["lesson_processing"]:.1f} (weight 30%)')
    print(f'  Rule Derivation:   {scores["rule_derivation"]:.1f} (weight 25%)')
    print(f'  Learning Chains:   {scores["learning_chains"]:.1f} (weight 20%)')
    print(f'  Freshness:         {scores["freshness"]:.1f} (weight 25%)')
    
    return result

if __name__ == '__main__':
    recalc()
