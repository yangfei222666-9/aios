#!/usr/bin/env python3
"""
v4.1.0 定向回归分析
针对 dependency_error / resource_exhausted 的策略分布 + 完整性检查
"""
import json
from pathlib import Path
from collections import Counter

AIOS_DIR = Path(__file__).resolve().parent
REC_LOG = AIOS_DIR / "recommendation_log.jsonl"
EXP_DB = AIOS_DIR / "experience_db_v4.jsonl"

def load_jsonl(path):
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            lines.append(json.loads(line))
        except Exception:
            pass
    return lines

def stats_for_error_type(recs, error_type):
    subset = [r for r in recs if r.get('error_type') == error_type]
    total = len(subset)
    if total == 0:
        return None
    
    exp_hit = sum(1 for r in subset if r.get('source') == 'experience')
    default_count = sum(1 for r in subset if r.get('recommended_strategy') == 'default_recovery')
    
    strat_dist = Counter(r.get('recommended_strategy') for r in subset)
    
    return {
        'total': total,
        'experience_hit': exp_hit,
        'experience_hit_rate': round(exp_hit / total, 4) if total else 0,
        'default_count': default_count,
        'default_ratio': round(default_count / total, 4) if total else 0,
        'strategy_dist': dict(strat_dist),
    }

def overall_stats(recs):
    total = len(recs)
    if total == 0:
        return None
    
    exp_hit = sum(1 for r in recs if r.get('source') == 'experience')
    default_count = sum(1 for r in recs if r.get('recommended_strategy') == 'default_recovery')
    grayscale_skip = sum(1 for r in recs if r.get('source') == 'grayscale_skip')
    
    return {
        'total': total,
        'experience_hit_rate': round(exp_hit / total, 4) if total else 0,
        'default_ratio': round(default_count / total, 4) if total else 0,
        'grayscale_skip_ratio': round(grayscale_skip / total, 4) if total else 0,
    }

def integrity_check(entries):
    idem_keys = [e.get('idem_key') for e in entries if e.get('idem_key')]
    repeats = len(idem_keys) - len(set(idem_keys))
    
    corrupt = sum(1 for e in entries if e.get('strategy') is None or e.get('error_type') is None)
    
    return {
        'total_entries': len(entries),
        'repeat_keys': repeats,
        'corrupt_records': corrupt,
    }

def main():
    print("=" * 70)
    print("v4.1.0 定向回归分析")
    print("=" * 70)
    
    recs = load_jsonl(REC_LOG)
    entries = load_jsonl(EXP_DB)
    
    print(f"\n[数据加载]")
    print(f"  recommendation_log: {len(recs)} 条")
    print(f"  experience_db: {len(entries)} 条")
    
    # 1. dependency_error
    print(f"\n[1] dependency_error 分析")
    dep_stats = stats_for_error_type(recs, 'dependency_error')
    if dep_stats:
        print(f"  总数: {dep_stats['total']}")
        print(f"  experience 命中: {dep_stats['experience_hit']} ({dep_stats['experience_hit_rate']:.1%})")
        print(f"  default_recovery: {dep_stats['default_count']} ({dep_stats['default_ratio']:.1%})")
        print(f"  策略分布:")
        for strat, cnt in sorted(dep_stats['strategy_dist'].items(), key=lambda x: -x[1]):
            print(f"    - {strat}: {cnt}")
    else:
        print("  无数据")
    
    # 2. resource_exhausted
    print(f"\n[2] resource_exhausted 分析")
    res_stats = stats_for_error_type(recs, 'resource_exhausted')
    if res_stats:
        print(f"  总数: {res_stats['total']}")
        print(f"  experience 命中: {res_stats['experience_hit']} ({res_stats['experience_hit_rate']:.1%})")
        print(f"  default_recovery: {res_stats['default_count']} ({res_stats['default_ratio']:.1%})")
        print(f"  策略分布:")
        for strat, cnt in sorted(res_stats['strategy_dist'].items(), key=lambda x: -x[1]):
            print(f"    - {strat}: {cnt}")
    else:
        print("  无数据")
    
    # 3. 完整性检查
    print(f"\n[3] 完整性检查")
    integrity = integrity_check(entries)
    print(f"  总条目: {integrity['total_entries']}")
    print(f"  重复键: {integrity['repeat_keys']} {'✅' if integrity['repeat_keys'] == 0 else '⚠️'}")
    print(f"  损坏记录: {integrity['corrupt_records']} {'✅' if integrity['corrupt_records'] == 0 else '⚠️'}")
    
    # 4. 70% 观察数据
    print(f"\n[4] 70% 灰度观察")
    overall = overall_stats(recs)
    if overall:
        print(f"  总请求数: {overall['total']}")
        print(f"  experience 命中率: {overall['experience_hit_rate']:.1%}")
        print(f"  default 占比: {overall['default_ratio']:.1%}")
        print(f"  灰度跳过比例: {overall['grayscale_skip_ratio']:.1%}")
    else:
        print("  无数据")
    
    print("\n" + "=" * 70)
    print("回归分析完成")
    print("=" * 70)

if __name__ == '__main__':
    main()
