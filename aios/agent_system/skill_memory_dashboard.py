"""
Skill Memory Dashboard - 可视化展示所有技能的统计信息

生成 Markdown 报告，包含：
1. 技能总览（总数、平均成功率、平均演化分数）
2. Top 10 技能（按演化分数排序）
3. 失败率最高的技能（需要优化）
4. 最常用的技能（按使用次数排序）
5. 失败教训汇总
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from skill_memory import skill_memory
from paths import DATA_DIR

DASHBOARD_OUTPUT = DATA_DIR / "skill_memory_dashboard.md"


def generate_dashboard():
    """生成 Skill Memory Dashboard"""
    all_skills = skill_memory.get_all_skills()
    
    if not all_skills:
        print("[DASHBOARD] No skills in memory")
        return
    
    # 计算总览统计
    total_skills = len(all_skills)
    total_usage = sum(s.get("usage_count", 0) for s in all_skills)
    avg_success_rate = sum(s.get("success_rate", 0) for s in all_skills) / total_skills
    avg_evolution_score = sum(s.get("evolution_score", 0) for s in all_skills) / total_skills
    
    # 按演化分数排序
    sorted_by_evolution = sorted(all_skills, key=lambda s: s.get("evolution_score", 0), reverse=True)
    
    # 按失败率排序（需要优化）
    sorted_by_failure = sorted(
        [s for s in all_skills if s.get("failure_count", 0) > 0],
        key=lambda s: s.get("failure_count", 0) / s.get("usage_count", 1),
        reverse=True
    )
    
    # 按使用次数排序
    sorted_by_usage = sorted(all_skills, key=lambda s: s.get("usage_count", 0), reverse=True)
    
    # 汇总失败教训
    all_lessons = defaultdict(lambda: {"count": 0, "skills": set()})
    for skill in all_skills:
        for lesson in skill.get("failure_lessons", []):
            error_type = lesson["error_type"]
            all_lessons[error_type]["count"] += lesson["count"]
            all_lessons[error_type]["skills"].add(skill["skill_id"])
    
    # 生成 Markdown 报告
    report = []
    report.append("# Skill Memory Dashboard")
    report.append(f"\n**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n---\n")
    
    # 1. 技能总览
    report.append("## 📊 技能总览")
    report.append("")
    report.append(f"- **技能总数：** {total_skills}")
    report.append(f"- **总使用次数：** {total_usage}")
    report.append(f"- **平均成功率：** {avg_success_rate:.1%}")
    report.append(f"- **平均演化分数：** {avg_evolution_score:.1f}/100")
    report.append("")
    
    # 2. Top 10 技能
    report.append("## 🏆 Top 10 技能（按演化分数）")
    report.append("")
    report.append("| 排名 | 技能 ID | 演化分数 | 使用次数 | 成功率 | 平均耗时 |")
    report.append("|------|---------|----------|----------|--------|----------|")
    
    for i, skill in enumerate(sorted_by_evolution[:10], 1):
        report.append(
            f"| {i} | {skill['skill_id']} | {skill['evolution_score']:.1f}/100 | "
            f"{skill['usage_count']} | {skill['success_rate']:.1%} | "
            f"{skill['avg_execution_time_ms']:.0f}ms |"
        )
    
    report.append("")
    
    # 3. 失败率最高的技能
    if sorted_by_failure:
        report.append("## ⚠️ 需要优化的技能（按失败率）")
        report.append("")
        report.append("| 技能 ID | 失败率 | 失败次数 | 总使用次数 | 演化分数 |")
        report.append("|---------|--------|----------|------------|----------|")
        
        for skill in sorted_by_failure[:5]:
            failure_rate = skill["failure_count"] / skill["usage_count"]
            report.append(
                f"| {skill['skill_id']} | {failure_rate:.1%} | "
                f"{skill['failure_count']} | {skill['usage_count']} | "
                f"{skill['evolution_score']:.1f}/100 |"
            )
        
        report.append("")
    
    # 4. 最常用的技能
    report.append("## 🔥 最常用的技能（按使用次数）")
    report.append("")
    report.append("| 排名 | 技能 ID | 使用次数 | 成功率 | 演化分数 |")
    report.append("|------|---------|----------|--------|----------|")
    
    for i, skill in enumerate(sorted_by_usage[:10], 1):
        report.append(
            f"| {i} | {skill['skill_id']} | {skill['usage_count']} | "
            f"{skill['success_rate']:.1%} | {skill['evolution_score']:.1f}/100 |"
        )
    
    report.append("")
    
    # 5. 失败教训汇总
    if all_lessons:
        report.append("## 📚 失败教训汇总")
        report.append("")
        report.append("| 错误类型 | 总次数 | 涉及技能数 | 恢复策略 |")
        report.append("|----------|--------|------------|----------|")
        
        sorted_lessons = sorted(all_lessons.items(), key=lambda x: x[1]["count"], reverse=True)
        for error_type, data in sorted_lessons[:10]:
            # 获取恢复策略（从第一个技能）
            recovery_strategy = "unknown"
            for skill in all_skills:
                for lesson in skill.get("failure_lessons", []):
                    if lesson["error_type"] == error_type:
                        recovery_strategy = lesson["recovery_strategy"]
                        break
            
            report.append(
                f"| {error_type} | {data['count']} | {len(data['skills'])} | "
                f"{recovery_strategy} |"
            )
        
        report.append("")
    
    # 6. 详细技能列表
    report.append("## 📋 详细技能列表")
    report.append("")
    
    for skill in sorted_by_evolution:
        report.append(f"### {skill['skill_id']}")
        report.append("")
        report.append(f"- **演化分数：** {skill['evolution_score']:.1f}/100")
        report.append(f"- **使用次数：** {skill['usage_count']}")
        report.append(f"- **成功率：** {skill['success_rate']:.1%}")
        report.append(f"- **平均耗时：** {skill['avg_execution_time_ms']:.0f}ms")
        report.append(f"- **最后使用：** {skill['last_used']}")
        
        if skill.get("common_patterns"):
            report.append("")
            report.append("**常见模式：**")
            for pattern in skill["common_patterns"][:5]:
                report.append(
                    f"- `{pattern['pattern']}`: {pattern['usage_count']} 次使用, "
                    f"{pattern['success_rate']:.1%} 成功率"
                )
        
        if skill.get("failure_lessons"):
            report.append("")
            report.append("**失败教训：**")
            for lesson in skill["failure_lessons"][:5]:
                report.append(
                    f"- `{lesson['error_type']}`: {lesson['count']} 次 → "
                    f"{lesson['recovery_strategy']}"
                )
        
        report.append("")
    
    # 写入文件
    report_text = "\n".join(report)
    DASHBOARD_OUTPUT.write_text(report_text, encoding="utf-8")
    
    print(f"[DASHBOARD] Report generated: {DASHBOARD_OUTPUT}")
    print(f"[DASHBOARD] Total skills: {total_skills}")
    print(f"[DASHBOARD] Avg success rate: {avg_success_rate:.1%}")
    print(f"[DASHBOARD] Avg evolution score: {avg_evolution_score:.1f}/100")


if __name__ == "__main__":
    generate_dashboard()
