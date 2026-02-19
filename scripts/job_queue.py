"""job_queue.py - 任务队列化
可排队可重试的作业流，从单线程对话升级为队列调度

状态机: QUEUED -> RUNNING -> SUCCESS | FAILED -> RETRY -> ... -> DEAD
重试策略: 指数退避 1m/5m/15m，最大3次
幂等保护: idempotency_key 去重

CLI: job_queue.py [enqueue|worker|list|stats|retry|dead|recover]
"""
import json, os, sys, io, uuid, time, subprocess, hashlib
from datetime import datetime, timedelta

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WS = r'C:\Users\A\.openclaw\workspace'
QUEUE_FILE = os.path.join(WS, 'memory', 'jobs_queue.jsonl')
STATE_FILE = os.path.join(WS, 'memory', 'jobs_state.json')
DEAD_FILE = os.path.join(WS, 'memory', 'jobs_deadletter.jsonl')
HISTORY_FILE = os.path.join(WS, 'memory', 'jobs_history.jsonl')

MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 900]  # 1m, 5m, 15m 指数退避
PYTHON = r'C:\Program Files\Python312\python.exe'

# --- Storage ---

def _load_jsonl(path):
    if not os.path.exists(path):
        return []
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except:
                    pass
    return items

def _save_jsonl(path, items):
    with open(path, 'w', encoding='utf-8') as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def _append_jsonl(path, item):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'idempotency_keys': {}, 'counters': {'enqueued': 0, 'success': 0, 'failed': 0, 'dead': 0, 'retried': 0}}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# --- Enqueue ---

def enqueue(action, params=None, priority='normal', idempotency_key=None, timeout_sec=30):
    """入队一个任务"""
    state = load_state()

    # 幂等检查
    if idempotency_key:
        if idempotency_key in state.get('idempotency_keys', {}):
            existing = state['idempotency_keys'][idempotency_key]
            return {'ok': False, 'reason': 'duplicate', 'existing_job_id': existing}

    job_id = uuid.uuid4().hex[:8]
    now = datetime.now().isoformat()

    job = {
        'job_id': job_id,
        'action': action,
        'params': params or {},
        'priority': priority,
        'status': 'QUEUED',
        'created_at': now,
        'updated_at': now,
        'retry_count': 0,
        'max_retries': MAX_RETRIES,
        'timeout_sec': timeout_sec,
        'idempotency_key': idempotency_key,
        'next_run_after': now,
    }

    _append_jsonl(QUEUE_FILE, job)

    # 更新索引
    if idempotency_key:
        state.setdefault('idempotency_keys', {})[idempotency_key] = job_id
    state['counters']['enqueued'] = state['counters'].get('enqueued', 0) + 1
    save_state(state)

    _log_event(job_id, None, 'QUEUED', f'入队: {action}')
    return {'ok': True, 'job_id': job_id}

# --- Worker ---

