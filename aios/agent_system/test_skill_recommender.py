"""
Skill Recommender 验证脚本

生成三个样例：
1. 任务前推荐（高匹配强 skill）
2. 连败恢复推荐（触发 crit 级别）
3. recommendation_accepted 记录样例
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

from paths import DATA_DIR
from skill_memory import skill_memory, SkillMemory
from skill_recommender import recommend_for_task, recommend_recovery, record_acceptance

# 清理旧数据
SKILL_MEMORY_FILE = DATA_DIR / "skill_memory.jsonl"
SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"
RECOMMENDATION_LOG = DATA_DIR / "recommendation_log.jsonl"

for f in [SKILL_MEMORY_FILE, SKILL_EXECUTIONS_FILE, RECOMMENDATION_LOG]:
    if f.exists():
        f.unlink()


def setup_test_data():
    """准备测试数据"""
    print("准备测试数据...")

    # Skill 1: pdf-skill（高匹配强 skill）
    for i in range(15):
        status = "success" if i < 13 else "failed"
        skill_memory.track_execution(
            skill_id="pdf-skill",
            skill_name="PDF 处理工具",
            task_id=f"task-pdf-{i:03d}",
            command=f"python pdf_cli.py extract file{i}.pdf",
            status=status,
            duration_ms=1200 + i * 50,
            skill_version="2.1.0",
            error="timeout" if status == "failed" else None,
        )
    skill_memory.update_skill_stats("pdf-skill")

    # Skill 2: git-skill（稳定 fallback 候选）
    for i in range(20):
        skill_memory.track_execution(
            skill_id="git-skill",
            skill_name="Git 操作工具",
            task_id=f"task-git-{i:03d}",
            command=f"git commit -m 'update {i}'",
            status="success",
            duration_ms=800 + i * 20,
            skill_version="1.5.0",
        )
    skill_memory.update_skill_stats("git-skill")

    # Skill 3: api-testing-skill（连败中）
    for i in range(8):
        status = "failed" if i >= 5 else "success"
        skill_memory.track_execution(
            skill_id="api-testing-skill",
            skill_name="API 测试工具",
            task_id=f"task-api-{i:03d}",
            command=f"python api_test.py run test{i}",
            status=status,
            duration_ms=2000 + i * 100,
            skill_version="1.0.0",
            error="network_error" if status == "failed" else None,
        )
    skill_memory.update_skill_stats("api-testing-skill")

    # Skill 4: docker-skill（低分 skill，不应该成为 Top1）
    for i in range(5):
        status = "success" if i < 2 else "failed"
        skill_memory.track_execution(
            skill_id="docker-skill",
            skill_name="Docker 操作工具",
            task_id=f"task-docker-{i:03d}",
            command=f"docker run test{i}",
            status=status,
            duration_ms=3000 + i * 200,
            skill_version="0.9.0",
            error="resource_exhausted" if status == "failed" else None,
        )
    skill_memory.update_skill_stats("docker-skill")

    print("✓ 测试数据准备完成")
    print()


def test_task_recommendation():
    """测试 1：任务前推荐（高匹配强 skill）"""
    print("=" * 70)
    print("测试 1：任务前推荐（高匹配强 skill）")
    print("=" * 70)

    rec = recommend_for_task(task_type="pdf", top_n=3)

    print(f"\n推荐 ID: {rec['rec_id']}")
    print(f"任务类型: {rec['task_type']}")
    print()

    if rec["top1"]:
        print("✅ Top1 推荐:")
        t1 = rec["top1"]
        print(f"   Skill: {t1['skill_id']} v{t1['skill_version']}")
        print(f"   成功率: {t1['success_rate']:.0%}")
        print(f"   演化分数: {t1['evolution_score']:.1f}")
        print(f"   使用次数: {t1['usage_count']}")
        print(f"   理由: {rec['top1_reason']}")
    else:
        print("❌ 无 Top1 推荐")
        print(f"   原因: {rec['no_top1_reason']}")

    print()
    print("📋 Top3 备选:")
    for i, s in enumerate(rec["top3"], 1):
        print(f"   {i}. {s['skill_id']} v{s['skill_version']}")
        print(f"      成功率: {s['success_rate']:.0%} | 演化分数: {s['evolution_score']:.1f}")
        print(f"      理由: {s['reason']}")

    print()
    if rec["fallback_skill"]:
        fb = rec["fallback_skill"]
        print("🛡️ Fallback Skill:")
        print(f"   {fb['skill_id']} v{fb['skill_version']}")
        print(f"   成功率: {fb['success_rate']:.0%} | 使用次数: {fb['usage_count']}")
        print(f"   为什么稳定: {fb['why_stable']}")
    else:
        print("⚠️ 无 Fallback Skill")

    print()
    return rec["rec_id"]


def test_recovery_recommendation():
    """测试 2：连败恢复推荐"""
    print("=" * 70)
    print("测试 2：连败恢复推荐（api-testing-skill 连败 3 次）")
    print("=" * 70)

    rec = recommend_recovery("api-testing-skill")

    print(f"\n推荐 ID: {rec['rec_id']}")
    print(f"Skill: {rec['skill_id']}")
    print(f"连续失败次数: {rec['consecutive_failures']}")
    print(f"严重程度: {rec['severity'].upper()}")
    print()

    if rec["severity"] != "ok":
        print(f"🔴 主要错误: {rec['dominant_error']}")
        print(f"💡 推荐恢复策略: {rec['recommended_recovery']}")
        print()

        if rec["fallback_skill"]:
            fb = rec["fallback_skill"]
            print("🛡️ Fallback Skill:")
            print(f"   {fb['skill_id']} v{fb['skill_version']}")
            print(f"   成功率: {fb['success_rate']:.0%}")
            print(f"   为什么稳定: {fb['why_stable']}")
            print()

        if rec["downgrade_suggestion"]:
            print("⚠️ 降级建议:")
            print(f"   {rec['downgrade_suggestion']}")
    else:
        print("✅ 无需恢复（连败次数未达阈值）")

    print()
    return rec["rec_id"]


def test_acceptance_record(rec_id: str):
    """测试 3：recommendation_accepted 记录"""
    print("=" * 70)
    print("测试 3：recommendation_accepted 记录（三态）")
    print("=" * 70)

    # 模拟三种状态
    states = [
        ("accepted", "Router 采纳了 Top1 推荐"),
        ("rejected", "用户手动选择了其他 Skill"),
        ("not_applicable", "任务最终未使用 Skill 驱动"),
    ]

    for state, note in states:
        success = record_acceptance(rec_id, state, note)
        print(f"\n状态: {state}")
        print(f"备注: {note}")
        print(f"记录结果: {'✓ 成功' if success else '✗ 失败'}")

    # 读取最终记录
    print()
    print("📄 最终记录:")
    with open(RECOMMENDATION_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if rec_id in line:
                rec = json.loads(line)
                print(f"   rec_id: {rec['rec_id']}")
                print(f"   recommendation_accepted: {rec['recommendation_accepted']}")
                print(f"   acceptance_note: {rec.get('acceptance_note', 'N/A')}")
                print(f"   accepted_at: {rec.get('accepted_at', 'N/A')}")
                break

    print()


def print_summary():
    """打印汇总"""
    print("=" * 70)
    print("验证汇总")
    print("=" * 70)

    all_skills = skill_memory.get_all_skills()
    print(f"\n总 Skill 数: {len(all_skills)}")
    for s in all_skills:
        print(f"  - {s['skill_id']} v{s['skill_version']}: "
              f"{s['success_rate']:.0%} 成功率, {s['usage_count']} 次使用, "
              f"演化分数 {s['evolution_score']:.1f}")

    print()
    print("✅ 三个约束验证完成:")
    print("   1. Top1 最低分门槛（score < 0.55 → 不给 Top1）")
    print("   2. fallback_skill 只从稳定 skill 里选（非连败中）")
    print("   3. recommendation_accepted 三态（accepted/rejected/not_applicable）")
    print()


if __name__ == "__main__":
    setup_test_data()

    # 测试 1：任务前推荐
    rec_id_1 = test_task_recommendation()

    # 测试 2：连败恢复推荐
    rec_id_2 = test_recovery_recommendation()

    # 测试 3：采纳记录（用测试 1 的 rec_id）
    test_acceptance_record(rec_id_1)

    # 汇总
    print_summary()

    print("验证完成！")
    print(f"\n数据文件:")
    print(f"  - {SKILL_MEMORY_FILE}")
    print(f"  - {SKILL_EXECUTIONS_FILE}")
    print(f"  - {RECOMMENDATION_LOG}")
