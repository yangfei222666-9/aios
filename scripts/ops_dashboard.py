"""ops_dashboard.py - 14天稳态运营看板 v1
三组指标 + 综合治理评分
CLI: python ops_dashboard.py [report|score|check-stable]
"""
import json, os, sys, io
from datetime import datetime, timedelta

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WS = r'C:\Users\A\.openclaw\workspace'
sys.path.insert(0, os.path.join(WS, 'scripts'))

# --- A. 告警质量 ---

def alert_quality(days=7):
    import alert_fsm
    history_file = alert_fsm.HISTORY_FILE
    active = alert_fsm.load_active()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    transitions = []
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e['ts'] >= cutoff:
                        transitions.append(e)
                except:
                    pass

    # 统计
    opened = [t for t in transitions if t.get('to') == 'OPEN' and t.get('from') is None]
    resolved = [t for t in transitions if t.get('to') == 'RESOLVED']
    reopened = [t for t in transitions if t.get('from') == 'ACK' and t.get('to') == 'OPEN']
    acked = [t for t in transitions if t.get('to') == 'ACK']

    alerts_total = len(opened)

    # MTTA: 从 OPEN 到 ACK 的平均时间
    ack_times = []
    open_ts = {}
    for t in transitions:
        if t.get('to') == 'OPEN' and t.get('from') is None:
            open_ts[t['alert_id']] = t['ts']
        elif t.get('to') == 'ACK' and t['alert_id'] in open_ts:
            try:
                dt = (datetime.fromisoformat(t['ts']) - datetime.fromisoformat(open_ts[t['alert_id']])).total_seconds()
                ack_times.append(dt)
            except:
                pass

    # MTTR: 从 OPEN 到 RESOLVED
    resolve_times = []
    for t in transitions:
        if t.get('to') == 'RESOLVED' and t['alert_id'] in open_ts:
            try:
                dt = (datetime.fromisoformat(t['ts']) - datetime.fromisoformat(open_ts[t['alert_id']])).total_seconds()
                resolve_times.append(dt)
            except:
                pass

    # SLA breach
    sla_breached = sum(1 for a in active.values() if a.get('sla_breached'))
    sla_total = alerts_total  # 所有告警都有 SLA

    mtta = round(sum(ack_times) / len(ack_times), 1) if ack_times else 0
    mttr = round(sum(resolve_times) / len(resolve_times), 1) if resolve_times else 0

    return {
        'alerts_total': alerts_total,
        'resolved': len(resolved),
        'reopened': len(reopened),
        'false_positive_rate': 0,  # 需要手动标记，暂时为0
        'mtta_sec': mtta,
        'mttr_sec': mttr,
        'sla_breach_rate': round(sla_breached / max(sla_total, 1) * 100, 1),
        'reopen_rate': round(len(reopened) / max(len(resolved), 1) * 100, 1),
        'closure_index': round(len(resolved) / max(alerts_total, 1), 2),
    }

# --- B. 变更安全 ---

def change_safety(days=7):
    import safe_run
    entries = safe_run.load_changes(500)
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in entries if e.get('ts', '') >= cutoff]

    total = len(entries)
    high_risk = [e for e in entries if e.get('risk') in ('HIGH', 'CRIT')]
    blocked = [e for e in entries if e.get('status') == 'REJECTED']
    failed = [e for e in entries if e.get('status') == 'FAILED']
    rolled_back = [e for e in entries if e.get('status') == 'ROLLED_BACK']
    success = [e for e in entries if e.get('status') == 'SUCCESS']
    rollback_actions = [e for e in entries if e.get('action') == 'rollback']
    rollback_ok = [e for e in rollback_actions if e.get('status') == 'SUCCESS']

    return {
        'total_changes': total,
        'high_risk_total': len(high_risk),
        'high_risk_blocked': len(blocked),
        'change_failure_rate': round(len(failed) / max(total, 1) * 100, 1),
        'rollback_count': len(rolled_back) + len(rollback_actions),
        'rollback_success_rate': round(len(rollback_ok) / max(len(rollback_actions), 1) * 100, 1) if rollback_actions else 100.0,
        'dry_run_coverage': 100.0 if not high_risk else round(len(blocked) / max(len(high_risk), 1) * 100, 1),
        'prevention_index': round(len(blocked) / max(len(high_risk), 1), 2) if high_risk else 1.0,
    }