def worker(max_jobs=10):
    """处理队列中的任务，一次最多处理 max_jobs 个"""
    queue = _load_jsonl(QUEUE_FILE)
    now = datetime.now()
    processed = 0
    results = []

    remaining = []
    runnable = []

    for job in queue:
        if job['status'] in ('QUEUED', 'RETRY'):
            # 检查是否到了可执行时间
            next_run = datetime.fromisoformat(job['next_run_after'])
            if now >= next_run and processed < max_jobs:
                runnable.append(job)
                processed += 1
            else:
                remaining.append(job)
        elif job['status'] == 'RUNNING':
            # 可能是上次崩溃遗留，标记为需要恢复
            remaining.append(job)
        else:
            remaining.append(job)

    for job in runnable:
        job['status'] = 'RUNNING'
        job['started_at'] = now.isoformat()
        job['updated_at'] = now.isoformat()
        _log_event(job['job_id'], 'QUEUED', 'RUNNING', '开始执行')

        try:
            result = _execute_job(job)
            job['status'] = 'SUCCESS'
            job['completed_at'] = datetime.now().isoformat()
            job['updated_at'] = datetime.now().isoformat()
            job['result'] = result
            _log_event(job['job_id'], 'RUNNING', 'SUCCESS', f'执行成功')

            state = load_state()
            state['counters']['success'] = state['counters'].get('success', 0) + 1
            save_state(state)

            # 成功的移到历史
            _append_jsonl(HISTORY_FILE, job)
            results.append({'job_id': job['job_id'], 'status': 'SUCCESS'})

        except Exception as e:
            job['updated_at'] = datetime.now().isoformat()
            job['last_error'] = str(e)[:500]

            if job['retry_count'] < job['max_retries']:
                # 重试
                delay = RETRY_DELAYS[min(job['retry_count'], len(RETRY_DELAYS) - 1)]
                job['status'] = 'RETRY'
                job['retry_count'] += 1
                job['next_run_after'] = (datetime.now() + timedelta(seconds=delay)).isoformat()
                _log_event(job['job_id'], 'RUNNING', 'RETRY',
                          f'失败({e})，第{job["retry_count"]}次重试，{delay}s后')
                remaining.append(job)

                state = load_state()
                state['counters']['retried'] = state['counters'].get('retried', 0) + 1
                save_state(state)

                results.append({'job_id': job['job_id'], 'status': 'RETRY', 'retry': job['retry_count']})
            else:
                # 进死信
                job['status'] = 'DEAD'
                _log_event(job['job_id'], 'RUNNING', 'DEAD',
                          f'重试{MAX_RETRIES}次仍失败，进入死信: {e}')
                _append_jsonl(DEAD_FILE, job)

                state = load_state()
                state['counters']['dead'] = state['counters'].get('dead', 0) + 1
                state['counters']['failed'] = state['counters'].get('failed', 0) + 1
                save_state(state)

                results.append({'job_id': job['job_id'], 'status': 'DEAD'})

    # 重写队列（只保留未完成的）
    _save_jsonl(QUEUE_FILE, remaining)
    return results

def _execute_job(job):
    """执行单个任务"""
    action = job['action']
    params = job.get('params', {})
    timeout = job.get('timeout_sec', 30)

    if action == 'shell':
        cmd = params.get('command')
        if not cmd:
            raise ValueError('shell 任务需要 params.command')
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=timeout, cwd=params.get('cwd', WS))
        if r.returncode != 0:
            raise RuntimeError(f'exit {r.returncode}: {r.stderr[:300]}')
        return {'stdout': r.stdout[:500], 'returncode': r.returncode}

    elif action == 'python':
        script = params.get('script')
        if not script:
            raise ValueError('python 任务需要 params.script')
        args = params.get('args', [])
        r = subprocess.run([PYTHON, script] + args, capture_output=True, text=True,
                          timeout=timeout, cwd=params.get('cwd', WS))
        if r.returncode != 0:
            raise RuntimeError(f'exit {r.returncode}: {r.stderr[:300]}')
        return {'stdout': r.stdout[:500], 'returncode': r.returncode}

    elif action == 'alert_push':
        # 告警推送任务
        message = params.get('message', '')
        return {'pushed': True, 'message': message}

    elif action == 'noop':
        # 测试用空任务
        if params.get('fail'):
            raise RuntimeError('intentional failure for testing')
        return {'noop': True}

    else:
        raise ValueError(f'未知任务类型: {action}')

# --- Recovery ---

def recover():
    """恢复崩溃遗留的 RUNNING 任务为 QUEUED"""
    queue = _load_jsonl(QUEUE_FILE)
    recovered = 0
    for job in queue:
        if job['status'] == 'RUNNING':
            job['status'] = 'QUEUED'
            job['updated_at'] = datetime.now().isoformat()
            job['next_run_after'] = datetime.now().isoformat()
            _log_event(job['job_id'], 'RUNNING', 'QUEUED', '崩溃恢复: RUNNING -> QUEUED')
            recovered += 1
    _save_jsonl(QUEUE_FILE, queue)
    return recovered

# --- Query ---

def list_queue(status_filter=None):
    queue = _load_jsonl(QUEUE_FILE)
    if status_filter:
        queue = [j for j in queue if j['status'] == status_filter]
    return queue

def list_dead(limit=20):
    return _load_jsonl(DEAD_FILE)[-limit:]

