#!/usr/bin/env python3
"""
LowSuccess_Agent v3.0 - Phase 3: 经验库应用闭环
集成到Heartbeat，每小时自动触发Bootstrapped Regeneration + Phase 3观察

核心流程：
1. 从lessons.json读取失败任务
2. 生成feedback（问题分析 + 改进建议）
3. regenerate新策略（可执行action列表）
4. 通过sessions_spawn真实执行
5. 成功 → 保存到experience_library.jsonl + LanceDB
6. 失败 → 需要人工介入
7. Phase 3观察：记录重生统计 + 生成图表报告
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import time

# 路径配置
WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")
AIOS_DIR = WORKSPACE / "aios" / "agent_system"
LESSONS_FILE = AIOS_DIR / "lessons.json"
EXPERIENCE_LIB = AIOS_DIR / "experience_library.jsonl"
FEEDBACK_LOG = AIOS_DIR / "feedback_log.jsonl"
TASKS_FILE = AIOS_DIR / "tasks.jsonl"

# 添加路径以导入sessions_spawn
sys.path.insert(0, str(WORKSPACE))

# Phase 3 v3.0集成：LanceDB经验学习
# Phase 4.0 升级：灰度 + 幂等 + 版本归因
from experience_learner_v4 import learner_v4

# Phase 3观察器集成（统一使用 aios/agent_system 下的版本）
from phase3_observer import observe_phase3, generate_phase3_report

def load_lessons():
    """加载失败教训"""
    if not LESSONS_FILE.exists():
        return []
    with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('lessons', [])

def get_task_by_id(task_id: str):
    """从tasks.jsonl读取任务详情"""
    if not TASKS_FILE.exists():
        return None
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            task = json.loads(line)
            if task.get('id') == task_id:
                return task
    return None

def generate_feedback(lesson):
    """
    从失败轨迹生成feedback（sirius核心机制）
    
    Args:
        lesson: 失败教训记录
    
    Returns:
        feedback字典（包含问题分析和改进建议）
    """
    error_type = lesson.get('error_type', 'unknown')
    context = lesson.get('context', '')
    
    # 根据错误类型生成针对性feedback
    feedback_templates = {
        'timeout': {
            'problem': '任务超时，可能是任务复杂度过高或资源不足',
            'suggestions': [
                '拆分任务为更小的子任务',
                '增加超时时间（60s → 120s）',
                '优化算法复杂度'
            ]
        },
        'dependency_error': {
            'problem': '依赖缺失或版本冲突',
            'suggestions': [
                '在任务开始前检查依赖',
                '使用虚拟环境隔离依赖',
                '明确指定依赖版本'
            ]
        },
        'logic_error': {
            'problem': '代码逻辑错误（如除零、空指针）',
            'suggestions': [
                '增加输入验证',
                '添加异常处理',
                '使用防御性编程'
            ]
        },
        'resource_exhausted': {
            'problem': '资源耗尽（内存/磁盘/网络）',
            'suggestions': [
                '优化资源使用',
                '增加资源限制检查',
                '使用流式处理'
            ]
        }
    }
    
    template = feedback_templates.get(error_type, {
        'problem': '未知错误类型',
        'suggestions': ['增加日志记录', '添加错误处理', '人工审查']
    })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'lesson_id': lesson.get('id', 'unknown'),
        'error_type': error_type,
        'problem': template['problem'],
        'suggestions': template['suggestions'],
        'context': context
    }

def regenerate_strategy(feedback):
    """
    基于feedback重新生成策略（sirius核心机制）
    
    Args:
        feedback: feedback字典
    
    Returns:
        新策略字典
    """
    suggestions = feedback['suggestions']
    
    # 将建议转化为可执行策略
    strategy = {
        'timestamp': datetime.now().isoformat(),
        'feedback_id': feedback.get('lesson_id', 'unknown'),
        'actions': []
    }
    
    for suggestion in suggestions:
        if '拆分任务' in suggestion:
            strategy['actions'].append({
                'type': 'task_decomposition',
                'description': '将任务拆分为更小的子任务',
                'priority': 'high'
            })
        elif '增加超时' in suggestion:
            strategy['actions'].append({
                'type': 'timeout_adjustment',
                'description': '增加超时时间到120秒',
                'priority': 'medium'
            })
        elif '检查依赖' in suggestion:
            strategy['actions'].append({
                'type': 'dependency_check',
                'description': '在任务开始前验证所有依赖',
                'priority': 'high'
            })
        elif '异常处理' in suggestion:
            strategy['actions'].append({
                'type': 'error_handling',
                'description': '添加try-catch和输入验证',
                'priority': 'high'
            })
        elif '资源限制' in suggestion:
            strategy['actions'].append({
                'type': 'resource_limit',
                'description': '添加资源使用监控和限制',
                'priority': 'medium'
            })
    
    return strategy

def regenerate_failed_task_real(lesson):
    """
    真实重生执行（Phase 2核心 + Phase 4.0 v4集成）
    
    Args:
        lesson: 失败教训记录
    
    Returns:
        (success: bool, result: dict, recommendation: dict)
    """
    task_id = lesson.get('id', 'unknown')
    error_type = lesson.get('error_type', 'unknown')
    print(f"[REGEN] 正在为任务 {task_id} 执行Bootstrapped Regeneration...")
    
    # Phase 4.0集成：从经验库推荐（含灰度 + 回滚开关）
    recommendation = learner_v4.recommend({
        'error_type': error_type,
        'task_id': task_id,
        'prompt': lesson.get('description', ''),
    })
    rec_strategy = recommendation['recommended_strategy']
    rec_source = recommendation['source']
    rec_version = recommendation['strategy_version']
    print(f"  [REC] Strategy: {rec_strategy} | Source: {rec_source} | Version: {rec_version}")
    
    # 1. 生成feedback
    feedback = generate_feedback(lesson)
    print(f"  [OK] 生成feedback: {feedback['problem']}")
    
    # 2. regenerate新策略
    strategy = regenerate_strategy(feedback)
    print(f"  [OK] 生成策略: {len(strategy['actions'])} 个action")
    
    # 3. 构建增强的任务描述（包含feedback、strategy和经验推荐）
    rec_block = ""
    if rec_source == "experience":
        rec_block = f"""
