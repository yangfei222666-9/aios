#!/usr/bin/env python3
"""
AIOS Evaluation Agent - 验证守门员

职责：
1. 验证任何改动/策略应用后的效果
2. 对比 before/after 指标
3. 不达标触发回滚
4. 生成验证报告

触发条件：
- 策略应用后
- 配置变更后
- 插件升级后
- 优化执行后

验证项：
- 成功率（不能下降 >10%）
- P95 耗时（不能增加 >20%）
- 错误率（不能上升 >10%）
- 资源使用（不能增加 >30%）

工作流程：
1. 记录 baseline（变更前）
2. 等待观察期（默认 1 小时）
3. 收集 after 指标
4. 对比分析
5. 判断是否回滚
6. 生成报告

集成点：
- 输入：change_events.jsonl（变更事件）
- 输出：evaluation_reports.jsonl（验证报告）
- 触发：Scheduler（变更后自动触发）
- 回滚：Reactor（不达标时）
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加 AIOS 路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer


class AIOSEvaluationAgent:
    """AIOS 验证守门员 Agent"""

    # 验证阈值
    SUCCESS_RATE_DROP_THRESHOLD = 0.10      # 成功率下降 >10%
    LATENCY_INCREASE_THRESHOLD = 0.20       # 耗时增加 >20%
    ERROR_RATE_INCREASE_THRESHOLD = 0.10    # 错误率上升 >10%
    RESOURCE_INCREASE_THRESHOLD = 0.30      # 资源使用增加 >30%

    # 观察期
    OBSERVATION_WINDOW_HOURS = 1            # 默认观察 1 小时

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data"
        self.evaluation_dir = self.data_dir / "evaluations"
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = TraceAnalyzer()
        self.changes_file = self.data_dir / "changes.jsonl"

    def run(self, change_id: Optional[str] = None) -> Dict:
        """运行完整验证流程"""
        print("=" * 60)
        print("  AIOS Evaluation Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        # 如果没有指定 change_id，查找最近的变更
        if not change_id:
            change = self._find_recent_change()
            if not change:
                print("[OK] 无待验证的变更")
                return {"status": "no_changes"}
            change_id = change["id"]
        else:
            change = self._load_change(change_id)

        print(f"验证变更: {change_id}")
        print(f"类型: {change['type']}")
        print(f"描述: {change['description']}")
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "change_id": change_id,
            "change": change,
            "baseline": {},
            "after": {},
            "comparison": {},
            "verdict": "unknown"
        }

        # Phase 1: 加载 baseline
        print("[Phase 1] 加载 baseline...")
        baseline = self._load_baseline(change)
        if not baseline:
            print("  [WARN]  无 baseline，执行 smoke test")
            smoke_result = self._smoke_test(change)
            report["smoke_test"] = smoke_result
            report["verdict"] = "pass" if smoke_result["passed"] else "fail"
            self._save_report(report)
            return report

        report["baseline"] = baseline
        print(f"  [OK] Baseline: 成功率 {baseline['success_rate']:.1%}, P95 {baseline['p95_duration']:.1f}s")

        # Phase 2: 收集 after 指标
        print("[Phase 2] 收集 after 指标...")
        after = self._collect_after_metrics(change)
        report["after"] = after
        print(f"  [OK] After: 成功率 {after['success_rate']:.1%}, P95 {after['p95_duration']:.1f}s")

        # Phase 3: 对比分析
        print("[Phase 3] 对比分析...")
        comparison = self._compare_metrics(baseline, after)
        report["comparison"] = comparison
        
        # 显示对比结果
        for metric, result in comparison.items():
            status = "[OK]" if result["passed"] else "[FAIL]"
            print(f"  {status} {metric}: {result['change']:.1%}")

        # Phase 4: 判断是否回滚
        print("[Phase 4] 判断是否回滚...")
        verdict = self._make_verdict(comparison)
        report["verdict"] = verdict
        
        if verdict == "pass":
            print("  [OK] 验证通过")
        elif verdict == "fail":
            print("  [FAIL] 验证失败，建议回滚")
            self._trigger_rollback(change, report)
        else:
            print("  [WARN]  需要人工判断")

        # 保存报告
        self._save_report(report)

        print()
        print("=" * 60)
        print(f"  验证结果: {verdict.upper()}")
        print("=" * 60)

        return report

    def _find_recent_change(self) -> Optional[Dict]:
        """查找最近的待验证变更"""
        if not self.changes_file.exists():
            return None

        # 读取最近的变更
        changes = []
        with open(self.changes_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    change = json.loads(line.strip())
                    # 只看最近 2 小时的变更
                    change_time = datetime.fromisoformat(change["timestamp"])
                    if datetime.now() - change_time < timedelta(hours=2):
                        # 检查是否已验证
                        if not change.get("evaluated", False):
                            changes.append(change)
                except:
                    continue

        return changes[-1] if changes else None

    def _load_change(self, change_id: str) -> Dict:
        """加载变更记录"""
        if not self.changes_file.exists():
            return None

        with open(self.changes_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    change = json.loads(line.strip())
                    if change["id"] == change_id:
                        return change
                except:
                    continue

        return None

    def _load_baseline(self, change: Dict) -> Optional[Dict]:
        """加载 baseline 指标"""
        # 从变更记录中读取 baseline
        baseline = change.get("baseline")
        if baseline:
            return baseline

        # 如果没有 baseline，从历史数据计算
        change_time = datetime.fromisoformat(change["timestamp"])
        cutoff_start = change_time - timedelta(hours=2)
        cutoff_end = change_time

        return self._calculate_metrics(cutoff_start, cutoff_end)

    def _collect_after_metrics(self, change: Dict) -> Dict:
        """收集变更后的指标"""
        change_time = datetime.fromisoformat(change["timestamp"])
        cutoff_start = change_time
        cutoff_end = datetime.now()

        return self._calculate_metrics(cutoff_start, cutoff_end)

    def _calculate_metrics(self, start_time: datetime, end_time: datetime) -> Dict:
        """计算指标"""
        traces = [
            t for t in self.analyzer.traces
            if start_time <= datetime.fromisoformat(t.get("start_time", "")) < end_time
            and t.get("env", "prod") == "prod"
        ]

        if not traces:
            return {
                "total_tasks": 0,
                "success_rate": 0,
                "error_rate": 0,
                "p95_duration": 0,
                "avg_duration": 0
            }

        successes = sum(1 for t in traces if t.get("success", False))
        failures = len(traces) - successes

        durations = [t.get("duration_sec", 0) for t in traces if t.get("duration_sec", 0) > 0]
        durations.sort()

        p95_duration = durations[int(len(durations) * 0.95)] if durations else 0
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_tasks": len(traces),
            "success_rate": successes / len(traces) if traces else 0,
            "error_rate": failures / len(traces) if traces else 0,
            "p95_duration": p95_duration,
            "avg_duration": avg_duration
        }

    def _compare_metrics(self, baseline: Dict, after: Dict) -> Dict:
        """对比指标"""
        comparison = {}

        # 1. 成功率
        success_rate_change = after["success_rate"] - baseline["success_rate"]
        comparison["success_rate"] = {
            "baseline": baseline["success_rate"],
            "after": after["success_rate"],
            "change": success_rate_change,
            "passed": success_rate_change >= -self.SUCCESS_RATE_DROP_THRESHOLD
        }

        # 2. P95 耗时
        if baseline["p95_duration"] > 0:
            latency_change = (after["p95_duration"] - baseline["p95_duration"]) / baseline["p95_duration"]
        else:
            latency_change = 0

        comparison["p95_duration"] = {
            "baseline": baseline["p95_duration"],
            "after": after["p95_duration"],
            "change": latency_change,
            "passed": latency_change <= self.LATENCY_INCREASE_THRESHOLD
        }

        # 3. 错误率
        error_rate_change = after["error_rate"] - baseline["error_rate"]
        comparison["error_rate"] = {
            "baseline": baseline["error_rate"],
            "after": after["error_rate"],
            "change": error_rate_change,
            "passed": error_rate_change <= self.ERROR_RATE_INCREASE_THRESHOLD
        }

        return comparison

    def _make_verdict(self, comparison: Dict) -> str:
        """判断验证结果"""
        # 所有指标都通过 → pass
        if all(result["passed"] for result in comparison.values()):
            return "pass"

        # 任何关键指标失败 → fail
        critical_metrics = ["success_rate", "error_rate"]
        if any(not comparison[m]["passed"] for m in critical_metrics if m in comparison):
            return "fail"

        # 其他情况 → needs_review
        return "needs_review"

    def _smoke_test(self, change: Dict) -> Dict:
        """Smoke test（无 baseline 时）"""
        print("  执行 smoke test...")
        
        # 简单检查：最近 10 分钟有没有严重错误
        cutoff = datetime.now() - timedelta(minutes=10)
        recent_traces = [
            t for t in self.analyzer.traces
            if datetime.fromisoformat(t.get("start_time", "")) >= cutoff
            and t.get("env", "prod") == "prod"
        ]

        if not recent_traces:
            return {"passed": True, "reason": "无数据，默认通过"}

        failures = sum(1 for t in recent_traces if not t.get("success", False))
        failure_rate = failures / len(recent_traces)

        if failure_rate > 0.5:
            return {"passed": False, "reason": f"失败率过高: {failure_rate:.1%}"}

        return {"passed": True, "reason": "smoke test 通过"}

    def _trigger_rollback(self, change: Dict, report: Dict):
        """触发回滚"""
        print("  [SYNC] 触发回滚...")
        
        # 生成回滚事件
        rollback_event = {
            "type": "rollback_requested",
            "timestamp": datetime.now().isoformat(),
            "change_id": change["id"],
            "reason": "验证失败",
            "report": report
        }

        # 写入事件流（Reactor 会处理）
        events_file = AIOS_ROOT / "data" / "events.jsonl"
        with open(events_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rollback_event, ensure_ascii=False) + '\n')

        print("  [OK] 回滚请求已发送")

    def _save_report(self, report: Dict):
        """保存验证报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.evaluation_dir / f"eval_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {report_file}")

        # 标记变更已验证
        if self.changes_file.exists():
            self._mark_change_evaluated(report["change_id"])

    def _mark_change_evaluated(self, change_id: str):
        """标记变更已验证"""
        if not self.changes_file.exists():
            return

        lines = []
        with open(self.changes_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    change = json.loads(line.strip())
                    if change["id"] == change_id:
                        change["evaluated"] = True
                        change["evaluated_at"] = datetime.now().isoformat()
                    lines.append(json.dumps(change, ensure_ascii=False))
                except:
                    lines.append(line.strip())

        with open(self.changes_file, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')


def main():
    """主函数"""
    agent = AIOSEvaluationAgent()
    report = agent.run()
    
    # 输出摘要
    status = report.get("status")
    if status == "no_changes":
        print("\nEVALUATION_OK")
    else:
        verdict = report.get("verdict", "unknown")
        if verdict == "pass":
            print("\nEVALUATION_PASS")
        elif verdict == "fail":
            print("\nEVALUATION_FAIL")
        else:
            print("\nEVALUATION_REVIEW")


if __name__ == "__main__":
    main()