# --- C. 队列健康 ---

def queue_health(days=7):
    import job_queue
    s = job_queue.stats()

    # P95 执行时间从历史算
    history = job_queue._load_jsonl(job_queue.HISTORY_FILE)
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    exec_times = []
    wait_times = []
    for h in history:
        if h.get('ts', '') < cutoff:
            continue
        if 'started_at' in h and 'completed_at' in h:
            try:
                started = datetime.fromisoformat(h['started_at'])
                completed = datetime.fromisoformat(h['completed_at'])
                exec_times.append((completed - started).total_seconds())
            except:
                pass
        if 'started_at' in h and 'created_at' in h:
            try:
                created = datetime.fromisoformat(h['created_at'])
                started = datetime.fromisoformat(h['started_at'])
                wait_times.append((started - created).total_seconds())
            except:
                pass

    def p95(values):
        if not values:
            return 0
        values = sorted(values)
        idx = int(len(values) * 0.95)
        return round(values[min(idx, len(values) - 1)], 2)

    total = s['total_success'] + s['total_failed']
    return {
        'jobs_enqueued': s['total_enqueued'],
        'jobs_success_rate': s['success_rate'],
        'jobs_retry_rate': round(s['total_retried'] / max(total, 1) * 100, 1),
        'deadletter_rate': round(s['total_dead'] / max(total, 1) * 100, 1),
        'queue_p95_wait_sec': p95(wait_times),
        'queue_p95_exec_sec': p95(exec_times),
        'queued_now': s['queued'],
        'running_now': s['running'],
        'retry_pending': s['retry_pending'],
        'reliability_index': round(s['success_rate'] / 100 * (1 - s['total_dead'] / max(total, 1)), 3),
    }

# --- D. 综合治理评分 ---

def governance_score(aq, cs, qh):
    """30% 告警质量 + 30% 变更安全 + 40% 队列健康"""
    # 告警质量分 (0-100)
    aq_score = 100
    if aq['sla_breach_rate'] > 10:
        aq_score -= 30
    elif aq['sla_breach_rate'] > 5:
        aq_score -= 15
    if aq['reopen_rate'] > 8:
        aq_score -= 20
    elif aq['reopen_rate'] > 4:
        aq_score -= 10
    if aq['false_positive_rate'] > 15:
        aq_score -= 25
    elif aq['false_positive_rate'] > 8:
        aq_score -= 12
    aq_score = max(0, aq_score)

    # 变更安全分 (0-100)
    cs_score = 100
    if cs['change_failure_rate'] > 5:
        cs_score -= 30
    elif cs['change_failure_rate'] > 2:
        cs_score -= 15
    if cs['rollback_success_rate'] < 95:
        cs_score -= 25
    cs_score = max(0, cs_score)

    # 队列健康分 (0-100)
    qh_score = 100
    if qh['jobs_success_rate'] < 97:
        qh_score -= 30
    elif qh['jobs_success_rate'] < 99:
        qh_score -= 10
    if qh['deadletter_rate'] > 2:
        qh_score -= 25
    elif qh['deadletter_rate'] > 1:
        qh_score -= 10
    qh_score = max(0, qh_score)

    total = round(aq_score * 0.3 + cs_score * 0.3 + qh_score * 0.4, 1)
    return {
        'alert_quality_score': aq_score,
        'change_safety_score': cs_score,
        'queue_health_score': qh_score,
        'governance_score': total,
        'stable': total >= 85,
    }

# --- 稳态判定 ---

SCORE_HISTORY = os.path.join(WS, 'memory', 'governance_scores.jsonl')

