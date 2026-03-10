#!/usr/bin/env python3
"""
LowSuccess_Agent v3.0 - Phase 3: 缁忛獙搴撳簲鐢ㄩ棴鐜?闆嗘垚鍒癏eartbeat锛屾瘡灏忔椂鑷姩瑙﹀彂Bootstrapped Regeneration + Phase 3瑙傚療

鏍稿績娴佺▼锛?1. 浠巐essons.json璇诲彇澶辫触浠诲姟
2. 鐢熸垚feedback锛堥棶棰樺垎鏋?+ 鏀硅繘寤鸿锛?3. regenerate鏂扮瓥鐣ワ紙鍙墽琛宎ction鍒楄〃锛?4. 閫氳繃sessions_spawn鐪熷疄鎵ц
5. 鎴愬姛 鈫?淇濆瓨鍒癳xperience_library.jsonl + LanceDB
6. 澶辫触 鈫?闇€瑕佷汉宸ヤ粙鍏?7. Phase 3瑙傚療锛氳褰曢噸鐢熺粺璁?+ 鐢熸垚鍥捐〃鎶ュ憡

v4.0 鏀归€狅細
- 闆嗘垚 spawn_manager锛圫tep 3/4 鍏ㄩ摼璺拷韪級
- load_lessons() 鏀逛负浠?experience_engine.harvest_real_failures() 璇诲彇
- 闂ㄧ锛氬彧澶勭悊 source=real + regeneration_status=pending
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import time
from audit_context import audit_event_auto, set_audit_context

# 璁剧疆瀹¤涓婁笅鏂?set_audit_context("lowsuccess-agent", "lowsuccess-session")

# Import unified paths
from paths import (
    LESSONS, EXPERIENCE_LIBRARY, FEEDBACK_LOG,
    SPAWN_REQUESTS, TASK_EXECUTIONS
)

# 璺緞閰嶇疆锛堜繚鐣欏吋瀹规€э級
WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")
AIOS_DIR = WORKSPACE / "aios" / "agent_system"
LESSONS_FILE = LESSONS
EXPERIENCE_LIB = EXPERIENCE_LIBRARY
FEEDBACK_LOG_FILE = FEEDBACK_LOG
TASKS_FILE = AIOS_DIR / "tasks.jsonl"  # 鏆傛椂淇濈暀锛屽悗缁縼绉?
# 娣诲姞璺緞浠ュ鍏essions_spawn
sys.path.insert(0, str(WORKSPACE))

# Phase 3 v3.0闆嗘垚锛歀anceDB缁忛獙瀛︿範
# Phase 4.0 鍗囩骇锛氱伆搴?+ 骞傜瓑 + 鐗堟湰褰掑洜
from experience_learner_v4 import learner_v4

# Phase 3瑙傚療鍣ㄩ泦鎴愶紙缁熶竴浣跨敤 aios/agent_system 涓嬬殑鐗堟湰锛?from phase3_observer import observe_phase3, generate_phase3_report

# v4.0 闆嗘垚锛歴pawn_manager 鍏ㄩ摼璺拷韪?from spawn_manager import build_spawn_requests, record_spawn_result, get_spawn_stats

def load_lessons():
    """
    鍔犺浇澶辫触鏁欒锛圫tep 3 鏀归€狅細浼樺厛浠庣湡瀹炲け璐ヤ腑璇诲彇锛?
    鏁版嵁婧愪紭鍏堢骇锛?    1. task_executions_v2.jsonl锛堢湡瀹炲け璐ワ紝杩囨护 Simulated锛?    2. lessons.json锛堝厹搴曪紝浠呬繚鐣?source=real 鐨勮褰曪級
    """
    import hashlib
    from experience_engine import harvest_real_failures

    # Step 1锛氬厛浠?task_executions_v2.jsonl 鏀跺壊鐪熷疄澶辫触 鈫?鍐欏叆 lessons.json
    try:
        harvested = harvest_real_failures()
        if harvested > 0:
            print(f"  [HARVEST] {harvested} new real failures 鈫?lessons.json")
    except Exception as e:
        print(f"  [WARN] harvest_real_failures failed: {e}")

    # Step 2锛氳鍙?lessons.json锛堟鏃跺凡鍖呭惈鐪熷疄澶辫触锛?
    if not LESSONS_FILE.exists():
        return []

    with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 鍏煎涓ょ鏍煎紡锛歿"lessons": [...]} 鎴栫洿鎺?[...]
    if isinstance(data, list):
        lessons = data
    else:
        lessons = data.get('lessons', [])

    # 闂ㄧ锛氬彧澶勭悊鐪熷疄澶辫触锛堣繃婊ゅ亣鏁版嵁锛?
    real_lessons = []
    for lesson in lessons:
        # 璺宠繃鏄庣‘鏍囪涓?simulated 鐨?
        if lesson.get("source") == "simulated":
            continue
        # 璺宠繃 error_message 浠?Simulated 寮€澶寸殑
        if lesson.get("error_message", "").startswith("Simulated"):
            continue
        # 璺宠繃 regeneration_status 宸插畬鎴愮殑
        if lesson.get("regeneration_status") in ("completed", "skipped"):
            continue
        real_lessons.append(lesson)

    return real_lessons

def get_task_by_id(task_id: str):
    """浠巘asks.jsonl璇诲彇浠诲姟璇︽儏"""
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
    浠庡け璐ヨ建杩圭敓鎴恌eedback锛坰irius鏍稿績鏈哄埗锛?    
    Args:
        lesson: 澶辫触鏁欒璁板綍
    
    Returns:
        feedback瀛楀吀锛堝寘鍚棶棰樺垎鏋愬拰鏀硅繘寤鸿锛?
        """
    error_type = lesson.get('error_type', 'unknown')
    context = lesson.get('context', '')
    
    # 鏍规嵁閿欒绫诲瀷鐢熸垚閽堝鎬eedback
    feedback_templates = {
        'timeout': {
            'problem': '浠诲姟瓒呮椂锛屽彲鑳芥槸浠诲姟澶嶆潅搴﹁繃楂樻垨璧勬簮涓嶈冻',
            'suggestions': [
                '鎷嗗垎浠诲姟涓烘洿灏忕殑瀛愪换鍔?',
                '澧炲姞瓒呮椂鏃堕棿锛?0s 鈫?120s锛?',
                '浼樺寲绠楁硶澶嶆潅搴?'
            ]
        },
        'dependency_error': {
            'problem': '渚濊禆缂哄け鎴栫増鏈啿绐?',
            'suggestions': [
                '鍦ㄤ换鍔″紑濮嬪墠妫€鏌ヤ緷璧?',
                '浣跨敤铏氭嫙鐜闅旂渚濊禆',
                '鏄庣‘鎸囧畾渚濊禆鐗堟湰'
            ]
        },
        'logic_error': {
            'problem': '浠ｇ爜閫昏緫閿欒锛堝闄ら浂銆佺┖鎸囬拡锛?',
            'suggestions': [
                '澧炲姞杈撳叆楠岃瘉',
                '娣诲姞寮傚父澶勭悊',
                '浣跨敤闃插尽鎬х紪绋?'
            ]
        },
        'resource_exhausted': {
            'problem': '璧勬簮鑰楀敖锛堝唴瀛?纾佺洏/缃戠粶锛?',
            'suggestions': [
                '浼樺寲璧勬簮浣跨敤',
                '澧炲姞璧勬簮闄愬埗妫€鏌?',
                '浣跨敤娴佸紡澶勭悊'
            ]
        },
        'api_error': {
            'problem': 'API 璋冪敤澶辫触锛堢綉缁滈敊璇€佹湇鍔′笉鍙敤銆佽璇佸け璐ワ級',
            'suggestions': [
                '瀹炵幇鎸囨暟閫€閬块噸璇曪紙1s 鈫?2s 鈫?4s锛?',
                '娣诲姞澶囩敤 API 绔偣',
                '澧炲姞瓒呮椂鍜岀啍鏂満鍒?',
                '璁板綍璇︾粏閿欒鏃ュ織'
            ]
        }
    }
    
    template = feedback_templates.get(error_type, {
        'problem': '鏈煡閿欒绫诲瀷',
        'suggestions': ['澧炲姞鏃ュ織璁板綍', '娣诲姞閿欒澶勭悊', '浜哄伐瀹℃煡']
    })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'lesson_id': lesson.get('lesson_id', 'unknown'),  # 淇锛氫娇鐢ㄦ纭殑瀛楁鍚?        'error_type': error_type,
        'problem': template['problem'],
        'suggestions': template['suggestions'],
        'context': context
    }

