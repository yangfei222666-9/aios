"""
Spawn Manager - LowSuccess Regeneration 鍏ㄩ摼璺拷韪?
Step 3: build_spawn_requests()  - 浠?lessons.json 鐢熸垚閲嶇敓璇锋眰
Step 4: record_spawn_result()   - 鎵ц缁撴灉鍥炲啓

鍏ㄩ摼璺細
  task_executions_v2.jsonl (failed)
    鈫?lessons.json (source=real, pending)
    鈫?spawn_requests.jsonl (queued)
    鈫?spawn_results.jsonl (success/failed)
"""

import json
import os
from datetime import datetime, timezone
from audit_context import audit_event_auto, set_audit_context

LESSONS_PATH = "lessons.json"
SPAWN_REQUESTS_PATH = "spawn_requests.jsonl"
SPAWN_RESULTS_PATH = "spawn_results.jsonl"

# 璁剧疆瀹¤涓婁笅鏂?set_audit_context("spawn-manager", "spawn-session")


def build_spawn_requests():
    """鍙粠 source=real + status=pending 鐨?lessons 鐢熸垚閲嶇敓璇锋眰"""
    if not os.path.exists(LESSONS_PATH):
        print("[WARN] lessons.json not found")
        return 0

    with open(LESSONS_PATH, "r", encoding="utf-8") as f:
        lessons = json.load(f)

    # 鍔犺浇宸叉湁 spawn_requests锛岄伩鍏嶉噸澶嶇敓鎴?    existing_spawn_ids = set()
    if os.path.exists(SPAWN_REQUESTS_PATH):
        with open(SPAWN_REQUESTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                    existing_spawn_ids.add(req.get("lesson_id"))
                except Exception:
                    continue

    requests = []
    for lesson in lessons:
        # 鍙岄噸闂ㄧ
        if lesson.get("source") != "real":
            continue
        if lesson.get("regeneration_status") != "pending":
            continue
        # 鍘婚噸
        if lesson.get("lesson_id") in existing_spawn_ids:
            continue

        req = {
            "spawn_id": f"spawn-{lesson['lesson_id']}",
            "source_task_id": lesson["source_task_id"],
            "lesson_id": lesson["lesson_id"],
            "task_description": lesson["task_description"],
            "error_type": lesson["error_type"],
            "error_context": lesson.get("context", {}),
            "original_error": lesson["error_message"][:200],  # 鎴柇瓒呴暱 error
            "created_at": lesson["harvested_at"],
            "status": "queued"
        }
        requests.append(req)

    if requests:
        with open(SPAWN_REQUESTS_PATH, "a", encoding="utf-8") as f:
            for req in requests:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
        print(f"[OK] build_spawn_requests: {len(requests)} new requests 鈫?{SPAWN_REQUESTS_PATH}")
        
        # 瀹¤鏃ュ織锛歴pawn.request
        audit_event_auto(
            action_type="spawn.request",
            target=SPAWN_REQUESTS_PATH,
            params={
                "count": len(requests),
                "spawn_ids": [r["spawn_id"] for r in requests],
            },
            result="success",
            risk_level="medium",
            reason="build from low-success lessons",
            extra={"lessons": [r["lesson_id"] for r in requests]}
        )
    else:
        print("[OK] build_spawn_requests: no new requests")

    return len(requests)


def record_spawn_result(spawn_id, lesson_id, success, duration_s, error=None, retries=0):
    """閲嶇敓缁撴灉鍐欏叆 spawn_results.jsonl + 鏇存柊 lessons.json 鐘舵€?""
    result = {
        "spawn_id": spawn_id,
        "lesson_id": lesson_id,
        "success": success,
        "duration_s": round(duration_s, 2),
        "error": error,
        "retries": retries,
        "completed_at": datetime.now(timezone.utc).isoformat()
    }

    # append-only 缁撴灉鏃ュ織
    with open(SPAWN_RESULTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    # 瀹¤鏃ュ織锛歴pawn.result
    audit_event_auto(
        action_type="spawn.result",
        target=spawn_id,
        params={
            "status": "success" if success else "failed",
            "error_message": error,
            "duration_s": duration_s,
            "retries": retries,
        },
        result="success" if success else "failed",
        risk_level="medium",
        lesson_id=lesson_id,
        spawn_id=spawn_id,
    )

    # 鏇存柊 lesson 鐘舵€?    if os.path.exists(LESSONS_PATH):
        with open(LESSONS_PATH, "r", encoding="utf-8") as f:
            lessons = json.load(f)

        for lesson in lessons:
            if lesson["lesson_id"] == lesson_id:
                lesson["regeneration_status"] = "success" if success else "failed"
                lesson["last_spawn_id"] = spawn_id
                lesson["last_updated"] = datetime.now(timezone.utc).isoformat()
                break

        with open(LESSONS_PATH, "w", encoding="utf-8") as f:
            json.dump(lessons, f, indent=2, ensure_ascii=False)
        
        # 瀹¤鏃ュ織锛歠ile.modify
        audit_event_auto(
            action_type="file.modify",
            target=LESSONS_PATH,
            params={
                "operation": "update_lesson_status",
                "lesson_id": lesson_id,
                "new_status": "success" if success else "failed",
            },
            result="success",
            risk_level="medium",
            lesson_id=lesson_id,
            spawn_id=spawn_id,
        )

    status = "success" if success else "failed"
    print(f"[OK] record_spawn_result: {spawn_id} 鈫?{status} ({duration_s:.1f}s)")
    return result


def get_spawn_stats():
    """缁熻 spawn 鍏ㄩ摼璺姸鎬?""
    stats = {
        "lessons_total": 0,
        "lessons_pending": 0,
        "lessons_success": 0,
        "lessons_failed": 0,
        "spawn_queued": 0,
        "spawn_results_success": 0,
        "spawn_results_failed": 0,
    }

    # lessons 缁熻
    if os.path.exists(LESSONS_PATH):
        with open(LESSONS_PATH, "r", encoding="utf-8") as f:
            lessons = json.load(f)
        stats["lessons_total"] = len(lessons)
        for l in lessons:
            s = l.get("regeneration_status", "pending")
            if s == "pending":
                stats["lessons_pending"] += 1
            elif s == "success":
                stats["lessons_success"] += 1
            elif s == "failed":
                stats["lessons_failed"] += 1

    # spawn_requests 缁熻
    if os.path.exists(SPAWN_REQUESTS_PATH):
        with open(SPAWN_REQUESTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    stats["spawn_queued"] += 1

    # spawn_results 缁熻
    if os.path.exists(SPAWN_RESULTS_PATH):
        with open(SPAWN_RESULTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    if r.get("success"):
                        stats["spawn_results_success"] += 1
                    else:
                        stats["spawn_results_failed"] += 1
                except Exception:
                    continue

    return stats


if __name__ == "__main__":
    print("Spawn Manager - Full Chain Verification")
    print("=" * 60)

    # Step 3: 鐢熸垚 spawn 璇锋眰
    n = build_spawn_requests()

    # 鎵撳嵃鍏ㄩ摼璺粺璁?    stats = get_spawn_stats()
    print("\n[CHAIN STATS]")
    print(f"  lessons total:          {stats['lessons_total']}")
    print(f"  lessons pending:        {stats['lessons_pending']}")
    print(f"  lessons success:        {stats['lessons_success']}")
    print(f"  lessons failed:         {stats['lessons_failed']}")
    print(f"  spawn_requests queued:  {stats['spawn_queued']}")
    print(f"  spawn_results success:  {stats['spawn_results_success']}")
    print(f"  spawn_results failed:   {stats['spawn_results_failed']}")

