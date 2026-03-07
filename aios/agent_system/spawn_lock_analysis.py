#!/usr/bin/env python3
"""Spawn Lock 48h 复盘分析脚本"""

import json
from datetime import datetime, timedelta

def analyze_spawn_lock():
    # 读取指标
    with open('spawn_lock_metrics.json', 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    # 计算平均延迟
    acquire_total = metrics['acquire_total']
    latency_sum = metrics['acquire_latency_ms_sum']
    avg_latency = latency_sum / acquire_total if acquire_total > 0 else 0
    
    # 计算幂等命中率
    idempotent_hit_total = metrics['idempotent_hit_total']
    hit_rate = (idempotent_hit_total / acquire_total * 100) if acquire_total > 0 else 0
    
    # 计算观测时长（从上线到现在）
    start_time = datetime.fromisoformat('2026-03-06T11:05:00')
    now = datetime.now()
    hours_elapsed = (now - start_time).total_seconds() / 3600
    
    # 计算每小时恢复陈旧锁数量
    stale_recovered = metrics['stale_lock_recovered_total']
    stale_per_hour = stale_recovered / hours_elapsed if hours_elapsed > 0 else 0
    
    print(f'观测时长: {hours_elapsed:.1f} 小时')
    print(f'平均延迟: {avg_latency:.2f} ms')
    print(f'幂等命中率: {hit_rate:.1f}%')
    print(f'幂等命中次数: {idempotent_hit_total}')
    print(f'总获取次数: {acquire_total}')
    print(f'陈旧锁恢复: {stale_recovered} 次')
    print(f'每小时恢复: {stale_per_hour:.2f} 次/小时')
    print()
    
    # 健康度评估
    issues = []
    if avg_latency > 50:
        issues.append('❌ 平均延迟 > 50ms（告警）')
    elif avg_latency > 10:
        issues.append('⚠️ 平均延迟 > 10ms（接近阈值）')
    else:
        issues.append('✅ 平均延迟健康（< 10ms）')
    
    if hit_rate < 1:
        issues.append('❌ 幂等命中率 < 1%（告警）')
    elif hit_rate < 5:
        issues.append('⚠️ 幂等命中率 < 5%（偏低）')
    elif hit_rate > 20:
        issues.append('⚠️ 幂等命中率 > 20%（偏高）')
    else:
        issues.append('✅ 幂等命中率健康（5-20%）')
    
    if stale_per_hour > 10:
        issues.append('❌ 陈旧锁恢复 > 10/小时（告警）')
    elif stale_recovered > 5:
        issues.append('⚠️ 陈旧锁恢复 > 5 次（需关注）')
    else:
        issues.append('✅ 陈旧锁恢复健康（< 5 次）')
    
    print('健康度评估:')
    for issue in issues:
        print(f'  {issue}')
    print()
    
    # 结论
    has_alert = any('❌' in i for i in issues)
    has_warning = any('⚠️' in i for i in issues)
    
    if has_alert:
        conclusion = '❌ 启动方案 B 迁移（触发告警阈值）'
    elif has_warning:
        conclusion = '⚠️ 观察延长 24h（部分指标接近阈值）'
    else:
        conclusion = '✅ 继续使用方案 A（所有指标健康）'
    
    print(f'结论: {conclusion}')
    
    return {
        'hours_elapsed': hours_elapsed,
        'avg_latency': avg_latency,
        'hit_rate': hit_rate,
        'idempotent_hit_total': idempotent_hit_total,
        'acquire_total': acquire_total,
        'stale_recovered': stale_recovered,
        'stale_per_hour': stale_per_hour,
        'issues': issues,
        'conclusion': conclusion
    }

if __name__ == '__main__':
    analyze_spawn_lock()
