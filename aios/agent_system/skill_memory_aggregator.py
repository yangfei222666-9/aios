"""
Skill Memory Aggregator - 每小时聚合所有 Skill 的统计信息

集成到 Heartbeat v5.0，每小时自动运行
"""

import json
from pathlib import Path
from datetime import datetime
from skill_memory import skill_memory
from paths import DATA_DIR

SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"


def aggregate_all_skills():
    """聚合所有 Skill 的统计信息"""
    if not SKILL_EXECUTIONS_FILE.exists():
        print("[SKILL_MEMORY] No execution records found")
        return
    
    # 读取所有执行记录，提取唯一的 skill_id
    skill_ids = set()
    with open(SKILL_EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    skill_ids.add(record["skill_id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    
    if not skill_ids:
        print("[SKILL_MEMORY] No skills to aggregate")
        return
    
    print(f"[SKILL_MEMORY] Aggregating {len(skill_ids)} skills...")
    
    # 为每个 Skill 更新统计
    updated_count = 0
    for skill_id in skill_ids:
        try:
            memory = skill_memory.update_skill_stats(skill_id)
            if memory:
                print(f"  ✓ {skill_id}: {memory['usage_count']} uses, {memory['success_rate']:.1%} success, {memory['evolution_score']:.1f}/100 evolution")
                updated_count += 1
        except Exception as e:
            print(f"  ✗ {skill_id}: {e}")
    
    print(f"[SKILL_MEMORY] Updated {updated_count}/{len(skill_ids)} skills")


def show_top_skills(top_n: int = 5):
    """显示 Top N 技能（按演化分数排序）"""
    all_skills = skill_memory.get_all_skills()
    
    if not all_skills:
        print("[SKILL_MEMORY] No skills in memory")
        return
    
    # 按演化分数排序
    sorted_skills = sorted(all_skills, key=lambda s: s.get("evolution_score", 0), reverse=True)
    
    print(f"\n[SKILL_MEMORY] Top {top_n} Skills (by Evolution Score):")
    print("=" * 80)
    
    for i, skill in enumerate(sorted_skills[:top_n], 1):
        print(f"{i}. {skill['skill_id']}")
        print(f"   Evolution Score: {skill['evolution_score']:.1f}/100")
        print(f"   Usage: {skill['usage_count']} times | Success Rate: {skill['success_rate']:.1%}")
        print(f"   Avg Duration: {skill['avg_execution_time_ms']:.0f}ms")
        print(f"   Last Used: {skill['last_used']}")
        
        if skill.get("common_patterns"):
            print(f"   Common Patterns:")
            for pattern in skill["common_patterns"][:3]:
                print(f"     - {pattern['pattern']}: {pattern['usage_count']} uses, {pattern['success_rate']:.1%} success")
        
        if skill.get("failure_lessons"):
            print(f"   Failure Lessons:")
            for lesson in skill["failure_lessons"][:2]:
                print(f"     - {lesson['error_type']}: {lesson['count']} times → {lesson['recovery_strategy']}")
        
        print()


if __name__ == "__main__":
    import sys
    
    if "--top" in sys.argv:
        # 只显示 Top 技能
        show_top_skills(top_n=10)
    else:
        # 聚合所有技能
        aggregate_all_skills()
        show_top_skills(top_n=5)
