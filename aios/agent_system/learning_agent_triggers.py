#!/usr/bin/env python3
"""
Learning Agent 触发器
自动为 Learning Agents 生成任务
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from paths import TASK_QUEUE, TASK_EXECUTIONS

QUEUE_FILE = str(TASK_QUEUE)
STATE_FILE = os.path.join(BASE_DIR, 'learning_trigger_state.json')
EXEC_FILE = str(TASK_EXECUTIONS)

def load_state():
    """加载触发状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_github_research': None,
        'last_bug_hunt': None,
        'last_failure_count': 0
    }

def save_state(state):
    """保存触发状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def add_task(agent_id, description, priority='normal'):
    """添加任务到队列"""
    task = {
        'task_id': f'learning-{agent_id}-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'agent_id': agent_id,
        'type': 'learning',
        'description': description,
        'priority': priority,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'retry_count': 0
    }
    
    with open(QUEUE_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(task, ensure_ascii=False) + '\n')
    
    return task['task_id']

def count_recent_failures():
    """统计最近的失败数量（24h内）"""
    if not os.path.exists(EXEC_FILE):
        return 0
    
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    
    count = 0
    with open(EXEC_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                r = json.loads(line)
                if r.get('timestamp', '') >= cutoff and r.get('status') == 'failed':
                    count += 1
            except:
                pass
    return count

def trigger_github_researcher():
    """触发 GitHub 研究员（每天一次）"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if state['last_github_research'] == today:
        return None  # 今天已经触发过
    
    task_id = add_task(
        'GitHub_Researcher',
        '搜索 GitHub 最新 AIOS/Agent/Self-Improving 相关项目，分析架构设计，提出改进建议',
        priority='normal'
    )
    
    state['last_github_research'] = today
    save_state(state)
    
    return task_id

def trigger_bug_hunter():
    """触发 Bug 猎人（有新失败时）"""
    state = load_state()
    current_failures = count_recent_failures()
    
    # 如果失败数量增加了 3+ 个，触发 Bug_Hunter
    if current_failures >= state['last_failure_count'] + 3:
        task_id = add_task(
            'Bug_Hunter',
            f'分析最近 {current_failures} 个失败任务，识别共性问题和根因',
            priority='high'
        )
        
        state['last_bug_hunt'] = datetime.now().isoformat()
        state['last_failure_count'] = current_failures
        save_state(state)
        
        return task_id
    
    # 更新失败计数
    state['last_failure_count'] = current_failures
    save_state(state)
    
    return None

def trigger_error_analyzer():
    """触发错误分析师（有 unknown 错误时）"""
    # 检查 lessons.json 里有没有 error_type=unknown 的
    lessons_file = os.path.join(BASE_DIR, 'lessons.json')
    if not os.path.exists(lessons_file):
        return None
    
    with open(lessons_file, 'r', encoding='utf-8') as f:
        lessons = json.load(f)
    
    unknown_count = sum(1 for l in lessons if l.get('error_type') == 'unknown')
    
    if unknown_count >= 3:
        task_id = add_task(
            'Error_Analyzer',
            f'分析 {unknown_count} 个 unknown 错误类型，自动分类并更新 lessons.json',
            priority='high'
        )
        return task_id
    
    return None

def trigger_code_reviewer():
    """触发代码审查员（每周一次）"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    last_review = state.get('last_code_review', '')
    
    # 每周一触发
    if datetime.now().weekday() == 0 and last_review != today:
        task_id = add_task(
            'Code_Reviewer',
            '审查 AIOS 核心代码质量，识别技术债务和改进机会',
            priority='normal'
        )
        state['last_code_review'] = today
        save_state(state)
        return task_id
    return None

def trigger_architecture_analyst():
    """触发架构分析师（每周一次）"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    last_analysis = state.get('last_architecture_analysis', '')
    
    # 每周日触发
    if datetime.now().weekday() == 6 and last_analysis != today:
        task_id = add_task(
            'Architecture_Analyst',
            '分析 AIOS 架构设计，对比业界最佳实践，提出优化建议',
            priority='normal'
        )
        state['last_architecture_analysis'] = today
        save_state(state)
        return task_id
    return None

