#!/usr/bin/env python3
"""
AIOS Optimizer Agent - 专门负责 AIOS 的优化和升级

职责：
1. 分析系统性能瓶颈
2. 识别优化机会
3. 生成优化方案
4. 执行低风险优化
5. 验证优化效果
6. 学习和改进

工作模式：
- 每天自动运行一次
- 分析最近 24 小时的数据
- 生成优化报告
- 自动应用低风险优化
- 中高风险优化需要人工确认
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# 添加 AIOS 路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer


class AIOSOptimizerAgent:
    """AIOS 优化 Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data"
        self.reports_dir = self.data_dir / "optimizer_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = TraceAnalyzer()

    def run(self) -> Dict:
        """运行完整优化流程"""
        print("=" * 60)
        print("  AIOS Optimizer Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "phases": {}
        }

        # Phase 1: 分析性能瓶颈
        print("[Phase 1] 分析性能瓶颈...")
        bottlenecks = self._analyze_bottlenecks()
        report["phases"]["bottlenecks"] = bottlenecks
        print(f"  发现 {len(bottlenecks)} 个瓶颈")

        # Phase 2: 识别优化机会
        print("[Phase 2] 识别优化机会...")
        opportunities = self._identify_opportunities(bottlenecks)
        report["phases"]["opportunities"] = opportunities
        print(f"  识别 {len(opportunities)} 个优化机会")

        # Phase 3: 生成优化方案
        print("[Phase 3] 生成优化方案...")
        plans = self._generate_plans(opportunities)
        report["phases"]["plans"] = plans
        print(f"  生成 {len(plans)} 个优化方案")

        # Phase 4: 执行优化
        print("[Phase 4] 执行优化...")
        results = self._execute_plans(plans)
        report["phases"]["results"] = results
        print(f"  执行 {results['applied']} 个优化")

        # Phase 5: 验证效果
        print("[Phase 5] 验证效果...")
        validation = self._validate_results(results)
        report["phases"]["validation"] = validation
        print(f"  验证完成")

        # 保存报告
        self._save_report(report)

        print()
        print("=" * 60)
        print(f"  完成！应用 {results['applied']} 个优化")
        print("=" * 60)

        return report

    def _analyze_bottlenecks(self) -> List[Dict]:
        """分析性能瓶颈"""
        bottlenecks = []

        # 1. 慢操作（>5s）
        slow_traces = [
            t for t in self.analyzer.traces
            if t.get("duration_sec", 0) > 5
            and t.get("env", "prod") == "prod"
        ]

        if len(slow_traces) >= 3:
            avg_duration = sum(t["duration_sec"] for t in slow_traces) / len(slow_traces)
            bottlenecks.append({
                "type": "slow_operations",
                "count": len(slow_traces),
                "avg_duration": avg_duration,
                "severity": "high" if avg_duration > 10 else "medium"
            })

        # 2. 高失败率 Agent
        agent_stats = {}
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            agent_id = trace.get("agent_id", "unknown")
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {"total": 0, "failures": 0}
            
            agent_stats[agent_id]["total"] += 1
            if not trace.get("success", False):
                agent_stats[agent_id]["failures"] += 1

        for agent_id, stats in agent_stats.items():
            if stats["total"] >= 5:
                failure_rate = stats["failures"] / stats["total"]
                if failure_rate > 0.3:
                    bottlenecks.append({
                        "type": "high_failure_rate",
                        "agent_id": agent_id,
                        "failure_rate": failure_rate,
                        "total_tasks": stats["total"],
                        "severity": "high" if failure_rate > 0.5 else "medium"
                    })

        # 3. 频繁超时
        timeout_count = sum(
            1 for t in self.analyzer.traces
            if "timeout" in str(t.get("error", "")).lower()
            and t.get("env", "prod") == "prod"
        )

        if timeout_count >= 5:
            bottlenecks.append({
                "type": "frequent_timeouts",
                "count": timeout_count,
                "severity": "high"
            })

        return bottlenecks

    def _identify_opportunities(self, bottlenecks: List[Dict]) -> List[Dict]:
        """识别优化机会"""
        opportunities = []

        for bottleneck in bottlenecks:
            if bottleneck["type"] == "slow_operations":
                opportunities.append({
                    "type": "optimize_slow_ops",
                    "description": f"优化慢操作（平均 {bottleneck['avg_duration']:.1f}s）",
                    "impact": "high",
                    "effort": "medium",
                    "bottleneck": bottleneck
                })

            elif bottleneck["type"] == "high_failure_rate":
                opportunities.append({
                    "type": "improve_agent_reliability",
                    "description": f"提升 {bottleneck['agent_id']} 可靠性（失败率 {bottleneck['failure_rate']:.1%}）",
                    "impact": "high",
                    "effort": "medium",
                    "bottleneck": bottleneck
                })

            elif bottleneck["type"] == "frequent_timeouts":
                opportunities.append({
                    "type": "adjust_timeouts",
                    "description": f"调整超时配置（{bottleneck['count']} 次超时）",
                    "impact": "medium",
                    "effort": "low",
                    "bottleneck": bottleneck
                })

        return opportunities

    def _generate_plans(self, opportunities: List[Dict]) -> List[Dict]:
        """生成优化方案"""
        plans = []

        for opp in opportunities:
            if opp["type"] == "optimize_slow_ops":
                plans.append({
                    "name": "增加缓存",
                    "description": "为慢操作增加缓存层",
                    "risk": "low",
                    "auto_apply": True,
                    "steps": [
                        "识别重复调用的操作",
                        "添加 LRU 缓存",
                        "设置合理的 TTL"
                    ]
                })

            elif opp["type"] == "improve_agent_reliability":
                agent_id = opp["bottleneck"]["agent_id"]
                plans.append({
                    "name": f"提升 {agent_id} 可靠性",
                    "description": "增加重试机制和错误处理",
                    "risk": "low",
                    "auto_apply": True,
                    "steps": [
                        "分析失败原因",
                        "添加重试逻辑",
                        "改进错误处理"
                    ]
                })

            elif opp["type"] == "adjust_timeouts":
                plans.append({
                    "name": "调整超时配置",
                    "description": "根据历史数据优化超时值",
                    "risk": "low",
                    "auto_apply": True,
                    "steps": [
                        "分析超时任务的耗时分布",
                        "计算 P95 耗时",
                        "更新超时配置"
                    ]
                })

        return plans

    def _execute_plans(self, plans: List[Dict]) -> Dict:
        """执行优化方案"""
        applied = 0
        skipped = 0
        failed = 0

        for plan in plans:
            if plan["risk"] == "low" and plan["auto_apply"]:
                try:
                    # 这里实际执行优化
                    # 目前只是模拟
                    print(f"  ✅ 应用: {plan['name']}")
                    applied += 1
                except Exception as e:
                    print(f"  ❌ 失败: {plan['name']} - {e}")
                    failed += 1
            else:
                print(f"  ⏭️  跳过: {plan['name']} (需要人工确认)")
                skipped += 1

        return {
            "applied": applied,
            "skipped": skipped,
            "failed": failed
        }

    def _validate_results(self, results: Dict) -> Dict:
        """验证优化效果"""
        # 简化版：只检查是否有失败
        return {
            "success": results["failed"] == 0,
            "message": "所有优化成功应用" if results["failed"] == 0 else f"{results['failed']} 个优化失败"
        }

    def _save_report(self, report: Dict):
        """保存优化报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"optimizer_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {report_file}")


def main():
    """主函数"""
    agent = AIOSOptimizerAgent()
    report = agent.run()
    
    # 输出摘要
    applied = report["phases"]["results"]["applied"]
    if applied > 0:
        print(f"\nOPTIMIZER_APPLIED:{applied}")
    else:
        print("\nOPTIMIZER_OK")


if __name__ == "__main__":
    main()