def regenerate_strategy(feedback):
    """
    鍩轰簬feedback閲嶆柊鐢熸垚绛栫暐锛坰irius鏍稿績鏈哄埗锛?    
    Args:
        feedback: feedback瀛楀吀
    
    Returns:
        鏂扮瓥鐣ュ瓧鍏?
        """
    suggestions = feedback['suggestions']
    
    # 灏嗗缓璁浆鍖栦负鍙墽琛岀瓥鐣?
    strategy = {
        'timestamp': datetime.now().isoformat(),
        'feedback_id': feedback.get('lesson_id', 'unknown'),
        'actions': []
    }
    
    for suggestion in suggestions:
        if '鎷嗗垎浠诲姟' in suggestion:
            strategy['actions'].append({
                'type': 'task_decomposition',
                'description': '灏嗕换鍔℃媶鍒嗕负鏇村皬鐨勫瓙浠诲姟',
                'priority': 'high'
            })
        elif '澧炲姞瓒呮椂' in suggestion:
            strategy['actions'].append({
                'type': 'timeout_adjustment',
                'description': '澧炲姞瓒呮椂鏃堕棿鍒?20绉?',
                'priority': 'medium'
            })
        elif '妫€鏌ヤ緷璧? in suggestion:'
            strategy['actions'].append({
                'type': 'dependency_check',
                'description': '鍦ㄤ换鍔″紑濮嬪墠楠岃瘉鎵€鏈変緷璧?',
                'priority': 'high'
            })
        elif '寮傚父澶勭悊' in suggestion:
            strategy['actions'].append({
                'type': 'error_handling',
                'description': '娣诲姞try-catch鍜岃緭鍏ラ獙璇?',
                'priority': 'high'
            })
        elif '璧勬簮闄愬埗' in suggestion:
            strategy['actions'].append({
                'type': 'resource_limit',
                'description': '娣诲姞璧勬簮浣跨敤鐩戞帶鍜岄檺鍒?',
                'priority': 'medium'
            })
    
    return strategy

