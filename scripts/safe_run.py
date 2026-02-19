"""safe_run.py - 变更保险丝
高风险动作默认 dry-run，需 --confirm 才能真执行
执行前自动快照，失败自动回滚，全程审计落盘

风险分级: LOW / MEDIUM / HIGH / CRIT
执行门禁: HIGH+ 无 --confirm 硬拒绝
CLI: safe-run plan <action> | safe-run apply <action> --confirm | safe-run rollback <change_id> | safe-run log
"""
import json, os, sys, io, shutil, uuid, hashlib, subprocess
from datetime import datetime

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WS = r'C:\Users\A\.openclaw\workspace'
CHANGES_LOG = os.path.join(WS, 'memory', 'changes_log.jsonl')
SNAPSHOTS_DIR = os.path.join(WS, 'memory', 'snapshots')
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# --- 风险目录 ---

RISK_CATALOG = {
    # 文件操作
    'file_delete':   {'risk': 'HIGH',   'desc': '删除文件', 'rollback': True},
    'file_modify':   {'risk': 'MEDIUM', 'desc': '修改文件', 'rollback': True},
    'file_create':   {'risk': 'LOW',    'desc': '创建文件', 'rollback': True},
    'file_bulk':     {'risk': 'HIGH',   'desc': '批量文件操作', 'rollback': True},
    # 系统操作
    'service_restart': {'risk': 'HIGH', 'desc': '重启服务', 'rollback': False},
    'service_stop':    {'risk': 'CRIT', 'desc': '停止服务', 'rollback': False},
    'system_config':   {'risk': 'HIGH', 'desc': '修改系统配置', 'rollback': True},
    # 外部写操作
    'send_message':  {'risk': 'MEDIUM', 'desc': '发送消息', 'rollback': False},
    'send_email':    {'risk': 'HIGH',   'desc': '发送邮件', 'rollback': False},
    'post_public':   {'risk': 'CRIT',   'desc': '公开发布', 'rollback': False},
    'git_push':      {'risk': 'HIGH',   'desc': 'Git 推送', 'rollback': False},
    # 数据操作
    'db_modify':     {'risk': 'HIGH',   'desc': '修改数据库', 'rollback': True},
    'batch_job':     {'risk': 'HIGH',   'desc': '批量任务', 'rollback': False},
    'cron_modify':   {'risk': 'MEDIUM', 'desc': '修改定时任务', 'rollback': False},
}

RISK_ORDER = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRIT': 3}
CONFIRM_THRESHOLD = 'HIGH'  # HIGH 及以上需要 --confirm

# --- 快照 ---

def snapshot_file(filepath):
    """备份单个文件，返回快照路径"""
    if not os.path.exists(filepath):
        return None
    snap_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(filepath)[1]
    snap_name = f"{snap_id}_{os.path.basename(filepath)}"
    snap_path = os.path.join(SNAPSHOTS_DIR, snap_name)
    shutil.copy2(filepath, snap_path)
    return snap_path

def file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# --- 审计 ---

