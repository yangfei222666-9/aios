"""alerts.py - 异常分级与自动降噪系统
三级事件: INFO(仅落盘) / WARN(进周报) / CRIT(立即推送)
5条规则: 连续失败 / 数据量骤降 / 关键文件缺失 / API超时率 / 备份失败
冷却机制: 同类事件6小时内只报一次
缓存机制: 结果缓存5分钟，减少重复执行开销
"""
import json, os, time, subprocess, sys, io
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 导入闭环状态机
sys.path.insert(0, os.path.dirname(__file__))
import alert_fsm

WS = r'C:\Users\A\.openclaw\workspace'

# 导入 AIOS dispatcher（感知扫描）
try:
    sys.path.insert(0, os.path.join(WS, 'aios'))
    from core.dispatcher import dispatch as aios_dispatch, get_pending_actions, clear_actions
    HAS_DISPATCHER = True
except ImportError:
    HAS_DISPATCHER = False
PYTHON = r'C:\Program Files\Python312\python.exe'
ALERTS_STATE = os.path.join(WS, 'memory', 'alerts_state.json')
ALERTS_LOG = os.path.join(WS, 'memory', 'alerts_log.jsonl')
ALERTS_CACHE = os.path.join(WS, 'memory', 'alerts_cache.json')
COOLDOWN_HOURS = 6
CACHE_TTL_SECONDS = 300  # 5分钟缓存

# --- Cache Management ---