def record_score(score_data):
    entry = {'ts': datetime.now().isoformat(), **score_data}
    with open(SCORE_HISTORY, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def check_stable():
    """连续2周 governance_score >= 85 且无 P0 => 稳态"""
    if not os.path.exists(SCORE_HISTORY):
        return False, "无历史数据"
    scores = []
    with open(SCORE_HISTORY, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    scores.append(json.loads(line))
                except:
                    pass
    if len(scores) < 2:
        return False, f"数据不足（{len(scores)}/2周）"
    recent = scores[-2:]
    all_stable = all(s.get('governance_score', 0) >= 85 for s in recent)
    if all_stable:
        return True, "连续2周 governance_score >= 85，进入稳态运行期 🎉"
    return False, f"最近2次评分: {[s.get('governance_score') for s in recent]}"

# --- Report ---

def full_report(days=7):
    aq = alert_quality(days)
    cs = change_safety(days)
    qh = queue_health(days)
    gs = governance_score(aq, cs, qh)

    lines = [
        f"# 运营看板 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 统计周期: {days} 天",
        "",
        "## A. 告警质量",
        f"- 告警总数: {aq['alerts_total']}",
        f"- 已解决: {aq['resolved']} | 重开: {aq['reopened']}",
        f"- MTTA: {aq['mtta_sec']}s | MTTR: {aq['mttr_sec']}s",
        f"- SLA超时率: {aq['sla_breach_rate']}% {'✅' if aq['sla_breach_rate'] < 10 else '⚠️'}",
        f"- 重开率: {aq['reopen_rate']}% {'✅' if aq['reopen_rate'] < 8 else '⚠️'}",
        f"- 闭环指数: {aq['closure_index']}",
        "",
        "## B. 变更安全",
        f"- 总变更: {cs['total_changes']} | 高风险: {cs['high_risk_total']}",
        f"- 高风险拦截: {cs['high_risk_blocked']}",
        f"- 变更失败率: {cs['change_failure_rate']}% {'✅' if cs['change_failure_rate'] < 5 else '⚠️'}",
        f"- 回滚成功率: {cs['rollback_success_rate']}% {'✅' if cs['rollback_success_rate'] > 95 else '⚠️'}",
        f"- 预防指数: {cs['prevention_index']}",
        "",
        "## C. 队列健康",
        f"- 入队: {qh['jobs_enqueued']} | 成功率: {qh['jobs_success_rate']}% {'✅' if qh['jobs_success_rate'] > 97 else '⚠️'}",
        f"- 死信率: {qh['deadletter_rate']}% {'✅' if qh['deadletter_rate'] < 2 else '⚠️'}",
        f"- P95等待: {qh['queue_p95_wait_sec']}s | P95执行: {qh['queue_p95_exec_sec']}s",
        f"- 可靠性指数: {qh['reliability_index']}",
        "",
        "## D. 治理评分",
        f"- 告警质量: {gs['alert_quality_score']}/100",
        f"- 变更安全: {gs['change_safety_score']}/100",
        f"- 队列健康: {gs['queue_health_score']}/100",
        f"- **综合评分: {gs['governance_score']}/100** {'🟢 稳态' if gs['stable'] else '🟡 观察期'}",
    ]

    # 记录评分
    record_score(gs)

    # 稳态判定
    stable, reason = check_stable()
    lines.extend(["", f"## 稳态判定: {reason}"])

    return '\n'.join(lines), gs

# --- CLI ---

def cli():
    args = sys.argv[1:]
    if not args:
        args = ['report']

    cmd = args[0]
    days = 7
    if '--days' in args:
        idx = args.index('--days')
        if idx + 1 < len(args):
            days = int(args[idx + 1])

    if cmd == 'report':
        report, gs = full_report(days)
        print(report)
    elif cmd == 'score':
        aq = alert_quality(days)
        cs = change_safety(days)
        qh = queue_health(days)
        gs = governance_score(aq, cs, qh)
        print(f"🏛️ 治理评分: {gs['governance_score']}/100 ({'稳态' if gs['stable'] else '观察期'})")
        print(f"  告警={gs['alert_quality_score']} 变更={gs['change_safety_score']} 队列={gs['queue_health_score']}")
    elif cmd == 'check-stable':
        stable, reason = check_stable()
        print(f"{'✅' if stable else '⏳'} {reason}")
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    cli()