def regenerate_failed_task_real(lesson):
    """
    鐪熷疄閲嶇敓鎵ц锛圥hase 2鏍稿績 + Phase 4.0 v4闆嗘垚锛?    
    Args:
        lesson: 澶辫触鏁欒璁板綍
    
    Returns:
        (success: bool, result: dict, recommendation: dict)
    """
    task_id = lesson.get('lesson_id', 'unknown')  # 淇锛氫娇鐢ㄦ纭殑瀛楁鍚?    error_type = lesson.get('error_type', 'unknown')
    print(f"[REGEN] 姝ｅ湪涓轰换鍔?{task_id} 鎵цBootstrapped Regeneration...")
    
    # Phase 4.0闆嗘垚锛氫粠缁忛獙搴撴帹鑽愶紙鍚伆搴?+ 鍥炴粴寮€鍏筹級
    recommendation = learner_v4.recommend({
        'error_type': error_type,
        'task_id': task_id,
        'prompt': lesson.get('description', ''),
    })
    rec_strategy = recommendation['recommended_strategy']
    rec_source = recommendation['source']
    rec_version = recommendation['strategy_version']
    print(f"  [REC] Strategy: {rec_strategy} | Source: {rec_source} | Version: {rec_version}")
    
    # 1. 鐢熸垚feedback
    feedback = generate_feedback(lesson)
    print(f"  [OK] 鐢熸垚feedback: {feedback['problem']}")
    
    # 2. regenerate鏂扮瓥鐣?
    strategy = regenerate_strategy(feedback)
    print(f"  [OK] 鐢熸垚绛栫暐: {len(strategy['actions'])} 涓猘ction")
    
    # 3. 鏋勫缓澧炲己鐨勪换鍔℃弿杩帮紙鍖呭惈feedback銆乻trategy鍜岀粡楠屾帹鑽愶級
    rec_block = ""
    if rec_source == "experience":
        rec_block = f
        """
[鍘嗗彶缁忛獙鎺ㄨ崘 (v={rec_version}, confidence={recommendation['confidence']:.2f})]
鎺ㄨ崘绛栫暐: {rec_strategy}
"""
    
    enhanced_task = f
    """
浠诲姟閲嶇敓锛圔ootstrapped Regeneration v4.0锛?
鍘熷浠诲姟ID: {task_id}
閿欒绫诲瀷: {feedback['error_type']}
绛栫暐鐗堟湰: {rec_version}
{rec_block}
闂鍒嗘瀽:
{feedback['problem']}

鏀硅繘寤鸿:
{chr(10).join(f"- {s}" for s in feedback['suggestions'])}

鎵ц绛栫暐:
{chr(10).join(f"- [{a['priority']}] {a['description']}" for a in strategy['actions'])}

璇锋牴鎹互涓婂垎鏋愬拰绛栫暐锛岄噸鏂版墽琛屼换鍔°€?
"""
    
    # 4. 閫氳繃 spawn_manager 鐢熸垚鏍囧噯 spawn 璇锋眰锛圫tep 3 鍏ㄩ摼璺級
    # 鍏堟妸 enhanced_task 鍐欏洖 lesson 鐨?context锛岃 build_spawn_requests 鑳借鍒?    # 杩欓噷鐩存帴鍐欏叆 spawn_requests.jsonl锛堝吋瀹规棫鏍煎紡 + 鏂版牸寮忓弻鍐欙級
    spawn_id = f"spawn-{lesson.get('lesson_id', task_id)}"
    spawn_request = {
        'spawn_id': spawn_id,
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'lesson_id': lesson.get('lesson_id', task_id),
        'source_task_id': lesson.get('source_task_id', task_id),
        'agent_id': 'LowSuccess_Agent',
        'task': enhanced_task,
        'label': f'aios-regen-{task_id}',
        'cleanup': 'keep',
        'runTimeoutSeconds': 120,
        'regeneration': True,
        'status': 'queued',
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

    spawn_file = SPAWN_REQUESTS
    with open(spawn_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(spawn_request, ensure_ascii=False) + '\n')

    print(f"  [OK] Spawn璇锋眰宸茬敓鎴? {spawn_file}")
    
    return True, {
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'status': 'pending',
        'spawn_request': spawn_request,
    }, recommendation

def save_to_experience_library(feedback, strategy, result):
    """
    淇濆瓨鎴愬姛杞ㄨ抗鍒癳xperience_library锛坰irius鏍稿績鏈哄埗锛?    
    Args:
        feedback: feedback瀛楀吀
        strategy: 绛栫暐瀛楀吀
        result: 鎵ц缁撴灉
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
    
    # 杩藉姞鍒癳xperience_library.jsonl
    with open(EXPERIENCE_LIB, 'a', encoding='utf-8') as f:
        f.write(json.dumps(experience, ensure_ascii=False) + '\n')

def save_feedback(feedback):
    """淇濆瓨feedback鍒版棩蹇?""
    with open(FEEDBACK_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(feedback, ensure_ascii=False) + '\n')

def get_already_spawned_ids():
    """鑾峰彇宸茬粡鐢熸垚杩?spawn 璇锋眰鐨?lesson ID锛岄伩鍏嶉噸澶嶇敓鎴?""
    spawn_file = SPAWN_REQUESTS
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
    杩愯LowSuccess_Agent閲嶇敓娴佺▼锛圚eartbeat璋冪敤锛? Phase 3瑙傚療
    
    Args:
        limit: 姣忔鏈€澶氬鐞嗙殑浠诲姟鏁?    
    Returns:
        澶勭悊缁熻
    """
    # 鍔犺浇澶辫触鏁欒
    lessons = load_lessons()
    if not lessons:
        return {'processed': 0, 'success': 0, 'failed': 0, 'pending': 0}
    
    # 鍘婚噸锛氳烦杩囧凡缁忕敓鎴愯繃 spawn 璇锋眰鐨?lesson
    already_spawned = get_already_spawned_ids()
    lessons = [l for l in lessons if l.get('id') not in already_spawned]
    
    if not lessons:
        print(f"  [OK] All {len(already_spawned)} lessons already have spawn requests, skipping")
        return {'processed': 0, 'success': 0, 'failed': 0, 'pending': 0}
    
    # 闄愬埗澶勭悊鏁伴噺
    lessons_to_process = lessons[:limit]
    
    stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'pending': 0
    }
    
    # 瀵规瘡涓け璐ユ暀璁墽琛宐ootstrapped regeneration
    for lesson in lessons_to_process:
        start_time = time.time()
        
        # 瀹¤鏃ュ織锛歱olicy.allow锛堝厑璁搁噸鐢燂級
        audit_event_auto(
            action_type="policy.allow",
            target="spawn_generation",
            params={
                "lesson_id": lesson.get("id"),
                "source": lesson.get("source"),
                "error_type": lesson.get("error_type"),
                "error_message": lesson.get("error_message", "")[:200],
            },
            result="allowed",
            risk_level="medium",
            reason="source=real and regeneration_status=pending",
            lesson_id=lesson.get("id"),
            source_task_id=lesson.get("source_task_id"),
        )
        
        success, result, recommendation = regenerate_failed_task_real(lesson)
        recovery_time = time.time() - start_time
        
        stats['processed'] += 1
        
        # Phase 3瑙傚療锛氳褰曟瘡娆￠噸鐢?        task_id = lesson.get('lesson_id', 'unknown')  # 淇锛氫娇鐢ㄦ纭殑瀛楁鍚?        task_description = lesson.get('task_description', '')  # 淇锛氫娇鐢ㄦ纭殑瀛楁鍚?        observe_phase3(task_id, task_description, success, recovery_time)
        
        if success:
            if result.get('status') == 'pending':
                stats['pending'] += 1
            else:
                stats['success'] += 1
                
                # Phase 4.0闆嗘垚锛氫繚瀛樻垚鍔熻建杩癸紙骞傜瓑 + 鐗堟湰锛?
                learner_v4.save_success({
                    'task_id': task_id,
                    'error_type': lesson.get('error_type', 'unknown'),
                    'strategy': recommendation.get('recommended_strategy', 'default_recovery'),
                    'confidence': 0.85,
                    'recovery_time': recovery_time,
                    'strategy_version': recommendation.get('strategy_version', 'v4.0.0'),
                })
                
                # 杩借釜鎺ㄨ崘鍚庣粨鏋滐紙鍒嗘《锛?
                learner_v4.track_outcome(
                    task_id=task_id,
                    strategy=recommendation.get('recommended_strategy', 'default_recovery'),
                    source=recommendation.get('source', 'default'),
                    success=True,
                )
        else:
            stats['failed'] += 1
            
            # 杩借釜鎺ㄨ崘鍚庡け璐ワ紙鍒嗘《锛?
            learner_v4.track_outcome(
                task_id=task_id,
                strategy=recommendation.get('recommended_strategy', 'default_recovery'),
                source=recommendation.get('source', 'default'),
                success=False,
            )
    
    # Phase 3瑙傚療锛氱敓鎴愭姤鍛?
    if stats['processed'] > 0:
        generate_phase3_report()
    
    print(f"\n[PHASE3] LowSuccess_Agent v3.0 completed (LanceDB recommendations applied)")
    return stats

def main():
    """main function"""
    print("LowSuccess_Agent v3.0 - Phase 2: 鐪熷疄Agent鎵ц")
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