def log_change(entry):
    with open(CHANGES_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def load_changes(limit=50):
    if not os.path.exists(CHANGES_LOG):
        return []
    entries = []
    with open(CHANGES_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except:
                    pass
    return entries[-limit:]

def find_change(change_id):
    for e in load_changes(500):
        if e.get('change_id') == change_id:
            return e
    return None

# --- Plan ---

def plan(action, targets=None, params=None):
    """评估风险，输出执行计划"""
    catalog = RISK_CATALOG.get(action)
    if not catalog:
        return {'ok': False, 'error': f'未知动作类型: {action}', 'known_actions': list(RISK_CATALOG.keys())}

    risk = catalog['risk']
    needs_confirm = RISK_ORDER[risk] >= RISK_ORDER[CONFIRM_THRESHOLD]

    result = {
        'action': action,
        'desc': catalog['desc'],
        'risk': risk,
        'needs_confirm': needs_confirm,
        'rollback_supported': catalog['rollback'],
        'targets': targets or [],
        'params': params or {},
    }

    # 文件类动作：检查目标文件状态
    if targets and action.startswith('file_'):
        file_info = []
        for t in targets:
            info = {'path': t, 'exists': os.path.exists(t)}
            if info['exists']:
                info['size'] = os.path.getsize(t)
                info['hash'] = file_hash(t)
            file_info.append(info)
        result['file_info'] = file_info

    return result

# --- Apply ---

def apply(action, targets=None, params=None, confirm=False, operator='小九'):
    """执行变更，带门禁和快照"""
    p = plan(action, targets, params)
    if not p.get('action'):
        return p

    change_id = uuid.uuid4().hex[:8]
    now = datetime.now().isoformat()

    # 门禁检查
    if p['needs_confirm'] and not confirm:
        entry = {
            'change_id': change_id,
            'ts': now,
            'action': action,
            'risk': p['risk'],
            'status': 'REJECTED',
            'reason': f'{p["risk"]} 级操作需要 --confirm 确认',
            'operator': operator,
            'targets': targets,
        }
        log_change(entry)
        return {'ok': False, 'change_id': change_id, 'status': 'REJECTED',
                'reason': f'🚫 {p["risk"]} 级操作 [{p["desc"]}] 需要 --confirm 确认才能执行'}

    # 快照（文件类）
    snapshots = {}
    if p['rollback_supported'] and targets:
        for t in (targets or []):
            snap = snapshot_file(t)
            if snap:
                snapshots[t] = snap

    # 执行
    entry = {
        'change_id': change_id,
        'ts': now,
        'action': action,
        'risk': p['risk'],
        'operator': operator,
        'targets': targets,
        'params': params,
        'snapshots': snapshots,
        'status': 'PENDING',
    }

    try:
        result = _execute(action, targets, params)
        entry['status'] = 'SUCCESS'
        entry['result'] = result
    except Exception as e:
        entry['status'] = 'FAILED'
        entry['error'] = str(e)
        # 失败自动回滚
        if snapshots:
            rollback_results = _do_rollback(snapshots)
            entry['auto_rollback'] = rollback_results
            entry['status'] = 'ROLLED_BACK'

    log_change(entry)
    return entry

def _execute(action, targets, params):
    """实际执行逻辑（按动作类型分发）"""
    params = params or {}

    if action == 'file_delete':
        results = []
        for t in (targets or []):
            if os.path.exists(t):
                os.remove(t)
                results.append(f'deleted: {t}')
            else:
                results.append(f'not found: {t}')
        return results

    elif action == 'file_modify':
        # params: {content: str} 或 {find: str, replace: str}
        results = []
        for t in (targets or []):
            if 'content' in params:
                with open(t, 'w', encoding='utf-8') as f:
                    f.write(params['content'])
                results.append(f'overwritten: {t}')
            elif 'find' in params and 'replace' in params:
                with open(t, 'r', encoding='utf-8') as f:
                    content = f.read()
                new_content = content.replace(params['find'], params['replace'])
                with open(t, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                results.append(f'replaced in: {t}')
        return results

    elif action == 'file_create':
        results = []
        for t in (targets or []):
            content = params.get('content', '')
            with open(t, 'w', encoding='utf-8') as f:
                f.write(content)
            results.append(f'created: {t}')
        return results

    elif action == 'system_config':
        cmd = params.get('command')
        if not cmd:
            raise ValueError('system_config 需要 params.command')
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError(f'命令失败 (code {r.returncode}): {r.stderr[:200]}')
        return {'stdout': r.stdout[:500], 'returncode': r.returncode}

    elif action == 'db_modify':
        # 通用 JSON 文件修改
        results = []
        for t in (targets or []):
            patch = params.get('patch', {})
            with open(t, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data.update(patch)
            with open(t, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            results.append(f'patched: {t}')
        return results

    else:
        raise ValueError(f'动作 {action} 暂不支持自动执行，请手动操作')

# --- Rollback ---

def rollback(change_id):
    """根据 change_id 回滚"""
    entry = find_change(change_id)
    if not entry:
        return {'ok': False, 'error': f'找不到变更记录: {change_id}'}

    snapshots = entry.get('snapshots', {})
    if not snapshots:
        return {'ok': False, 'error': f'变更 {change_id} 无快照，不支持回滚'}

    results = _do_rollback(snapshots)

    # 记录回滚操作
    rb_entry = {
        'change_id': uuid.uuid4().hex[:8],
        'ts': datetime.now().isoformat(),
        'action': 'rollback',
        'risk': 'MEDIUM',
        'operator': '小九',
        'original_change': change_id,
        'status': 'SUCCESS',
        'result': results,
    }
    log_change(rb_entry)
    return {'ok': True, 'results': results, 'rollback_id': rb_entry['change_id']}

def _do_rollback(snapshots):
    results = []
    for original_path, snap_path in snapshots.items():
        if os.path.exists(snap_path):
            shutil.copy2(snap_path, original_path)
            results.append(f'restored: {original_path}')
        else:
            results.append(f'snapshot missing: {snap_path}')
    return results

# --- Stats (for weekly report) ---

def weekly_stats(days=7):
    cutoff = datetime.now().isoformat()[:10]  # simplified
    entries = load_changes(500)
    stats = {
        'total': 0, 'high_risk': 0, 'rejected': 0,
        'success': 0, 'failed': 0, 'rolled_back': 0,
    }
    for e in entries:
        stats['total'] += 1
        if e.get('risk') in ('HIGH', 'CRIT'):
            stats['high_risk'] += 1
        s = e.get('status', '')
        if s == 'REJECTED':
            stats['rejected'] += 1
        elif s == 'SUCCESS':
            stats['success'] += 1
        elif s == 'FAILED':
            stats['failed'] += 1
        elif s == 'ROLLED_BACK':
            stats['rolled_back'] += 1
    return stats

# --- CLI ---

def cli():
    args = sys.argv[1:]
    if not args:
        print("用法:")
        print("  safe-run plan <action> [--targets t1,t2]")
        print("  safe-run apply <action> [--targets t1,t2] [--confirm]")
        print("  safe-run rollback <change_id>")
        print("  safe-run log [--limit N]")
        print("  safe-run stats")
        print("  safe-run actions")
        return

    cmd = args[0]

    if cmd == 'actions':
        print("可用动作:")
        for name, info in sorted(RISK_CATALOG.items()):
            rb = "✅" if info['rollback'] else "❌"
            print(f"  {name:20s} {info['risk']:6s} {info['desc']}  回滚:{rb}")
        return

    if cmd == 'plan':
        if len(args) < 2:
            print("用法: safe-run plan <action> [--targets t1,t2]")
            return
        action = args[1]
        targets = _parse_targets(args)
        p = plan(action, targets)
        print(json.dumps(p, ensure_ascii=False, indent=2))

    elif cmd == 'apply':
        if len(args) < 2:
            print("用法: safe-run apply <action> [--targets t1,t2] [--confirm]")
            return
        action = args[1]
        targets = _parse_targets(args)
        confirm = '--confirm' in args
        result = apply(action, targets, confirm=confirm)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == 'rollback':
        if len(args) < 2:
            print("用法: safe-run rollback <change_id>")
            return
        result = rollback(args[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == 'log':
        limit = 10
        if '--limit' in args:
            idx = args.index('--limit')
            if idx + 1 < len(args):
                limit = int(args[idx + 1])
        entries = load_changes(limit)
        for e in entries:
            risk_icon = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🟠', 'CRIT': '🔴'}.get(e.get('risk', ''), '⚪')
            status = e.get('status', '?')
            print(f"[{e.get('change_id', '?')}] {risk_icon} {e.get('risk', '?')} {e.get('action', '?')} → {status} ({e.get('ts', '?')[:16]})")

    elif cmd == 'stats':
        s = weekly_stats()
        print(f"📊 变更统计: 总计={s['total']} 高风险={s['high_risk']} 成功={s['success']} 拒绝={s['rejected']} 失败={s['failed']} 回滚={s['rolled_back']}")

    else:
        print(f"未知命令: {cmd}")

def _parse_targets(args):
    if '--targets' in args:
        idx = args.index('--targets')
        if idx + 1 < len(args):
            return args[idx + 1].split(',')
    return []

if __name__ == '__main__':
    cli()
