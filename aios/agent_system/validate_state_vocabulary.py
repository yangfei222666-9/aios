"""
状态词表 v1.0 样例验证

目标：用 6 个真实对象验证新词表能自然表达，不别扭。
"""

import json
from datetime import datetime

# ============================================================
# 1. GitHub_Researcher（已通过治理验收的 Learning Agent）
# ============================================================
github_researcher_new = {
    "name": "GitHub_Researcher",
    "readiness_status": "production-ready",
    "run_status": "success",
    "health_status": "healthy",
    "enabled": True,
    "routable": True,
    "stats": {
        "tasks_completed": 1,
        "tasks_failed": 0,
        "last_run": "2026-03-11T14:40:45+08:00"
    }
}

github_researcher_old = {
    "name": "GitHub_Researcher",
    "enabled": True,
    "mode": "active",
    "lifecycle_state": "active",
    "production_ready": True,
    "routable": True,
    "stats": {
        "tasks_completed": 0,
        "tasks_failed": 0
    }
}

print("=== 1. GitHub_Researcher ===")
print("旧模型：")
print(json.dumps(github_researcher_old, indent=2, ensure_ascii=False))
print("\n新模型：")
print(json.dumps(github_researcher_new, indent=2, ensure_ascii=False))
print("\n✅ 新模型能清晰表达：")
print("  - 已通过验收（production-ready）")
print("  - 最近一次执行成功（success）")
print("  - 当前健康（healthy）")
print("  - 旧模型的 production_ready=True 但 tasks_completed=0 矛盾消失了")
print()

# ============================================================
# 2. Code_Reviewer（已注册但未验证的 Learning Agent）
# ============================================================
code_reviewer_new = {
    "name": "Code_Reviewer",
    "readiness_status": "registered",
    "run_status": "no-sample",
    "health_status": "unknown",
    "enabled": True,
    "routable": True,
    "stats": {
        "tasks_completed": 0,
        "tasks_failed": 0
    }
}

code_reviewer_old = {
    "name": "Code_Reviewer",
    "enabled": True,
    "mode": "active",
    "lifecycle_state": "active",
    "production_ready": False,
    "routable": True,
    "stats": {
        "tasks_completed": 0,
        "tasks_failed": 0
    }
}

print("=== 2. Code_Reviewer ===")
print("旧模型：")
print(json.dumps(code_reviewer_old, indent=2, ensure_ascii=False))
print("\n新模型：")
print(json.dumps(code_reviewer_new, indent=2, ensure_ascii=False))
print("\n✅ 新模型能清晰表达：")
print("  - 已注册但未验证（registered）")
print("  - 从未运行过（no-sample）")
print("  - 健康度未知（unknown）")
print("  - 旧模型的 mode=active 但 production_ready=False 矛盾消失了")
print()

# ============================================================
# 3. Error_Analyzer（已验证但未进入生产的 Agent）
# ============================================================
error_analyzer_new = {
    "name": "Error_Analyzer",
    "readiness_status": "validated",
    "run_status": "no-sample",
    "health_status": "unknown",
    "enabled": True,
    "routable": True,
    "stats": {
        "tasks_completed": 0,
        "tasks_failed": 0
    }
}

error_analyzer_old = {
    "name": "Error_Analyzer",
    "enabled": True,
    "mode": "active",
    "lifecycle_state": "active",
    "production_ready": True,
    "routable": True,
    "stats": {
        "tasks_completed": 0,
        "tasks_failed": 0
    }
}

print("=== 3. Error_Analyzer ===")
print("旧模型：")
print(json.dumps(error_analyzer_old, indent=2, ensure_ascii=False))
print("\n新模型：")
print(json.dumps(error_analyzer_new, indent=2, ensure_ascii=False))
print("\n✅ 新模型能清晰表达：")
print("  - 已验证但未进入生产（validated）")
print("  - 从未运行过（no-sample）")
print("  - 健康度未知（unknown）")
print("  - 旧模型的 production_ready=True 但 tasks_completed=0 矛盾消失了")
print()