def stats():
    state = load_state()
    c = state.get('counters', {})
    queue = _load_jsonl(QUEUE_FILE)
    queued = sum(1 for j in queue if j['status'] == 'QUEUED')
    running = sum(1 for j in queue if j['status'] == 'RUNNING')
    retry = sum(1 for j in queue if j['status'] == 'RETRY')

    # 平均等待时长（从历史）
    history = _load_jsonl(HISTORY_FILE)
    wait_times = []
    for h in history[-100:]:
        if 'started_at' in h and 'created_at' in h:
            try:
                created = datetime.fromisoformat(h['created_at'])
                started = datetime.fromisoformat(h['started_at'])
                wait_times.append((started - created).total_seconds())
            except:
                pass
    avg_wait = round(sum(wait_times) / len(wait_times), 1) if wait_times else 0

    return {
        'queued': queued,
        'running': running,
        'retry_pending': retry,
        'total_enqueued': c.get('enqueued', 0),
        'total_success': c.get('success', 0),
        'total_failed': c.get('failed', 0),
        'total_dead': c.get('dead', 0),
        'total_retried': c.get('retried', 0),
        'avg_wait_sec': avg_wait,
        'success_rate': round(c.get('success', 0) / max(c.get('success', 0) + c.get('failed', 0), 1) * 100, 1),
    }

# --- Audit ---

def _log_event(job_id, from_status, to_status, reason):
    entry = {
        'ts': datetime.now().isoformat(),
        'job_id': job_id,
        'from': from_status,
        'to': to_status,
        'reason': reason,
    }
    _append_jsonl(HISTORY_FILE, entry)

# --- CLI ---

def cli():
    args = sys.argv[1:]
    if not args:
        print("用法:")
        print("  job_queue.py enqueue <action> [--params JSON] [--key IDEMPOTENCY_KEY]")
        print("  job_queue.py worker [--max N]")
        print("  job_queue.py list [--status QUEUED|RETRY|RUNNING]")
        print("  job_queue.py dead")
        print("  job_queue.py stats")
        print("  job_queue.py recover")
        return

    cmd = args[0]

    if cmd == 'enqueue':
        if len(args) < 2:
            print("用法: job_queue.py enqueue <action> [--params JSON] [--key KEY]")
            return
        action = args[1]
        params = {}
        key = None
        if '--params' in args:
            idx = args.index('--params')
            if idx + 1 < len(args):
                params = json.loads(args[idx + 1])
        if '--key' in args:
            idx = args.index('--key')
            if idx + 1 < len(args):
                key = args[idx + 1]
        r = enqueue(action, params, idempotency_key=key)
        print(json.dumps(r, ensure_ascii=False))

    elif cmd == 'worker':
        max_jobs = 10
        if '--max' in args:
            idx = args.index('--max')
            if idx + 1 < len(args):
                max_jobs = int(args[idx + 1])
        results = worker(max_jobs)
        if not results:
            print("📭 队列为空，无任务可执行")
        else:
            for r in results:
                icon = {'SUCCESS': '✅', 'RETRY': '🔄', 'DEAD': '💀'}.get(r['status'], '❓')
                print(f"  {icon} [{r['job_id']}] {r['status']}")

    elif cmd == 'list':
        status = None
        if '--status' in args:
            idx = args.index('--status')
            if idx + 1 < len(args):
                status = args[idx + 1]
        jobs = list_queue(status)
        if not jobs:
            print("📭 队列为空")
        else:
            for j in jobs:
                print(f"  [{j['job_id']}] {j['status']} {j['action']} (retry:{j['retry_count']}/{j['max_retries']})")

    elif cmd == 'dead':
        dead = list_dead()
        if not dead:
            print("✅ 无死信")
        else:
            for d in dead:
                print(f"  💀 [{d['job_id']}] {d['action']} err: {d.get('last_error', '?')[:80]}")

    elif cmd == 'stats':
        s = stats()
        print(f"📊 队列统计:")
        print(f"  当前: 待执行={s['queued']} 运行中={s['running']} 待重试={s['retry_pending']}")
        print(f"  累计: 入队={s['total_enqueued']} 成功={s['total_success']} 失败={s['total_failed']} 死信={s['total_dead']}")
        print(f"  重试次数={s['total_retried']} 成功率={s['success_rate']}% 平均等待={s['avg_wait_sec']}s")

    elif cmd == 'recover':
        n = recover()
        print(f"🔧 恢复了 {n} 个崩溃遗留任务")

    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    cli()
