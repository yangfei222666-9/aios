"""weekly_health.py - 周报自动汇总
从 reports/refresh_*.md + AIOS score + autolearn health 聚合趋势
输出 reports/weekly_health_YYYYmmdd.md
"""
import os, re, json, subprocess, sys
from datetime import datetime, timedelta

WS = r'C:\Users\A\.openclaw\workspace'
REPORTS = os.path.join(WS, 'reports')
PYTHON = r'C:\Program Files\Python312\python.exe'
GIT = r'C:\Program Files\Git\cmd\git.exe'

now = datetime.now()
week_ago = now - timedelta(days=7)

# 1. 聚合 refresh 报告
refresh_files = sorted([f for f in os.listdir(REPORTS) if f.startswith('refresh_') and f.endswith('.md')])
weekly_refreshes = []
for f in refresh_files:
    # refresh_20260219.md -> 2026-02-19
    m = re.match(r'refresh_(\d{4})(\d{2})(\d{2})\.md', f)
    if not m:
        continue
    dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if dt >= week_ago:
        path = os.path.join(REPORTS, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        entry = {'date': dt.strftime('%Y-%m-%d'), 'file': f}
        for line in content.splitlines():
            if line.startswith('- DDragon'):
                entry['version'] = line.split(':')[-1].strip()
            elif line.startswith('- 成功:'):
                entry['success'] = int(line.split(':')[-1].strip())
            elif line.startswith('- 失败:'):
                entry['fail'] = int(line.split(':')[-1].strip())
            elif line.startswith('- 变更:'):
                entry['changed'] = int(line.split(':')[-1].strip())
            elif line.startswith('- 新增:'):
                entry['new'] = int(line.split(':')[-1].strip())
            elif line.startswith('- 重试次数:'):
                entry['retries'] = int(line.split(':')[-1].strip())
        weekly_refreshes.append(entry)

# 2. AIOS score
try:
    r = subprocess.run([PYTHON, '-m', 'aios', 'score'], cwd=WS, capture_output=True, text=True, timeout=15)
    aios = json.loads(r.stdout)
except:
    aios = {'score': 'N/A', 'grade': 'N/A'}

# 3. Autolearn health
try:
    r = subprocess.run([PYTHON, '-m', 'autolearn', 'health'], cwd=WS, capture_output=True, text=True, timeout=15)
    al_out = r.stdout.strip()
    al_healthy = 'healthy' in al_out.lower()
    # 提取 pass/fail
    m = re.search(r'(\d+) PASS / (\d+) FAIL', al_out)
    al_pass = int(m.group(1)) if m else 0
    al_fail = int(m.group(2)) if m else 0
except:
    al_healthy = False
    al_pass = al_fail = 0

# 4. Git 活动
try:
    since = week_ago.strftime('%Y-%m-%d')
    r = subprocess.run([GIT, 'log', f'--since={since}', '--oneline'], cwd=WS, capture_output=True, text=True, timeout=10)
    commits = [l for l in r.stdout.strip().splitlines() if l]
except:
    commits = []

# 5. 备份检查
backup_dir = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'autolearn_backups')
backups = []
if os.path.isdir(backup_dir):
    for f in sorted(os.listdir(backup_dir)):
        if f.startswith('autolearn_backup_') and f.endswith('.zip'):
            size_mb = round(os.path.getsize(os.path.join(backup_dir, f)) / 1024 / 1024, 2)
            backups.append(f'{f} ({size_mb} MB)')

# 6. 生成周报
ts = now.strftime('%Y%m%d')
out_path = os.path.join(REPORTS, f'weekly_health_{ts}.md')

lines = [
    f'# 周报 {now.strftime("%Y-%m-%d %H:%M")}',
    f'> 统计周期: {week_ago.strftime("%Y-%m-%d")} ~ {now.strftime("%Y-%m-%d")}',
    '',
    '## 系统健康',
    f'- AIOS score: {aios.get("score", "N/A")} (grade: {aios.get("grade", "N/A")})',
    f'- Autolearn: {"✅ healthy" if al_healthy else "⚠️ unhealthy"} ({al_pass} pass / {al_fail} fail)',
    '',
    '## LOL 数据刷新',
]

if weekly_refreshes:
    total_success = sum(r.get('success', 0) for r in weekly_refreshes)
    total_fail = sum(r.get('fail', 0) for r in weekly_refreshes)
    total_changed = sum(r.get('changed', 0) for r in weekly_refreshes)
    total_new = sum(r.get('new', 0) for r in weekly_refreshes)
    total_retries = sum(r.get('retries', 0) for r in weekly_refreshes)
    latest_ver = weekly_refreshes[-1].get('version', 'N/A')

    lines.append(f'- 刷新次数: {len(weekly_refreshes)}')
    lines.append(f'- 当前版本: {latest_ver}')
    lines.append(f'- 总成功/失败: {total_success}/{total_fail}')
    lines.append(f'- 总变更/新增: {total_changed}/{total_new}')
    lines.append(f'- 总重试: {total_retries}')
    lines.append(f'- 成功率: {round(total_success/(total_success+total_fail)*100, 1) if (total_success+total_fail) > 0 else 0}%')
    lines.append('')

    if total_fail > 0:
        lines.append('⚠️ 本周有失败记录，建议排查')
    else:
        lines.append('✅ 本周零失败')
