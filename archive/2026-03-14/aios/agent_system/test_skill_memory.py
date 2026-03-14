"""
Skill Memory 完整流程测试

测试场景：
1. 模拟 3 次 Skill 执行（2 成功 + 1 失败）
2. 聚合统计
3. 验证记忆条目
4. 验证失败教训
5. 验证演化分数
"""

import json
import time
from pathlib import Path
from datetime import datetime

# 导入模块
from skill_memory import skill_memory
from skill_memory_aggregator import aggregate_all_skills, show_top_skills
from paths import DATA_DIR

# 清理旧数据（测试用）
SKILL_MEMORY_FILE = DATA_DIR / "skill_memory.jsonl"
SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"

def clean_test_data():
    """清理测试数据"""
    if SKILL_MEMORY_FILE.exists():
        SKILL_MEMORY_FILE.unlink()
    if SKILL_EXECUTIONS_FILE.exists():
        SKILL_EXECUTIONS_FILE.unlink()
    print("✓ 清理旧数据")


def test_skill_memory():
    """完整流程测试"""
    print("=" * 80)
    print("Skill Memory 完整流程测试")
    print("=" * 80)
    
    # 1. 清理旧数据
    clean_test_data()
    
    # 2. 模拟 3 次 PDF Skill 执行
    print("\n[1] 模拟 3 次 PDF Skill 执行...")
    
    # 执行 1: 成功
    exec_id_1 = skill_memory.track_execution(
        skill_id="pdf-skill",
        skill_name="PDF 处理工具",
        task_id="task-001",
        command="python pdf_cli.py extract input.pdf",
        status="success",
        duration_ms=1200,
        input_params={"file": "input.pdf", "action": "extract"},
        output_summary="Extracted 15 pages, 8500 words",
        context={"agent": "document-agent", "user_intent": "提取 PDF 文本"}
    )
    print(f"  ✓ 执行 1 (成功): {exec_id_1}")
    time.sleep(0.1)
    
    # 执行 2: 成功
    exec_id_2 = skill_memory.track_execution(
        skill_id="pdf-skill",
        skill_name="PDF 处理工具",
        task_id="task-002",
        command="python pdf_cli.py merge file1.pdf file2.pdf",
        status="success",
        duration_ms=2300,
        input_params={"files": ["file1.pdf", "file2.pdf"], "action": "merge"},
        output_summary="Merged 2 PDFs into output.pdf",
        context={"agent": "document-agent", "user_intent": "合并 PDF"}
    )
    print(f"  ✓ 执行 2 (成功): {exec_id_2}")
    time.sleep(0.1)
    
    # 执行 3: 失败（编码错误）
    exec_id_3 = skill_memory.track_execution(
        skill_id="pdf-skill",
        skill_name="PDF 处理工具",
        task_id="task-003",
        command="python pdf_cli.py extract corrupted.pdf",
        status="failed",
        duration_ms=500,
        input_params={"file": "corrupted.pdf", "action": "extract"},
        error="UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff",
        context={"agent": "document-agent", "user_intent": "提取损坏的 PDF"}
    )
    print(f"  ✓ 执行 3 (失败): {exec_id_3}")
    
    # 3. 聚合统计
    print("\n[2] 聚合统计...")
    memory = skill_memory.update_skill_stats("pdf-skill")
    
    print(f"  ✓ 技能 ID: {memory['skill_id']}")
    print(f"  ✓ 使用次数: {memory['usage_count']}")
    print(f"  ✓ 成功次数: {memory['success_count']}")
    print(f"  ✓ 失败次数: {memory['failure_count']}")
    print(f"  ✓ 成功率: {memory['success_rate']:.1%}")
    print(f"  ✓ 平均耗时: {memory['avg_execution_time_ms']:.0f}ms")
    print(f"  ✓ 演化分数: {memory['evolution_score']:.1f}/100")
    
    # 4. 验证常见模式
    print("\n[3] 验证常见模式...")
    if memory.get("common_patterns"):
        for pattern in memory["common_patterns"]:
            print(f"  ✓ {pattern['pattern']}: {pattern['usage_count']} 次使用, {pattern['success_rate']:.1%} 成功率")
    else:
        print("  ✗ 没有识别到常见模式")
    
    # 5. 验证失败教训
    print("\n[4] 验证失败教训...")
    if memory.get("failure_lessons"):
        for lesson in memory["failure_lessons"]:
            print(f"  ✓ {lesson['error_type']}: {lesson['count']} 次")
            print(f"    恢复策略: {lesson['recovery_strategy']}")
    else:
        print("  ✗ 没有失败教训")
    
    # 6. 验证演化分数计算
    print("\n[5] 验证演化分数计算...")
    expected_success_component = (2/3) * 70  # 66.7% 成功率 * 70
    expected_usage_component = (3/100) * 30  # 3 次使用 / 100 * 30
    expected_score = expected_success_component + expected_usage_component
    print(f"  预期分数: {expected_score:.1f}/100")
    print(f"  实际分数: {memory['evolution_score']:.1f}/100")
    
    if abs(memory['evolution_score'] - expected_score) < 0.1:
        print("  ✓ 演化分数计算正确")
    else:
        print("  ✗ 演化分数计算错误")
    
    # 7. 测试聚合器
    print("\n[6] 测试聚合器...")
    aggregate_all_skills()
    
    # 8. 显示 Top 技能
    print("\n[7] 显示 Top 技能...")
    show_top_skills(top_n=3)
    
    # 9. 测试获取记忆
    print("\n[8] 测试获取记忆...")
    retrieved = skill_memory.get_skill_memory("pdf-skill")
    if retrieved:
        print(f"  ✓ 成功获取记忆: {retrieved['skill_id']}")
    else:
        print("  ✗ 获取记忆失败")
    
    # 10. 测试获取所有技能
    print("\n[9] 测试获取所有技能...")
    all_skills = skill_memory.get_all_skills()
    print(f"  ✓ 共有 {len(all_skills)} 个技能")
    
    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    test_skill_memory()
