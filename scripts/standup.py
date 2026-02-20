"""standup.py - 每日站会摘要生成器
读取 projects.json 和昨天的日志，生成站会报告
"""
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

WS = Path(r'C:\Users\A\.openclaw\workspace')
PROJECTS_FILE = WS / 'projects.json'
MEMORY_DIR = WS / 'memory'

def load_projects():
    if not PROJECTS_FILE.exists():
        return []
    with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('projects', [])

def get_yesterday_log():
    """读取昨天的日志"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    log_file = MEMORY_DIR / f'{yesterday}.md'
    
    if not log_file.exists():
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        return f.read()

def generate_standup():
    projects = load_projects()
    yesterday_log = get_yesterday_log()
    
    lines = [
        f"# 每日站会 - {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## 昨天完成",
    ]
    
    if yesterday_log:
        # 简单提取昨天的主要工作（从日志标题提取）
        completed = []
        for line in yesterday_log.split('\n'):
            if line.startswith('## ') and '##' in line:
                completed.append(line.replace('##', '').strip())
        
        if completed:
            for item in completed[:5]:  # 最多 5 条
                lines.append(f"- {item}")
        else:
            lines.append("- 无重大更新")
    else:
        lines.append("- 昨日日志缺失")
    
    lines.extend([
        "",
        "## 今天计划",
    ])
    
    # 从项目中提取今天的计划
    active_projects = [p for p in projects if p['status'] in ('active', 'observing')]
    if active_projects:
        for p in active_projects[:3]:  # 最多 3 个
            lines.append(f"- [{p['name']}] {p['next_action']}")
    else:
        lines.append("- 无活跃项目")
    
    lines.extend([
        "",
        "## 阻塞项",
    ])
    
    blocked = [p for p in projects if p['status'] == 'blocked']
    if blocked:
        for p in blocked:
            lines.append(f"- [{p['name']}] {p['blocker']}")
    else:
        lines.append("- 无阻塞")
    
    lines.extend([
        "",
        "## 项目状态总览",
        "",
        "| 项目 | 状态 | 下一步 |",
        "| :--- | :--- | :--- |",
    ])
    
    for p in projects:
        status_emoji = {
            'active': '[A]',
            'blocked': '[B]',
            'observing': '[O]',
            'done': '[D]',
            'paused': '[P]'
        }.get(p['status'], '[?]')
        
        lines.append(f"| {p['name']} | {status_emoji} {p['status']} | {p['next_action'][:50]}... |")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    report = generate_standup()
    print(report)
    
    # 保存到文件
    today = datetime.now().strftime('%Y-%m-%d')
    output_file = WS / 'logs' / f'standup-{today}.md'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nOK 站会报告已保存到: {output_file}")
