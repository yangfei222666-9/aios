"""alert_fsm.py - 告警闭环状态机
状态流转: OPEN -> ACK -> RESOLVED (允许 ACK -> OPEN 反开)
指纹去重: fingerprint = rule_id + scope + day_bucket
自动恢复: 同 fingerprint 连续恢复 N 次自动 RESOLVED
SLA: CRIT 1h, WARN 24h, INFO 72h
"""
import json, os, sys, io, time, uuid
from datetime import datetime, timedelta

# 只在直接运行时重定向 stdout
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WS = r'C:\Users\A\.openclaw\workspace'
ACTIVE_FILE = os.path.join(WS, 'memory', 'alerts_active.json')
HISTORY_FILE = os.path.join(WS, 'memory', 'alerts_history.jsonl')

SLA_HOURS = {"CRIT": 1, "WARN": 24, "INFO": 72}
AUTO_RESOLVE_COUNT = 2  # 连续恢复 N 次自动 RESOLVED

# --- Storage ---

def load_active():
    if os.path.exists(ACTIVE_FILE):
        with open(ACTIVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_active(alerts):
    with open(ACTIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)

def append_history(entry):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

# --- Fingerprint ---

def make_fingerprint(rule_id, scope="default"):
    day = datetime.now().strftime('%Y-%m-%d')
    return f"{rule_id}:{scope}:{day}"

# --- State Transitions ---

def open_alert(rule_id, severity, message, scope="default", owner="小九"):
    """检测到问题时调用，创建或更新 OPEN 告警"""
    alerts = load_active()
    fp = make_fingerprint(rule_id, scope)

    if fp in alerts:
        # 已存在，更新 hit_count
        alert = alerts[fp]
        alert['hit_count'] = alert.get('hit_count', 1) + 1
        alert['last_hit'] = datetime.now().isoformat()
        alert['recovery_streak'] = 0  # 重置恢复计数
        if alert['status'] == 'ACK':
            # ACK -> OPEN 反开
            alert['status'] = 'OPEN'
            _log_transition(alert, 'ACK', 'OPEN', '问题复发')
        save_active(alerts)
        return alert

    # 新建告警
    alert = {
        'id': uuid.uuid4().hex[:8],
        'fingerprint': fp,
        'rule_id': rule_id,
        'severity': severity,
        'message': message,
        'scope': scope,
        'owner': owner,
        'status': 'OPEN',
        'created_at': datetime.now().isoformat(),
        'last_hit': datetime.now().isoformat(),
        'hit_count': 1,
        'recovery_streak': 0,
        'sla_deadline': (datetime.now() + timedelta(hours=SLA_HOURS.get(severity, 72))).isoformat(),
    }
    alerts[fp] = alert
    _log_transition(alert, None, 'OPEN', f'新告警: {message}')
    save_active(alerts)
    return alert

def record_recovery(rule_id, scope="default"):
    """检测到恢复正常时调用，累计恢复计数，达标自动 RESOLVED"""
    alerts = load_active()
    fp = make_fingerprint(rule_id, scope)

    if fp not in alerts:
        return None

    alert = alerts[fp]
    if alert['status'] == 'RESOLVED':
        return alert

    alert['recovery_streak'] = alert.get('recovery_streak', 0) + 1

    if alert['recovery_streak'] >= AUTO_RESOLVE_COUNT:
        old_status = alert['status']
        alert['status'] = 'RESOLVED'
        alert['resolved_at'] = datetime.now().isoformat()
        _log_transition(alert, old_status, 'RESOLVED', f'连续恢复 {AUTO_RESOLVE_COUNT} 次，自动关闭')
        # 移到历史
        _archive_alert(alerts, fp)
    else:
        save_active(alerts)

    return alert

def ack_alert(alert_id):
    """手动确认告警"""
    alerts = load_active()
    for fp, alert in alerts.items():
        if alert['id'] == alert_id:
            if alert['status'] != 'OPEN':
                return None, f"告警 {alert_id} 状态为 {alert['status']}，无法 ACK"
            alert['status'] = 'ACK'
            alert['acked_at'] = datetime.now().isoformat()
            _log_transition(alert, 'OPEN', 'ACK', '手动确认')
            save_active(alerts)
            return alert, "OK"
    return None, f"告警 {alert_id} 不存在"

def resolve_alert(alert_id, reason="手动关闭"):
    """手动解决告警"""
    alerts = load_active()
    for fp, alert in alerts.items():
        if alert['id'] == alert_id:
            old_status = alert['status']
            alert['status'] = 'RESOLVED'
            alert['resolved_at'] = datetime.now().isoformat()
            _log_transition(alert, old_status, 'RESOLVED', reason)
            _archive_alert(alerts, fp)
            return alert, "OK"
    return None, f"告警 {alert_id} 不存在"

def check_sla():
    """检查 SLA 超时，返回超期告警列表"""
    alerts = load_active()
    now = datetime.now()
    overdue = []

    for fp, alert in alerts.items():
        if alert['status'] in ('OPEN', 'ACK'):
            deadline = datetime.fromisoformat(alert['sla_deadline'])
            if now > deadline:
                alert['sla_breached'] = True
                overdue.append(alert)

    if overdue:
        save_active(alerts)
    return overdue

# --- Internal ---

def _log_transition(alert, from_status, to_status, reason):
    entry = {
        'ts': datetime.now().isoformat(),
        'alert_id': alert['id'],
        'fingerprint': alert['fingerprint'],
        'rule_id': alert['rule_id'],
        'severity': alert['severity'],
        'from': from_status,
        'to': to_status,
        'reason': reason,
    }
    append_history(entry)

def _archive_alert(alerts, fp):
    if fp in alerts:
        del alerts[fp]
    save_active(alerts)

# --- Query ---

def list_active(severity_filter=None):
    alerts = load_active()
    result = list(alerts.values())
    if severity_filter:
        result = [a for a in result if a['severity'] == severity_filter]
    return sorted(result, key=lambda a: a['created_at'], reverse=True)

def stats():
    """统计：新增/处理中/已解决/超SLA，供周报使用"""
    alerts = load_active()
    now = datetime.now()
    s = {'open': 0, 'ack': 0, 'overdue': 0}
    for a in alerts.values():
        if a['status'] == 'OPEN':
            s['open'] += 1
        elif a['status'] == 'ACK':
            s['ack'] += 1
        deadline = datetime.fromisoformat(a['sla_deadline'])
        if now > deadline and a['status'] in ('OPEN', 'ACK'):
            s['overdue'] += 1

    # 今日已解决数从历史里算
    today = datetime.now().strftime('%Y-%m-%d')
    s['resolved_today'] = 0
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get('to') == 'RESOLVED' and e['ts'].startswith(today):
                        s['resolved_today'] += 1
                except:
                    continue
    return s

# --- CLI ---

def cli():
    if len(sys.argv) < 2:
        print("用法: python alert_fsm.py [list|ack|resolve|sla|stats]")
        return

    cmd = sys.argv[1]

    if cmd == 'list':
        active = list_active()
        if not active:
            print("✅ 无活跃告警")
            return
        for a in active:
            sla_left = ""
            deadline = datetime.fromisoformat(a['sla_deadline'])
            remaining = deadline - datetime.now()
            if remaining.total_seconds() > 0:
                hours = remaining.total_seconds() / 3600
                sla_left = f"SLA剩余 {hours:.1f}h"
            else:
                sla_left = "⚠️ SLA已超时"
            print(f"[{a['id']}] {a['severity']} {a['status']} | {a['message']} | {sla_left} | 命中{a['hit_count']}次")

    elif cmd == 'ack':
        if len(sys.argv) < 3:
            print("用法: python alert_fsm.py ack <alert_id>")
            return
        alert, msg = ack_alert(sys.argv[2])
        print(msg if not alert else f"✅ 已确认: [{alert['id']}] {alert['message']}")

    elif cmd == 'resolve':
        if len(sys.argv) < 3:
            print("用法: python alert_fsm.py resolve <alert_id>")
            return
        reason = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else "手动关闭"
        alert, msg = resolve_alert(sys.argv[2], reason)
        print(msg if not alert else f"✅ 已解决: [{alert['id']}] {alert['message']}")

    elif cmd == 'sla':
        overdue = check_sla()
        if not overdue:
            print("✅ 无 SLA 超时告警")
        else:
            print(f"⚠️ {len(overdue)} 个告警超 SLA:")
            for a in overdue:
                print(f"  [{a['id']}] {a['severity']} | {a['message']}")

    elif cmd == 'stats':
        s = stats()
        print(f"📊 告警统计: OPEN={s['open']} ACK={s['ack']} 今日解决={s['resolved_today']} 超SLA={s['overdue']}")

    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    cli()
