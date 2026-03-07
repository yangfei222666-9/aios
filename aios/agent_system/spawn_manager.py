"""
Spawn Manager - LowSuccess Regeneration 全链路追踪

Step 3: build_spawn_requests()  - 从 lessons.json 生成重生请求
Step 4: record_spawn_result()   - 执行结果回写

全链路：
  task_executions.jsonl (failed)
    → lessons.json (source=real, pending)
    → spawn_requests.jsonl (queued)
    → spawn_results.jsonl (success/failed)
"""

import json
import os
from datetime import datetime, timezone
from audit_context import audit_event_auto, set_audit_context

LESSONS_PATH = "lessons.json"
SPAWN_REQUESTS_PATH = "spawn_requests.jsonl"
SPAWN_RESULTS_PATH = "spawn_results.jsonl"

# 设置审计上下文
set_audit_context("spawn-manager", "spawn-session")


def build_spawn_requests():
    """只从 source=real + status=pending 的 lessons 生成重生请求"""
    if not os.path.exists(LESSONS_PATH):
        print("[WARN] lessons.json not found")
        return 0

    with open(LESSONS_PATH, "r", encoding="utf-8") as f:
        lessons = json.load(f)

    # 加载已有 spawn_requests，避免重复生成
    existing_spawn_ids = set()
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
        # 双重门禁
        if lesson.get("source") != "real":
            continue
        if lesson.get("regeneration_status") != "pending":
            continue
        # 去重
        if lesson.get("lesson_id") in existing_spawn_ids:
            continue

        req = {
            "spawn_id": f"spawn-{lesson['lesson_id']}",
            "source_task_id": lesson["source_task_id"],
            "lesson_id": lesson["lesson_id"],
            "task_description": lesson["task_description"],
            "error_type": lesson["error_type"],
            "error_context": lesson.get("context", {}),
            "original_error": lesson["error_message"][:200],  # 截断超长 error
            "created_at": lesson["harvested_at"],
            "status": "queued"
        }
        requests.append(req)

    if requests:
        with open(SPAWN_REQUESTS_PATH, "a", encoding="utf-8") as f:
            for req in requests:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
        print(f"[OK] build_spawn_requests: {len(requests)} new requests → {SPAWN_REQUESTS_PATH}")
        
        # 审计日志：spawn.request
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
    """重生结果写入 spawn_results.jsonl + 更新 lessons.json 状态"""
    result = {
        "spawn_id": spawn_id,
        "lesson_id": lesson_id,
        "success": success,
        "duration_s": round(duration_s, 2),
        "error": error,
        "retries": retries,
        "completed_at": datetime.now(timezone.utc).isoformat()
    }

    # append-only 结果日志
    with open(SPAWN_RESULTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    # 审计日志：spawn.result
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

    # 更新 lesson 状态
    if os.path.exists(LESSONS_PATH):
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
        
        # 审计日志：file.modify
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
    print(f"[OK] record_spawn_result: {spawn_id} → {status} ({duration_s:.1f}s)")
    return result


def get_spawn_stats():
    """统计 spawn 全链路状态"""
    stats = {
        "lessons_total": 0,
        "lessons_pending": 0,
        "lessons_success": 0,
        "lessons_failed": 0,
        "spawn_queued": 0,
        "spawn_results_success": 0,
        "spawn_results_failed": 0,
    }

    # lessons 统计
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

    # spawn_requests 统计
    if os.path.exists(SPAWN_REQUESTS_PATH):
        with open(SPAWN_REQUESTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    stats["spawn_queued"] += 1

    # spawn_results 统计
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

    # Step 3: 生成 spawn 请求
    n = build_spawn_requests()

    # 打印全链路统计
    stats = get_spawn_stats()
    print("\n[CHAIN STATS]")
    print(f"  lessons total:          {stats['lessons_total']}")
    print(f"  lessons pending:        {stats['lessons_pending']}")
    print(f"  lessons success:        {stats['lessons_success']}")
    print(f"  lessons failed:         {stats['lessons_failed']}")
    print(f"  spawn_requests queued:  {stats['spawn_queued']}")
    print(f"  spawn_results success:  {stats['spawn_results_success']}")
    print(f"  spawn_results failed:   {stats['spawn_results_failed']}")
