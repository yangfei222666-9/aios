"""exec_logger.py - exec 性能埋点（最小侵入）
只记录慢调用（>500ms），用于性能回归检测
"""
import json, time, os
from datetime import datetime
from pathlib import Path

WS = Path(r'C:\Users\A\.openclaw\workspace')
LOG_DIR = WS / 'logs'
LOG_FILE = LOG_DIR / 'exec_perf.jsonl'
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB 滚动切分
SLOW_THRESHOLD_MS = 500

LOG_DIR.mkdir(exist_ok=True)

def log_exec(command: str, elapsed_ms: int, exit_code: int = 0, cached: bool = False, error: str = None):
    """记录 exec 调用（仅慢调用）"""
    if elapsed_ms < SLOW_THRESHOLD_MS:
        return
    
    # 滚动切分
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
        backup = LOG_DIR / f'exec_perf_{int(time.time())}.jsonl'
        LOG_FILE.rename(backup)
    
    # 命令摘要（前 100 字符）
    cmd_summary = command[:100] if len(command) > 100 else command
    
    entry = {
        'ts': datetime.now().isoformat(),
        'cmd': cmd_summary,
        'ms': elapsed_ms,
        'exit_code': exit_code,
        'cached': cached,
    }
    
    if error:
        entry['error'] = error[:200]
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def get_stats(days: int = 1) -> dict:
    """获取最近 N 天的 P95/P99 统计"""
    if not LOG_FILE.exists():
        return {'count': 0, 'p95': 0, 'p99': 0, 'max': 0}
    
    cutoff = time.time() - days * 86400
    times = []
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry['ts']).timestamp()
                if ts >= cutoff:
                    times.append(entry['ms'])
            except:
                continue
    
    if not times:
        return {'count': 0, 'p95': 0, 'p99': 0, 'max': 0}
    
    times.sort()
    count = len(times)
    
    return {
        'count': count,
        'p95': times[int(count * 0.95)] if count > 0 else 0,
        'p99': times[int(count * 0.99)] if count > 0 else 0,
        'max': times[-1] if times else 0,
    }

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        stats = get_stats(days)
        print(f"exec 性能统计（最近 {days} 天）")
        print(f"慢调用次数: {stats['count']}")
        print(f"P95: {stats['p95']}ms")
        print(f"P99: {stats['p99']}ms")
        print(f"Max: {stats['max']}ms")
    else:
        print("Usage: python exec_logger.py stats [days]")