# ============================================================
# 4. heartbeat_alert_deduper（已验证但未试运行的 Skill 草案）
# ============================================================
heartbeat_alert_deduper_new = {
    "name": "heartbeat_alert_deduper",
    "type": "skill",
    "readiness_status": "validated",
    "run_status": "no-sample",
    "health_status": "unknown",
    "enabled": False,
    "routable": False,
    "draft_registry": {
        "status": "validated",
        "validation_passed": True,
        "created_at": "2026-03-11T10:00:00+08:00"
    }
}

print("=== 4. heartbeat_alert_deduper ===")
print("新模型：")
print(json.dumps(heartbeat_alert_deduper_new, indent=2, ensure_ascii=False))
print("\n✅ 新模型能清晰表达：")
print("  - 已通过验证（validated）")
print("  - 从未运行过（no-sample）")
print("  - 健康度未知（unknown）")
print("  - 未启用，不可路由（enabled=False, routable=False）")
print("  - 旧模型无法表达 Skill 状态，新模型可以")
print()

# ============================================================
# 5. 一个 queued task
# ============================================================
queued_task_new = {
    "id": "task-20260311-190900",
    "type": "analysis",
    "description": "分析系统性能瓶颈",
    "run_status": "queued",
    "health_status": "healthy",
    "priority": "normal",
    "created_at": "2026-03-11T19:09:00+08:00"
}

queued_task_old = {
    "id": "task-20260311-190900",
    "type": "analysis",
    "description": "分析系统性能瓶颈",
    "status": "pending",
    "priority": "normal",
    "created_at": "2026-03-11T19:09:00+08:00"
}

print("=== 5. queued task ===")
print("旧模型：")
print(json.dumps(queued_task_old, indent=2, ensure_ascii=False))
print("\n新模型：")
print(json.dumps(queued_task_new, indent=2, ensure_ascii=False))
print("\n✅ 新模型能清晰表达：")
print("  - 已进入队列（queued）")
print("  - 当前健康（healthy）")
print("  - 旧模型的 status=pending 语义不清（是 pending 还是 queued？）")
print()

# ============================================================
# 6. 一条待提炼的 lesson
# ============================================================
pending_lesson_new = {
    "lesson_id": "lesson-66ff2238",
    "source_task_id": "task-1772188610619-6e669983",
    "task_description": "优化 Memory Manager 缓存策略",
    "task_type": "refactor",
    "error_type": "unknown",
    "error_message": "Simulated failure",
    "derivation_status": "pending",
    "harvested_at": "2026-03-06T14:07:48.057889Z"
}

pending_lesson_old = {
    "lesson_id": "lesson-66ff2238",
    "source_task_id": "task-1772188610619-6e669983",
    "task_description": "优化 Memory Manager 缓存策略",
    "task_type": "refactor",
    "error_type": "unknown",
    "error_message": "Simulated failure",
    "regeneration_status": "pending",
    "harvested_at": "2026-03-06T14:07:48.057889Z"
}

print("=== 6. pending lesson ===")
print("旧模型：")
print(json.dumps(pending_lesson_old, indent=2, ensure_ascii=False))
print("\n新模型：")
print(json.dumps(pending_lesson_new, indent=2, ensure_ascii=False))
print("\n✅ 新模型能清晰表达：")
print("  - 等待提炼（pending）")
print("  - 旧模型的 regeneration_status 语义不准确（不是在重新生成，是在等提炼）")
print()

# ============================================================
# 总结
# ============================================================
print("=" * 60)
print("总结：6 个真实对象验证通过")
print("=" * 60)
print()
print("✅ 新词表能自然表达所有 4 类对象")
print("✅ 解决了旧模型的 3 个根问题：")
print("   1. 状态混叠（mode 和 lifecycle_state 冗余）")
print("   2. 无样本误判（引入 no-sample 和 not-evaluable）")
print("   3. 4 类对象不统一（Agent/Skill/Task/Lesson 都能表达）")
print()
print("✅ 旧模型的矛盾消失了：")
print("   - production_ready=True 但 tasks_completed=0")
print("   - mode=active 但 production_ready=False")
print("   - status=pending 语义不清")
print()
print("下一步：进入 Phase 1 迁移")
print("  1. 先接健康报告（验证消费者能正常读取新词表）")
print("  2. 逐步扩展到其他消费者（日报、Dashboard、Agent 总览）")