else:
    lines.append('- 本周无刷新记录')

lines.extend(['', '## 版本控制', f'- 本周提交: {len(commits)}'])
for c in commits[-10:]:
    lines.append(f'  - {c}')

lines.extend(['', '## 备份', f'- 备份文件数: {len(backups)}'])
for b in backups[-7:]:
    lines.append(f'  - {b}')

# 趋势判断
lines.extend(['', '## 趋势判断'])
issues = []
if aios.get('grade') in ('degraded', 'critical'):
    issues.append('AIOS 评分异常')
if not al_healthy:
    issues.append('Autolearn 测试有失败')
if weekly_refreshes and total_fail > 0:
    issues.append(f'LOL 刷新有 {total_fail} 次失败')

# 集成 alerts 系统的 WARN 事件
try:
    sys.path.insert(0, os.path.join(WS, 'scripts'))
    from alerts import get_recent_warns
    weekly_warns = get_recent_warns(days=7)
    if weekly_warns:
        lines.extend(['', '## 本周告警 (WARN)'])
        for w in weekly_warns:
            lines.append(f'- [{w["rule"]}] {w["message"]} (x{w["count"]})')
        for w in weekly_warns:
            issues.append(f'告警: {w["message"]}')
except:
    pass

# 集成闭环状态机统计
try:
    import alert_fsm
    fsm_stats = alert_fsm.stats()
    lines.extend(['', '## 告警闭环状态'])
    lines.append(f'- 当前 OPEN: {fsm_stats["open"]}')
    lines.append(f'- 当前 ACK (处理中): {fsm_stats["ack"]}')
    lines.append(f'- 今日已解决: {fsm_stats["resolved_today"]}')
    lines.append(f'- 超 SLA: {fsm_stats["overdue"]}')
    if fsm_stats['overdue'] > 0:
        issues.append(f'{fsm_stats["overdue"]} 个告警超 SLA')
except:
    pass

# 集成变更保险丝统计
try:
    import safe_run
    sr_stats = safe_run.weekly_stats()
    lines.extend(['', '## 高风险变更'])
    lines.append(f'- 本周变更总计: {sr_stats["total"]}')
    lines.append(f'- 高风险变更: {sr_stats["high_risk"]}')
    lines.append(f'- 成功: {sr_stats["success"]} | 拒绝: {sr_stats["rejected"]} | 失败: {sr_stats["failed"]} | 回滚: {sr_stats["rolled_back"]}')
    if sr_stats['failed'] > 0:
        issues.append(f'{sr_stats["failed"]} 次变更执行失败')
    if sr_stats['rolled_back'] > 0:
        issues.append(f'{sr_stats["rolled_back"]} 次变更被回滚')
except:
    pass

# 集成任务队列统计
try:
    import job_queue
    jq_stats = job_queue.stats()
    lines.extend(['', '## 任务队列'])
    lines.append(f'- 吞吐: 入队={jq_stats["total_enqueued"]} 成功={jq_stats["total_success"]}')
    lines.append(f'- 成功率: {jq_stats["success_rate"]}%')
    lines.append(f'- 平均等待: {jq_stats["avg_wait_sec"]}s')
    lines.append(f'- 死信: {jq_stats["total_dead"]} | 重试: {jq_stats["total_retried"]}')
    lines.append(f'- 当前队列: 待执行={jq_stats["queued"]} 运行中={jq_stats["running"]} 待重试={jq_stats["retry_pending"]}')
    if jq_stats['total_dead'] > 0:
        issues.append(f'{jq_stats["total_dead"]} 个任务进入死信')
except:
    pass

# 集成运营看板治理评分
try:
    import ops_dashboard
    aq = ops_dashboard.alert_quality(7)
    cs = ops_dashboard.change_safety(7)
    qh = ops_dashboard.queue_health(7)
    gs = ops_dashboard.governance_score(aq, cs, qh)
    lines.extend(['', '## 治理评分'])
    lines.append(f'- 告警质量: {gs["alert_quality_score"]}/100')
    lines.append(f'- 变更安全: {gs["change_safety_score"]}/100')
    lines.append(f'- 队列健康: {gs["queue_health_score"]}/100')
    icon = '🟢' if gs['stable'] else '🟡'
    lines.append(f'- 综合评分: {gs["governance_score"]}/100 {icon}')
    ops_dashboard.record_score(gs)
    if gs['governance_score'] < 70:
        issues.append(f'治理评分偏低: {gs["governance_score"]}/100')
except:
    pass

if not issues:
    lines.append('🟢 系统稳定运行，无异常趋势')
else:
    lines.append('🟡 需要关注:')
    for i in issues:
        lines.append(f'- {i}')

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

# Git 提交
try:
    subprocess.run([GIT, 'add', out_path], cwd=WS, capture_output=True)
    subprocess.run([GIT, 'commit', '-m', f'report: weekly health {now.strftime("%Y-%m-%d")}'], cwd=WS, capture_output=True)
except:
    pass

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
print(f'weekly report: {out_path}')
for l in lines:
    print(l)
