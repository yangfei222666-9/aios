#!/usr/bin/env python3
"""
Spawn Lock Monitor - 监控 spawn lock 健康度
"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from paths import SPAWN_LOCKS, SPAWN_LOCK_METRICS, SPAWN_LOCK_MONITOR_STATE, ALERTS

# 配置
STALE_THRESHOLD_SEC = 300  # 5分钟
CHECK_INTERVAL_SEC = 60    # 1分钟
ALERT_FILE = ALERTS

def load_locks():
    """加载当前锁状态"""
    if not SPAWN_LOCKS.exists():
        return {}
    with open(SPAWN_LOCKS, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_metrics():
    """加载指标"""
    if not SPAWN_LOCK_METRICS.exists():
        return {}
    with open(SPAWN_LOCK_METRICS, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_metrics(metrics):
    """保存指标"""
    with open(SPAWN_LOCK_METRICS, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def check_stale_locks(locks):
    """检查过期锁"""
    now = time.time()
    stale = []
    for task_id, lock in locks.items():
        acquired_at = lock.get('acquired_at', 0)
        age_sec = now - acquired_at
        if age_sec > STALE_THRESHOLD_SEC:
            stale.append({
                'task_id': task_id,
                'executor': lock.get('executor'),
                'age_sec': age_sec,
                'token': lock.get('token')
            })
    return stale

def alert_stale_locks(stale_locks):
    """告警过期锁"""
    if not stale_locks:
        return
    
    alert = {
        'timestamp': datetime.now().isoformat(),
        'level': 'warning',
        'title': f'⚠️ Spawn Lock Stale ({len(stale_locks)} locks)',
        'body': f'检测到 {len(stale_locks)} 个过期锁（超过 {STALE_THRESHOLD_SEC}s）\n\n' +
                '\n'.join([f"- {l['task_id']} ({l['executor']}, {l['age_sec']:.0f}s)" for l in stale_locks]),
        'sent': False
    }
    
    with open(ALERT_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(alert, ensure_ascii=False) + '\n')

def monitor_loop():
    """监控循环"""
    print("[MONITOR] Spawn Lock Monitor started")
    
    while True:
        try:
            locks = load_locks()
            metrics = load_metrics()
            
            # 检查过期锁
            stale = check_stale_locks(locks)
            
            # 更新指标
            metrics['last_check'] = datetime.now().isoformat()
            metrics['active_locks'] = len(locks)
            metrics['stale_locks'] = len(stale)
            save_metrics(metrics)
            
            # 告警
            if stale:
                alert_stale_locks(stale)
                print(f"[WARN] {len(stale)} stale locks detected")
            else:
                print(f"[OK] {len(locks)} active locks, all healthy")
            
            time.sleep(CHECK_INTERVAL_SEC)
        
        except KeyboardInterrupt:
            print("\n[MONITOR] Stopped")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(CHECK_INTERVAL_SEC)

if __name__ == '__main__':
    monitor_loop()
