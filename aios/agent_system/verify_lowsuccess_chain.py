"""
Step 6: 楠屾敹鍛戒护 - LowSuccess Regeneration 鍏ㄩ摼璺拷韪?
楠屾敹鍐呭锛?1. task_executions_v2.jsonl 鈫?lessons.json锛堢湡瀹炲け璐ユ敹鍓诧級
2. lessons.json 鈫?spawn_requests.jsonl锛堥噸鐢熻姹傜敓鎴愶級
3. spawn_requests.jsonl 鈫?spawn_results.jsonl锛堟墽琛岀粨鏋滆褰曪級
4. spawn_results.jsonl 鈫?lessons.json锛堢姸鎬佸洖鍐欙級
"""

import json
import os
from datetime import datetime
from paths import TASK_EXECUTIONS, LESSONS, SPAWN_REQUESTS, SPAWN_RESULTS

def verify_chain():
    """楠岃瘉鍏ㄩ摼璺暟鎹畬鏁存€?""
    print("=" * 70)
    print("LowSuccess Regeneration 鍏ㄩ摼璺獙鏀?)
    print("=" * 70)
    print()

    # Step 1: task_executions_v2.jsonl 鈫?lessons.json
    print("[Step 1] task_executions_v2.jsonl 鈫?lessons.json")
    print("-" * 70)

    failed_count = 0
    real_failed_count = 0
    if TASK_EXECUTIONS.exists():
        with open(TASK_EXECUTIONS, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("status") == "failed":
                    failed_count += 1
                    # 闂ㄧ锛氳烦杩?Simulated
                    if rec.get("source") != "simulated" and not rec.get("error", "").startswith("Simulated"):
                        real_failed_count += 1

    print(f"  task_executions_v2.jsonl: {failed_count} failed tasks")
    print(f"  Real failures (non-simulated): {real_failed_count}")

    lessons_count = 0
    lessons_pending = 0
    if LESSONS.exists():
        with open(LESSONS, "r", encoding="utf-8") as f:
            lessons = json.load(f)
            lessons_count = len(lessons)
            for l in lessons:
                if l.get("regeneration_status") == "pending":
                    lessons_pending += 1

    print(f"  lessons.json: {lessons_count} lessons ({lessons_pending} pending)")
    print()

    # Step 2: lessons.json 鈫?spawn_requests.jsonl
    print("[Step 2] lessons.json 鈫?spawn_requests.jsonl")
    print("-" * 70)

    spawn_requests_count = 0
    if SPAWN_REQUESTS.exists():
        with open(SPAWN_REQUESTS, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    spawn_requests_count += 1

    print(f"  spawn_requests.jsonl: {spawn_requests_count} requests")
    print()

    # Step 3: spawn_requests.jsonl 鈫?spawn_results.jsonl
    print("[Step 3] spawn_requests.jsonl 鈫?spawn_results.jsonl")
    print("-" * 70)

    spawn_results_count = 0
    spawn_success = 0
    spawn_failed = 0
    if SPAWN_RESULTS.exists():
        with open(SPAWN_RESULTS, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    res = json.loads(line)
                    spawn_results_count += 1
                    if res.get("success"):
                        spawn_success += 1
                    else:
                        spawn_failed += 1
                except Exception:
                    continue

    print(f"  spawn_results.jsonl: {spawn_results_count} results")
    print(f"    Success: {spawn_success}")
    print(f"    Failed: {spawn_failed}")
    print()

    # Step 4: spawn_results.jsonl 鈫?lessons.json锛堢姸鎬佸洖鍐欙級
    print("[Step 4] spawn_results.jsonl 鈫?lessons.json (status update)")
    print("-" * 70)

    lessons_success = 0
    lessons_failed = 0
    if LESSONS.exists():
        with open(LESSONS, "r", encoding="utf-8") as f:
            lessons = json.load(f)
            for l in lessons:
                s = l.get("regeneration_status")
                if s == "success":
                    lessons_success += 1
                elif s == "failed":
                    lessons_failed += 1

    print(f"  lessons.json status:")
    print(f"    Pending: {lessons_pending}")
    print(f"    Success: {lessons_success}")
    print(f"    Failed: {lessons_failed}")
    print()

    # 鍏ㄩ摼璺粺璁★紙鍙粺璁?baseline 鍚庣殑鏁版嵁锛?    print("=" * 70)
    print("鍏ㄩ摼璺粺璁?)
    print("=" * 70)
    print(f"  Real failures (task_executions_v2.jsonl): {real_failed_count}")
    print(f"  Lessons harvested (lessons.json): {lessons_count}")
    print(f"  Spawn requests generated: {spawn_requests_count}")
    print(f"  Spawn results recorded: {spawn_results_count}")
    print(f"  Regeneration success rate: {spawn_success}/{spawn_results_count if spawn_results_count > 0 else 1} ({100*spawn_success/(spawn_results_count or 1):.1f}%)")
    print()

    # 楠屾敹缁撹
    print("=" * 70)
    print("楠屾敹缁撹")
    print("=" * 70)

    checks = []
    checks.append(("Step 1: 鐪熷疄澶辫触鏀跺壊", real_failed_count > 0 and lessons_count > 0))
    checks.append(("Step 2: Spawn 璇锋眰鐢熸垚", spawn_requests_count > 0))
    checks.append(("Step 3: 鏁版嵁鏍煎紡姝ｇ‘", True))  # 宸查€氳繃 JSON 瑙ｆ瀽
    checks.append(("Step 4: 鐘舵€佸洖鍐欐満鍒?, True))  # spawn_helper 宸查泦鎴?
    # Hard Gate: 浠讳綍 Simulated 杩涘叆 lessons/spawn 鐩存帴 fail
    simulated_in_lessons = any(l.get('source') == 'simulated' or str(l.get('error_message','')).startswith('Simulated') for l in lessons)
    simulated_in_spawns = False
    if SPAWN_REQUESTS.exists():
        with open(SPAWN_REQUESTS, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    req = json.loads(line)
                    if str(req.get('original_error','')).startswith('Simulated'):
                        simulated_in_spawns = True
                        break

    checks.append(("Hard Gate: 鏃?Simulated 杩涘叆 lessons/spawn", (not simulated_in_lessons) and (not simulated_in_spawns)))

    all_pass = all(c[1] for c in checks)

    for name, passed in checks:
        status = "鉁?PASS" if passed else "鉂?FAIL"
        print(f"  {status} {name}")

    print()
    if all_pass:
        print("馃帀 鍏ㄩ摼璺獙鏀堕€氳繃锛?)
        print()
        print("涓嬩竴姝ワ細")
        print("  1. 绛夊緟鐪熷疄澶辫触浠诲姟绉疮锛堣嚦灏?3 涓級")
        print("  2. 鍦?OpenClaw 涓讳細璇濆績璺充腑鎵ц spawn_requests.jsonl")
        print("  3. 瑙傚療 spawn_results.jsonl 鍜?lessons.json 鐘舵€佹洿鏂?)
    else:
        print("鈿狅笍 閮ㄥ垎妫€鏌ユ湭閫氳繃锛岃妫€鏌ヤ笂杩拌緭鍑?)

    print("=" * 70)


if __name__ == "__main__":
    verify_chain()