def load_cache():
    """加载缓存，如果未过期则返回结果"""
    if not os.path.exists(ALERTS_CACHE):
        return None
    
    try:
        with open(ALERTS_CACHE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        cached_at = cache.get('cached_at', 0)
        age = time.time() - cached_at
        
        if age < CACHE_TTL_SECONDS:
            return cache.get('data')
        else:
            return None
    except:
        return None

def save_cache(data):
    """保存结果到缓存"""
    cache = {
        'cached_at': time.time(),
        'data': data
    }
    with open(ALERTS_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# --- State Management ---

def load_state():
    if os.path.exists(ALERTS_STATE):
        with open(ALERTS_STATE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_alerts": {}, "counters": {}}

def save_state(state):
    with open(ALERTS_STATE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def log_event(level, rule, message):
    entry = {
        "ts": datetime.now().isoformat(),
        "level": level,
        "rule": rule,
        "message": message
    }
    with open(ALERTS_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry

def is_cooled_down(state, rule_id):
    last = state.get("last_alerts", {}).get(rule_id)
    if not last:
        return True
    last_ts = datetime.fromisoformat(last)
    return (datetime.now() - last_ts).total_seconds() > COOLDOWN_HOURS * 3600

def mark_alerted(state, rule_id):
    if "last_alerts" not in state:
        state["last_alerts"] = {}
    state["last_alerts"][rule_id] = datetime.now().isoformat()
    if "counters" not in state:
        state["counters"] = {}
    state["counters"][rule_id] = state["counters"].get(rule_id, 0) + 1

# --- Rule Checks ---

def check_consecutive_failures(state):
    """规则1: autolearn smoke 连续失败"""
    try:
        r = subprocess.run([PYTHON, '-m', 'autolearn', 'health'],
                          cwd=WS, capture_output=True, text=True, timeout=15)
        if 'FAIL' in r.stdout and '0 FAIL' not in r.stdout:
            return "CRIT", "autolearn smoke 测试有失败项"
        return "INFO", "autolearn smoke 全部通过"
    except:
        return "WARN", "autolearn health 执行超时或异常"

def check_data_drop():
    """规则2: ARAM 数据量骤降"""
    db_path = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'ARAM-Helper', 'aram_data.json')
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        count = len(db)
        if count < 150:
            return "CRIT", f"ARAM 数据库只有 {count} 英雄（预期 172），数据可能损坏"
        elif count < 170:
            return "WARN", f"ARAM 数据库 {count} 英雄，低于预期 172"
        return "INFO", f"ARAM 数据库 {count} 英雄，正常"
    except FileNotFoundError:
        return "CRIT", "ARAM 数据库文件不存在！"
    except:
        return "WARN", "ARAM 数据库读取异常"

def check_critical_files():
    """规则3: 关键文件缺失"""
    critical = [
        os.path.join(WS, 'MEMORY.md'),
        os.path.join(WS, 'SOUL.md'),
        os.path.join(WS, 'memory', 'lessons.json'),
        os.path.join(WS, 'memory', 'selflearn-state.json'),
        os.path.join(WS, 'aios', 'events', 'events.jsonl'),
    ]
    missing = [f for f in critical if not os.path.exists(f)]
    if missing:
        names = [os.path.basename(f) for f in missing]
        return "CRIT", f"关键文件缺失: {', '.join(names)}"
    return "INFO", "关键文件完整"

def check_aios_score():
    """规则4: AIOS evolution score 异常（含API超时率）"""
    try:
        r = subprocess.run([PYTHON, '-m', 'aios', 'score'],
                          cwd=WS, capture_output=True, text=True, timeout=15)
        data = json.loads(r.stdout)
        grade = data.get('grade', 'unknown')
        score = data.get('score', 0)
        if grade == 'critical':
            return "CRIT", f"AIOS 评分 critical ({score:.3f})"
        elif grade == 'degraded':
            return "WARN", f"AIOS 评分 degraded ({score:.3f})"
        return "INFO", f"AIOS 评分 {grade} ({score:.3f})"
    except:
        return "WARN", "AIOS score 执行异常"

def check_backup():
    """规则5: 备份是否正常"""
    backup_dir = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'autolearn_backups')
    if not os.path.isdir(backup_dir):
        return "WARN", "备份目录不存在"
    zips = sorted([f for f in os.listdir(backup_dir) if f.endswith('.zip')])
    if not zips:
        return "WARN", "无备份文件"
    latest = zips[-1]
    latest_path = os.path.join(backup_dir, latest)
    age_hours = (time.time() - os.path.getmtime(latest_path)) / 3600
    size = os.path.getsize(latest_path)
    if age_hours > 48:
        return "WARN", f"最近备份已超过 {int(age_hours)}h ({latest})"
    if size < 100:
        return "CRIT", f"最近备份文件异常小 ({size} bytes): {latest}"
    return "INFO", f"备份正常: {latest} ({round(size/1024/1024, 2)} MB, {int(age_hours)}h ago)"

# --- Main ---

RULES = [
    ("consecutive_failures", "连续失败", check_consecutive_failures),
    ("data_drop", "数据量骤降", check_data_drop),
    ("critical_files", "关键文件缺失", check_critical_files),
    ("aios_score", "API超时/评分", check_aios_score),
    ("backup", "备份状态", check_backup),
]

def run_checks():
    state = load_state()
    results = {"INFO": [], "WARN": [], "CRIT": []}
    notifications = []

    for rule_id, rule_name, check_fn in RULES:
        # 有些 check 需要 state 参数
        try:
            if rule_id == "consecutive_failures":
                level, msg = check_fn(state)
            else:
                level, msg = check_fn()
        except Exception as e:
            level, msg = "WARN", f"{rule_name} 检查异常: {e}"

        full_msg = f"[{rule_name}] {msg}"
        results[level].append(full_msg)
        log_event(level, rule_id, msg)

        # 闭环状态机集成
        if level in ("CRIT", "WARN"):
            alert_fsm.open_alert(rule_id, level, msg)
        else:
            # INFO = 正常，记录恢复
            alert_fsm.record_recovery(rule_id)

        # CRIT 需要实时推送，但要检查冷却
        if level == "CRIT":
            if is_cooled_down(state, rule_id):
                notifications.append(full_msg)
                mark_alerted(state, rule_id)

    # 检查 SLA 超时
    overdue = alert_fsm.check_sla()
    for a in overdue:
        sla_msg = f"⏰ SLA超时: [{a['id']}] {a['severity']} {a['message']}"
        if is_cooled_down(state, f"sla_{a['id']}"):
            notifications.append(sla_msg)
            mark_alerted(state, f"sla_{a['id']}")

    # 感知扫描（dispatcher）
    if HAS_DISPATCHER:
        try:
            aios_dispatch(run_sensors=True)
            actions = get_pending_actions()
            for a in actions:
                pri = a.get("priority", "normal")
                summary = a.get("summary", "")
                if pri == "high":
                    results["WARN"].append(f"[感知] {summary}")
                    log_event("WARN", "sensor", summary)
            if actions:
                clear_actions()
        except Exception:
            pass

    save_state(state)
    return results, notifications

def format_summary(results):
    lines = [f"🔍 异常检查 {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    lines.append(f"CRIT: {len(results['CRIT'])} | WARN: {len(results['WARN'])} | INFO: {len(results['INFO'])}")

    if results['CRIT']:
        lines.append("\n🔴 CRIT:")
        for m in results['CRIT']:
            lines.append(f"  {m}")
    if results['WARN']:
        lines.append("\n🟡 WARN:")
        for m in results['WARN']:
            lines.append(f"  {m}")

    if not results['CRIT'] and not results['WARN']:
        lines.append("🟢 全部正常")

    # 状态机摘要
    s = alert_fsm.stats()
    active_total = s['open'] + s['ack']
    if active_total > 0 or s['overdue'] > 0:
        lines.append(f"\n📋 告警状态: OPEN={s['open']} ACK={s['ack']} 超SLA={s['overdue']}")

    return '\n'.join(lines)

def get_recent_warns(days=7):
    """获取最近N天的 WARN 事件，供周报使用"""
    if not os.path.exists(ALERTS_LOG):
        return []
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    warns = []
    with open(ALERTS_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry['level'] == 'WARN' and entry['ts'] >= cutoff:
                    warns.append(entry)
            except:
                continue
    # 同类合并
    merged = {}
    for w in warns:
        key = w['rule']
        if key not in merged:
            merged[key] = {'rule': key, 'message': w['message'], 'count': 1, 'last': w['ts']}
        else:
            merged[key]['count'] += 1
            merged[key]['last'] = w['ts']
            merged[key]['message'] = w['message']
    return list(merged.values())

if __name__ == '__main__':
    # 尝试从缓存加载
    cached = load_cache()
    if cached:
        print(cached['summary'])
        if cached['notifications']:
            print("\n📢 需要立即推送:")
            for n in cached['notifications']:
                print(f"  {n}")
        else:
            print("\n静默: 无需推送")
        print("\n💾 [缓存命中]")
    else:
        # 缓存未命中，执行检查
        results, notifications = run_checks()
        summary = format_summary(results)
        print(summary)

        if notifications:
            print("\n📢 需要立即推送:")
            for n in notifications:
                print(f"  {n}")
        else:
            print("\n静默: 无需推送")
        
        # 保存到缓存
        save_cache({
            'summary': summary,
            'notifications': notifications,
            'results': results
        })