def trigger_documentation_writer():
    """触发文档撰写员（每周两次）"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    last_doc = state.get('last_documentation', '')
    
    # 每周三、周六触发
    if datetime.now().weekday() in (2, 5) and last_doc != today:
        task_id = add_task(
            'Documentation_Writer',
            '更新 AIOS 文档，补充新功能说明和使用示例',
            priority='normal'
        )
        state['last_documentation'] = today
        save_state(state)
        return task_id
    return None

def trigger_github_issue_tracker():
    """触发 GitHub Issue 追踪员（每天一次）"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if state.get('last_issue_track') == today:
        return None
    
    task_id = add_task(
        'GitHub_Issue_Tracker',
        '追踪 AIOS 相关项目的 GitHub Issues，识别常见问题和解决方案',
        priority='normal'
    )
    state['last_issue_track'] = today
    save_state(state)
    return task_id

def trigger_competitor_tracker():
    """触发竞争对手追踪员（每周一次）"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    last_track = state.get('last_competitor_track', '')
    
    # 每周二触发
    if datetime.now().weekday() == 1 and last_track != today:
        task_id = add_task(
            'Competitor_Tracker',
            '追踪竞争对手动态（agiresearch/AIOS 等），分析差异化优势',
            priority='normal'
        )
        state['last_competitor_track'] = today
        save_state(state)
        return task_id
    return None

def trigger_quick_win_hunter():
    """触发快速胜利猎人（每周一次）"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    last_hunt = state.get('last_quick_win', '')
    
    # 每周五触发
    if datetime.now().weekday() == 4 and last_hunt != today:
        task_id = add_task(
            'Quick_Win_Hunter',
            '识别可以快速实现的高价值功能（1-2天完成）',
            priority='high'
        )
        state['last_quick_win'] = today
        save_state(state)
        return task_id
    return None

def run_triggers():
    """运行所有触发器"""
    print('[LEARNING_TRIGGERS] Checking triggers...')
    
    tasks = []
    
    # GitHub Researcher - 每天一次
    task_id = trigger_github_researcher()
    if task_id:
        print(f'  ✓ GitHub_Researcher triggered: {task_id}')
        tasks.append(task_id)
    
    # Bug Hunter - 失败数增加时
    task_id = trigger_bug_hunter()
    if task_id:
        print(f'  ✓ Bug_Hunter triggered: {task_id}')
        tasks.append(task_id)
    
    # Error Analyzer - 有 unknown 错误时
    task_id = trigger_error_analyzer()
    if task_id:
        print(f'  ✓ Error_Analyzer triggered: {task_id}')
        tasks.append(task_id)
    
    # Code Reviewer - 每周一
    task_id = trigger_code_reviewer()
    if task_id:
        print(f'  ✓ Code_Reviewer triggered: {task_id}')
        tasks.append(task_id)
    
    # Architecture Analyst - 每周日
    task_id = trigger_architecture_analyst()
    if task_id:
        print(f'  ✓ Architecture_Analyst triggered: {task_id}')
        tasks.append(task_id)
    
    # Documentation Writer - 每周三、六
    task_id = trigger_documentation_writer()
    if task_id:
        print(f'  ✓ Documentation_Writer triggered: {task_id}')
        tasks.append(task_id)
    
    # GitHub Issue Tracker - 每天一次
    task_id = trigger_github_issue_tracker()
    if task_id:
        print(f'  ✓ GitHub_Issue_Tracker triggered: {task_id}')
        tasks.append(task_id)
    
    # Competitor Tracker - 每周二
    task_id = trigger_competitor_tracker()
    if task_id:
        print(f'  ✓ Competitor_Tracker triggered: {task_id}')
        tasks.append(task_id)
    
    # Quick Win Hunter - 每周五
    task_id = trigger_quick_win_hunter()
    if task_id:
        print(f'  ✓ Quick_Win_Hunter triggered: {task_id}')
        tasks.append(task_id)
    
    if not tasks:
        print('  [no triggers fired]')
    
    return tasks

if __name__ == '__main__':
    run_triggers()