[历史经验推荐 (v={rec_version}, confidence={recommendation['confidence']:.2f})]
推荐策略: {rec_strategy}
"""
    
    enhanced_task = f"""
任务重生（Bootstrapped Regeneration v4.0）

原始任务ID: {task_id}
错误类型: {feedback['error_type']}
策略版本: {rec_version}
{rec_block}
问题分析:
{feedback['problem']}

改进建议:
{chr(10).join(f"- {s}" for s in feedback['suggestions'])}

执行策略:
{chr(10).join(f"- [{a['priority']}] {a['description']}" for a in strategy['actions'])}

请根据以上分析和策略，重新执行任务。
"""
    
    # 4. 生成spawn请求
    spawn_request = {
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'agent_id': 'LowSuccess_Agent',
        'task': enhanced_task,
        'label': f'aios-regen-{task_id}',
        'cleanup': 'keep',
        'runTimeoutSeconds': 120,
        'regeneration': True,
        'feedback': feedback,
        'strategy': strategy,
        'recommendation': {
            'strategy': rec_strategy,
            'source': rec_source,
            'version': rec_version,
            'confidence': recommendation.get('confidence', 0.0),
            'grayscale': recommendation.get('grayscale', False),
        },
    }
    
    spawn_file = AIOS_DIR / "spawn_requests.jsonl"
    with open(spawn_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(spawn_request, ensure_ascii=False) + '\n')
    
    print(f"  [OK] Spawn请求已生成: {spawn_file}")
    
    return True, {
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'status': 'pending',
        'spawn_request': spawn_request,
    }, recommendation

def save_to_experience_library(feedback, strategy, result):
    """
    保存成功轨迹到experience_library（sirius核心机制）
    
    Args:
        feedback: feedback字典
        strategy: 策略字典
        result: 执行结果
    """
    experience = {
        'timestamp': datetime.now().isoformat(),
        'lesson_id': feedback.get('lesson_id', 'unknown'),
        'error_type': feedback['error_type'],
        'feedback': feedback,
        'strategy': strategy,
        'result': result,
        'success': result.get('success', False)
    }
    
    # 追加到experience_library.jsonl
    with open(EXPERIENCE_LIB, 'a', encoding='utf-8') as f:
        f.write(json.dumps(experience, ensure_ascii=False) + '\n')

def save_feedback(feedback):
    """保存feedback到日志"""
    with open(FEEDBACK_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(feedback, ensure_ascii=False) + '\n')

def get_already_spawned_ids():
    """获取已经生成过 spawn 请求的 lesson ID，避免重复生成"""
    spawn_file = AIOS_DIR / "spawn_requests.jsonl"
    spawned = set()
    if spawn_file.exists():
        with open(spawn_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                    tid = req.get('task_id')
                    if tid:
                        spawned.add(tid)
                except:
                    continue
    return spawned


def run_low_success_regeneration(limit=5):
    """
    运行LowSuccess_Agent重生流程（Heartbeat调用）+ Phase 3观察
    
    Args:
        limit: 每次最多处理的任务数
    
    Returns:
        处理统计
    """
    # 加载失败教训
    lessons = load_lessons()
    if not lessons:
        return {'processed': 0, 'success': 0, 'failed': 0, 'pending': 0}
    
    # 去重：跳过已经生成过 spawn 请求的 lesson
    already_spawned = get_already_spawned_ids()
    lessons = [l for l in lessons if l.get('id') not in already_spawned]
    
    if not lessons:
        print(f"  [OK] All {len(already_spawned)} lessons already have spawn requests, skipping")
        return {'processed': 0, 'success': 0, 'failed': 0, 'pending': 0}
    
    # 限制处理数量
    lessons_to_process = lessons[:limit]
    
    stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'pending': 0
    }
    
    # 对每个失败教训执行bootstrapped regeneration
    for lesson in lessons_to_process:
        start_time = time.time()
        success, result, recommendation = regenerate_failed_task_real(lesson)
        recovery_time = time.time() - start_time
        
        stats['processed'] += 1
        
        # Phase 3观察：记录每次重生
        task_id = lesson.get('id', 'unknown')
        task_description = lesson.get('description', '')
        observe_phase3(task_id, task_description, success, recovery_time)
        
        if success:
            if result.get('status') == 'pending':
                stats['pending'] += 1
            else:
                stats['success'] += 1
                
                # Phase 4.0集成：保存成功轨迹（幂等 + 版本）
                learner_v4.save_success({
                    'task_id': task_id,
                    'error_type': lesson.get('error_type', 'unknown'),
                    'strategy': recommendation.get('recommended_strategy', 'default_recovery'),
                    'confidence': 0.85,
                    'recovery_time': recovery_time,
                    'strategy_version': recommendation.get('strategy_version', 'v4.0.0'),
                })
                
                # 追踪推荐后结果（分桶）
                learner_v4.track_outcome(
                    task_id=task_id,
                    strategy=recommendation.get('recommended_strategy', 'default_recovery'),
                    source=recommendation.get('source', 'default'),
                    success=True,
                )
        else:
            stats['failed'] += 1
            
            # 追踪推荐后失败（分桶）
            learner_v4.track_outcome(
                task_id=task_id,
                strategy=recommendation.get('recommended_strategy', 'default_recovery'),
                source=recommendation.get('source', 'default'),
                success=False,
            )
    
    # Phase 3观察：生成报告
    if stats['processed'] > 0:
        generate_phase3_report()
    
    print(f"\n[PHASE3] LowSuccess_Agent v3.0 completed (LanceDB recommendations applied)")
    return stats

def main():
    """主函数（用于测试）"""
    print("LowSuccess_Agent v3.0 - Phase 2: 真实Agent执行")
    print("=" * 60)
    
    stats = run_low_success_regeneration(limit=5)
    
    print("\n" + "=" * 60)
    print("[STATS] LowSuccess Regeneration")
    print(f"  Processed: {stats['processed']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Success: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
    
    if stats['processed'] > 0:
        print(f"\n[OK] LowSuccess_Agent regenerated: {stats['processed']} tasks")
    else:
        print(f"\n[OK] No failed tasks to regenerate")

if __name__ == '__main__':
    main()
