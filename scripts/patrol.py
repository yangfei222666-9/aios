"""patrol.py - 定时巡检（只读，不执行外部动作）
每小时运行一次，输出结构化事件到 patrol_events.jsonl
事件分级：CRIT/WARN/INFO，同类告警 1 小时内不重复推送
"""
import json, os, time, shutil
from datetime import datetime, timedelta
from pathlib import Path

WS = Path(r'C:\Users\A\.openclaw\workspace')
EVENTS_FILE = WS / 'logs' / 'patrol_events.jsonl'
STATE_FILE = WS / 'memory' / 'patrol_state.json'
COOLDOWN_SECONDS = 3600  # 1 小时去重

# 确保目录存在
EVENTS_FILE.parent.mkdir(exist_ok=True)

# --- State Management ---

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_alerts": {}}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def should_alert(state, event_id):
    """检查是否应该推送（去重）"""
    last = state.get("last_alerts", {}).get(event_id)
    if not last:
        return True
    last_ts = datetime.fromisoformat(last)
    return (datetime.now() - last_ts).total_seconds() > COOLDOWN_SECONDS

def mark_alerted(state, event_id):
    if "last_alerts" not in state:
        state["last_alerts"] = {}
    state["last_alerts"][event_id] = datetime.now().isoformat()

def log_event(level, category, message, should_push=False):
    """记录事件到 JSONL"""
    entry = {
        "ts": datetime.now().isoformat(),
        "level": level,
        "category": category,
        "message": message,
        "push": should_push
    }
    with open(EVENTS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry

# --- Patrol Checks ---

def check_disk_space():
    """检查磁盘空间"""
    total, used, free = shutil.disk_usage("C:\\")
    usage_pct = (used / total) * 100
    
    if usage_pct > 95:
        return ("CRIT", "disk_space", f"C盘空间严重不足：{usage_pct:.1f}% 已用")
    elif usage_pct > 90:
        return ("WARN", "disk_space", f"C盘空间不足：{usage_pct:.1f}% 已用")
    else:
        return ("INFO", "disk_space", f"C盘空间正常：{usage_pct:.1f}% 已用")

def check_aram_data():
    """检查 ARAM 数据更新时间"""
    db_path = Path(os.environ['USERPROFILE']) / 'Desktop' / 'ARAM-Helper' / 'aram_data.json'
    
    if not db_path.exists():
        return ("CRIT", "aram_data", "ARAM 数据库文件不存在")
    
    try:
        mtime = db_path.stat().st_mtime
        age_days = (time.time() - mtime) / 86400
        
        if age_days > 14:
            return ("WARN", "aram_data", f"ARAM 数据已 {int(age_days)} 天未更新")
        else:
            return ("INFO", "aram_data", f"ARAM 数据正常（{int(age_days)} 天前更新）")
    except:
        return ("WARN", "aram_data", "ARAM 数据库读取异常")

def check_memory_files():
    """检查关键记忆文件"""
    critical_files = [
        WS / 'MEMORY.md',
        WS / 'SOUL.md',
        WS / 'memory' / 'lessons.json',
        WS / 'memory' / 'selflearn-state.json',
    ]
    
    missing = [f.name for f in critical_files if not f.exists()]
    
    if missing:
        return ("CRIT", "memory_files", f"关键文件缺失: {', '.join(missing)}")
    else:
        return ("INFO", "memory_files", "关键文件完整")

def check_ai_news():
    """检查 AI 新闻是否更新"""
    news_dir = Path(os.environ['USERPROFILE']) / 'Desktop' / 'AI新闻'
    today = datetime.now().strftime('%Y-%m-%d')
    today_file = news_dir / f'{today}-AI新闻日报.md'
    
    if today_file.exists():
        return ("INFO", "ai_news", f"今日 AI 新闻已更新")
    else:
        return ("INFO", "ai_news", "今日 AI 新闻尚未更新")

def check_logs_size():
    """检查日志文件大小"""
    logs_dir = WS / 'logs'
    if not logs_dir.exists():
        return ("INFO", "logs_size", "日志目录不存在")
    
    total_size = sum(f.stat().st_size for f in logs_dir.rglob('*') if f.is_file())
    size_mb = total_size / 1024 / 1024
    
    if size_mb > 100:
        return ("WARN", "logs_size", f"日志文件过大：{size_mb:.1f} MB")
    else:
        return ("INFO", "logs_size", f"日志大小正常：{size_mb:.1f} MB")

# --- Main ---

CHECKS = [
    check_disk_space,
    check_aram_data,
    check_memory_files,
    check_ai_news,
    check_logs_size,
]

def run_patrol():
    state = load_state()
    results = {"CRIT": [], "WARN": [], "INFO": []}
    push_list = []
    
    for check_fn in CHECKS:
        try:
            level, category, message = check_fn()
        except Exception as e:
            level, category, message = "WARN", check_fn.__name__, f"检查异常: {e}"
        
        results[level].append(f"[{category}] {message}")
        
        # 判断是否需要推送
        event_id = f"{level}_{category}"
        should_push = False
        
        if level in ("CRIT", "WARN"):
            if should_alert(state, event_id):
                should_push = True
                push_list.append(f"{level}: [{category}] {message}")
                mark_alerted(state, event_id)
        
        log_event(level, category, message, should_push)
    
    save_state(state)
    return results, push_list

def format_summary(results, push_list):
    lines = [f"巡检报告 {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    lines.append(f"CRIT: {len(results['CRIT'])} | WARN: {len(results['WARN'])} | INFO: {len(results['INFO'])}")
    
    if results['CRIT']:
        lines.append("\nCRIT:")
        for m in results['CRIT']:
            lines.append(f"  {m}")
    
    if results['WARN']:
        lines.append("\nWARN:")
        for m in results['WARN']:
            lines.append(f"  {m}")
    
    if not results['CRIT'] and not results['WARN']:
        lines.append("全部正常")
    
    if push_list:
        lines.append(f"\n需要推送 ({len(push_list)} 条)")
    else:
        lines.append("\n静默: 无需推送")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    results, push_list = run_patrol()
    summary = format_summary(results, push_list)
    print(summary)
    
    # 如果有需要推送的，输出到 stdout（供 cron 捕获）
    if push_list:
        print("\n=== PUSH ===")
        for msg in push_list:
            print(msg)
