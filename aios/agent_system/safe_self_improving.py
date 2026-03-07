"""
Self-Improving Agent 验证版本
支持 dry-run、风险控制、冷却期
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from self_improving_agent import SelfImprovingAgent
from safety_valve import SafetyValve
from validation_report import ValidationReport


class SafeSelfImprovingAgent(SelfImprovingAgent):
    """带安全阀的自我改进 Agent"""

    def __init__(self, dry_run: bool = False, allow_risk_level: str = "low"):
        super().__init__()
        self.dry_run = dry_run
        self.allow_risk_level = allow_risk_level
        self.safety_valve = SafetyValve()

    def run_improvement_cycle(self, days: int = 7, min_occurrences: int = 3) -> dict:
        """运行改进循环（带安全检查）"""
        print("=== Safe Self-Improving Agent ===\n")
        print(f"模式: {'DRY-RUN（只分析不应用）' if self.dry_run else '自动应用'}")
        print(f"风险等级: {self.allow_risk_level}")
        print(f"分析周期: {days} 天")
        print(f"最少出现: {min_occurrences} 次\n")

        # 检查熔断器
        if self.safety_valve._is_circuit_broken():
            print("[WARN] 熔断器已触发，24h 内禁止自动改进")
            return {"status": "circuit_broken"}

        # 运行基础分析
        failure_report = self.failure_analyzer.analyze(days=days, min_occurrences=min_occurrences)

        if not failure_report["improvements"]:
            print("✓ 未发现需要改进的模式，系统运行正常")
            return {"status": "healthy"}

        improvements = failure_report["improvements"]
        print(f"发现 {len(improvements)} 条改进建议\n")
        applied = []
        blocked = []

        for improvement in improvements:
            improvement_type = improvement.get("improvement_type")
            target = improvement.get("agent_id") or improvement.get("pattern_signature", "unknown")

            # 安全检查
            allowed, reason = self.safety_valve.is_allowed(
                improvement_type,
                target,
                self.allow_risk_level
            )

            if not allowed:
                print(f"\n🚫 阻止应用: {improvement['description']}")
                print(f"   原因: {reason}")
                blocked.append({
                    "improvement": improvement,
                    "reason": reason
                })
                continue

            if self.dry_run:
                print(f"\n[DRY-RUN] 将应用: {improvement['description']}")
                print(f"   操作: {improvement['action']['change']}")
                applied.append({
                    "improvement": improvement,
                    "dry_run": True,
                    "success": None
                })
            else:
                print(f"\n✓ 应用改进: {improvement['description']}")
                result = self.auto_fixer._apply_fix(improvement)
                applied.append(result)

                # 记录到安全阀
                self.safety_valve.record_application(
                    improvement_type,
                    target,
                    result.get("success", False)
                )

        # 更新报告
        report = {
            "status": "improved" if applied else "no_change",
            "applied": applied,
            "blocked": blocked,
            "summary": {
                "total_improvements": len(improvements),
                "applied": len(applied),
                "blocked": len(blocked),
                "success": sum(1 for a in applied if a.get("success")),
            }
        }

        return report


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Safe Self-Improving Agent")
    parser.add_argument("--dry-run", action="store_true", help="只分析不应用")
    parser.add_argument("--days", type=int, default=7, help="分析最近多少天")
    parser.add_argument("--min", type=int, default=3, help="最少出现次数")
    parser.add_argument("--risk", choices=["low", "medium", "high"], default="low", help="允许的风险等级")
    parser.add_argument("--report", type=int, help="生成 Day N 验证报告")

    args = parser.parse_args()

    # 生成验证报告
    if args.report:
        reporter = ValidationReport()
        report = reporter.generate_daily_report(day=args.report)
        reporter.print_report(report)
        return

    # 运行改进循环
    agent = SafeSelfImprovingAgent(
        dry_run=args.dry_run,
        allow_risk_level=args.risk
    )

    report = agent.run_improvement_cycle(
        days=args.days,
        min_occurrences=args.min
    )

    # 打印摘要
    if report.get("status") == "circuit_broken":
        print("\n[WARN] 熔断器已触发，请检查系统状态")
        return

    if report.get("status") == "healthy":
        print("\n✓ 系统运行正常，无需改进")
        return

    summary = report.get("summary", {})
    print(f"\n=== 摘要 ===")
    print(f"总改进建议: {summary.get('total_improvements', 0)}")
    print(f"已应用: {summary.get('applied', 0)}")
    print(f"被阻止: {summary.get('blocked', 0)}")
    print(f"成功: {summary.get('success', 0)}")

    if args.dry_run:
        print("\n[IDEA] 这是 dry-run 模式，没有实际应用任何改进")
        print("   移除 --dry-run 参数以实际应用")


if __name__ == "__main__":
    main()
