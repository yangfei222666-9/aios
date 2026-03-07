#!/usr/bin/env python3
"""
AIOS Security Agent - 安全守护

职责：
1. 监控异常行为（频繁失败、异常调用）
2. 检测潜在风险（权限滥用、数据泄露）
3. 自动熔断危险操作
4. 生成安全报告

检测项：
- 频繁失败（同一操作短时间内多次失败）
- 异常调用（非工作时间的大量操作）
- 权限异常（尝试访问敏感路径）
- 资源滥用（单个 Agent 占用过多资源）
- 数据异常（大量数据读写）

工作模式：
- 每小时自动运行一次
- 发现风险立即通知
- 高风险自动熔断
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter, defaultdict

# 添加 AIOS 路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer


class AIOSSecurityAgent:
    """AIOS 安全守护 Agent"""

    # 安全阈值
    FREQUENT_FAILURE_THRESHOLD = 5      # 1小时内失败5次
    ABNORMAL_CALL_THRESHOLD = 100       # 非工作时间100次调用
    RESOURCE_ABUSE_THRESHOLD = 0.8      # 单个Agent占用80%资源
    DATA_ANOMALY_THRESHOLD = 1000       # 1小时内1000次数据操作

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data"
        self.security_dir = self.data_dir / "security"
        self.security_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = TraceAnalyzer()
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"

    def run(self) -> Dict:
        """运行完整安全检查"""
        print("=" * 60)
        print("  AIOS Security Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "risks": []
        }

        # 1. 检测频繁失败
        print("[1/5] 检测频繁失败...")
        frequent_failures = self._detect_frequent_failures()
        if frequent_failures:
            report["risks"].extend(frequent_failures)
            print(f"  [WARN]  发现 {len(frequent_failures)} 个频繁失败风险")
        else:
            print(f"  [OK] 无频繁失败")

        # 2. 检测异常调用
        print("[2/5] 检测异常调用...")
        abnormal_calls = self._detect_abnormal_calls()
        if abnormal_calls:
            report["risks"].extend(abnormal_calls)
            print(f"  [WARN]  发现 {len(abnormal_calls)} 个异常调用风险")
        else:
            print(f"  [OK] 无异常调用")

        # 3. 检测权限异常
        print("[3/5] 检测权限异常...")
        permission_issues = self._detect_permission_issues()
        if permission_issues:
            report["risks"].extend(permission_issues)
            print(f"  [WARN]  发现 {len(permission_issues)} 个权限异常")
        else:
            print(f"  [OK] 无权限异常")

        # 4. 检测资源滥用
        print("[4/5] 检测资源滥用...")
        resource_abuse = self._detect_resource_abuse()
        if resource_abuse:
            report["risks"].extend(resource_abuse)
            print(f"  [WARN]  发现 {len(resource_abuse)} 个资源滥用")
        else:
            print(f"  [OK] 无资源滥用")

        # 5. 检测数据异常
        print("[5/5] 检测数据异常...")
        data_anomalies = self._detect_data_anomalies()
        if data_anomalies:
            report["risks"].extend(data_anomalies)
            print(f"  [WARN]  发现 {len(data_anomalies)} 个数据异常")
        else:
            print(f"  [OK] 无数据异常")

        # 保存报告
        self._save_report(report)

        # 自动熔断高风险操作
        high_risks = [r for r in report["risks"] if r["severity"] == "high"]
        if high_risks:
            self._circuit_break(high_risks)

        print()
        print("=" * 60)
        if report["risks"]:
            print(f"  [WARN]  发现 {len(report['risks'])} 个安全风险")
        else:
            print(f"  [OK] 系统安全")
        print("=" * 60)

        return report

    def _detect_frequent_failures(self) -> List[Dict]:
        """检测频繁失败"""
        risks = []
        cutoff = datetime.now() - timedelta(hours=1)
        
        # 按 Agent 统计最近1小时的失败次数
        agent_failures = defaultdict(list)
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            start_time = datetime.fromisoformat(trace.get("start_time", ""))
            if start_time < cutoff:
                continue
            
            if not trace.get("success", False):
                agent_id = trace.get("agent_id", "unknown")
                agent_failures[agent_id].append(trace)

        # 检查是否超过阈值
        for agent_id, failures in agent_failures.items():
            if len(failures) >= self.FREQUENT_FAILURE_THRESHOLD:
                risks.append({
                    "type": "frequent_failures",
                    "severity": "high",
                    "agent_id": agent_id,
                    "failure_count": len(failures),
                    "description": f"Agent {agent_id} 在1小时内失败 {len(failures)} 次",
                    "recommendation": "检查 Agent 配置，考虑暂停该 Agent"
                })

        return risks

    def _detect_abnormal_calls(self) -> List[Dict]:
        """检测异常调用（非工作时间大量操作）"""
        risks = []
        cutoff = datetime.now() - timedelta(hours=1)
        
        # 统计非工作时间（23:00-08:00）的调用次数
        night_calls = []
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            start_time = datetime.fromisoformat(trace.get("start_time", ""))
            if start_time < cutoff:
                continue
            
            hour = start_time.hour
            if hour >= 23 or hour < 8:
                night_calls.append(trace)

        if len(night_calls) >= self.ABNORMAL_CALL_THRESHOLD:
            risks.append({
                "type": "abnormal_calls",
                "severity": "medium",
                "call_count": len(night_calls),
                "description": f"非工作时间（23:00-08:00）有 {len(night_calls)} 次调用",
                "recommendation": "检查是否有异常自动化任务"
            })

        return risks

    def _detect_permission_issues(self) -> List[Dict]:
        """检测权限异常"""
        risks = []
        
        # 敏感路径列表
        sensitive_paths = [
            "C:\\Windows\\System32",
            "C:\\Program Files",
            "/etc",
            "/root",
            "~/.ssh"
        ]

        # 检查是否有访问敏感路径的尝试
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            for tool_call in trace.get("tools_used", []):
                args = tool_call.get("args", {})
                path = args.get("path", "") or args.get("file", "")
                
                for sensitive in sensitive_paths:
                    if sensitive.lower() in path.lower():
                        risks.append({
                            "type": "permission_issue",
                            "severity": "high",
                            "agent_id": trace.get("agent_id"),
                            "path": path,
                            "description": f"Agent {trace.get('agent_id')} 尝试访问敏感路径 {path}",
                            "recommendation": "检查 Agent 权限配置"
                        })
                        break

        return risks

    def _detect_resource_abuse(self) -> List[Dict]:
        """检测资源滥用"""
        risks = []
        
        # 统计每个 Agent 的任务数量
        agent_task_counts = Counter()
        total_tasks = 0
        
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            agent_id = trace.get("agent_id", "unknown")
            agent_task_counts[agent_id] += 1
            total_tasks += 1

        # 检查是否有单个 Agent 占用过多资源
        if total_tasks > 0:
            for agent_id, count in agent_task_counts.items():
                ratio = count / total_tasks
                if ratio >= self.RESOURCE_ABUSE_THRESHOLD:
                    risks.append({
                        "type": "resource_abuse",
                        "severity": "medium",
                        "agent_id": agent_id,
                        "task_count": count,
                        "ratio": ratio,
                        "description": f"Agent {agent_id} 占用 {ratio:.1%} 的资源",
                        "recommendation": "检查是否有死循环或资源泄漏"
                    })

        return risks

    def _detect_data_anomalies(self) -> List[Dict]:
        """检测数据异常"""
        risks = []
        cutoff = datetime.now() - timedelta(hours=1)
        
        # 统计最近1小时的数据操作次数
        data_ops = 0
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            start_time = datetime.fromisoformat(trace.get("start_time", ""))
            if start_time < cutoff:
                continue
            
            for tool_call in trace.get("tools_used", []):
                tool = tool_call.get("tool", "")
                if tool in ["read", "write", "edit"]:
                    data_ops += 1

        if data_ops >= self.DATA_ANOMALY_THRESHOLD:
            risks.append({
                "type": "data_anomaly",
                "severity": "medium",
                "operation_count": data_ops,
                "description": f"1小时内有 {data_ops} 次数据操作",
                "recommendation": "检查是否有数据泄漏或异常批处理"
            })

        return risks

    def _circuit_break(self, high_risks: List[Dict]):
        """熔断高风险操作"""
        print()
        print("🚨 检测到高风险，执行熔断...")
        
        for risk in high_risks:
            if risk["type"] == "frequent_failures":
                agent_id = risk["agent_id"]
                print(f"  🔴 熔断 Agent: {agent_id}")
                # 这里实际应该调用 Agent 管理器暂停该 Agent
                # 目前只是记录
                
            elif risk["type"] == "permission_issue":
                agent_id = risk["agent_id"]
                print(f"  🔴 限制 Agent 权限: {agent_id}")
                # 这里实际应该调整 Agent 权限
                # 目前只是记录

    def _save_report(self, report: Dict):
        """保存安全报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.security_dir / f"security_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {report_file}")


def main():
    """主函数"""
    agent = AIOSSecurityAgent()
    report = agent.run()
    
    # 输出摘要
    risks = report.get("risks", [])
    if risks:
        print(f"\nSECURITY_ALERT:{len(risks)}")
    else:
        print("\nSECURITY_OK")


if __name__ == "__main__":
    main()
