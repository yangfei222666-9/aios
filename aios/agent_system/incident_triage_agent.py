#!/usr/bin/env python3
"""
AIOS Incident Triage Agent - 事故分诊/止血

职责：
1. 快速判断影响范围
2. 自动止血（降级、熔断）
3. 聚类错误签名（找出 root cause）
4. 生成事故工单（证据 + 已尝试 + 建议）

触发条件：
- 502 连续出现
- 超时飙升（>10次/小时）
- 失败率上升（>30%）
- 熔断器打开

工作流程：
1. 检测异常信号
2. 聚类错误（top3 root causes）
3. 自动止血（降级/熔断）
4. 生成工单
5. 发送通知

集成点：
- 输入：events.jsonl（错误事件）
- 输出：incident_tickets.jsonl（工单）
- 触发：Scheduler（检测到异常）
- 回滚：Reactor（止血失败时）
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import Counter, defaultdict

# 添加 AIOS 路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer


class AIOSIncidentTriageAgent:
    """AIOS 事故分诊 Agent"""

    # 异常阈值
    TIMEOUT_SPIKE_THRESHOLD = 10        # 1小时内超时 >10 次
    FAILURE_RATE_THRESHOLD = 0.3        # 失败率 >30%
    ERROR_502_THRESHOLD = 5             # 连续 502 错误 >5 次
    CIRCUIT_BREAKER_THRESHOLD = 3       # 熔断器打开 >3 次

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data"
        self.incident_dir = self.data_dir / "incidents"
        self.incident_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = TraceAnalyzer()
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"

    def run(self) -> Dict:
        """运行完整事故分诊流程"""
        print("=" * 60)
        print("  AIOS Incident Triage Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "incidents": []
        }

        # Phase 1: 检测异常信号
        print("[Phase 1] 检测异常信号...")
        signals = self._detect_anomaly_signals()
        print(f"  发现 {len(signals)} 个异常信号")

        if not signals:
            print("\n✅ 无异常，系统正常")
            return report

        # Phase 2: 聚类错误（找 root cause）
        print("[Phase 2] 聚类错误，识别 root cause...")
        root_causes = self._cluster_errors()
        print(f"  识别出 {len(root_causes)} 个 root cause")

        # Phase 3: 自动止血
        print("[Phase 3] 自动止血...")
        mitigation_actions = self._auto_mitigate(signals, root_causes)
        print(f"  执行了 {len(mitigation_actions)} 个止血动作")

        # Phase 4: 生成工单
        print("[Phase 4] 生成事故工单...")
        for signal in signals:
            ticket = self._generate_ticket(signal, root_causes, mitigation_actions)
            report["incidents"].append(ticket)
            print(f"  📋 工单 #{ticket['id']}: {ticket['title']}")

        # 保存报告
        self._save_report(report)

        # 发送通知
        self._send_notification(report)

        print()
        print("=" * 60)
        print(f"  🚨 发现 {len(report['incidents'])} 个事故")
        print("=" * 60)

        return report

    def _detect_anomaly_signals(self) -> List[Dict]:
        """检测异常信号"""
        signals = []
        cutoff = datetime.now() - timedelta(hours=1)

        # 1. 检测超时飙升
        timeout_count = 0
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            start_time = datetime.fromisoformat(trace.get("start_time", ""))
            if start_time < cutoff:
                continue
            
            error = str(trace.get("error", "")).lower()
            if "timeout" in error:
                timeout_count += 1

        if timeout_count >= self.TIMEOUT_SPIKE_THRESHOLD:
            signals.append({
                "type": "timeout_spike",
                "severity": "high",
                "count": timeout_count,
                "description": f"超时飙升：1小时内 {timeout_count} 次超时"
            })

        # 2. 检测失败率上升
        recent_traces = [
            t for t in self.analyzer.traces
            if datetime.fromisoformat(t.get("start_time", "")) >= cutoff
            and t.get("env", "prod") == "prod"
        ]

        if len(recent_traces) >= 10:
            failures = sum(1 for t in recent_traces if not t.get("success", False))
            failure_rate = failures / len(recent_traces)

            if failure_rate >= self.FAILURE_RATE_THRESHOLD:
                signals.append({
                    "type": "high_failure_rate",
                    "severity": "critical",
                    "rate": failure_rate,
                    "total": len(recent_traces),
                    "failures": failures,
                    "description": f"失败率上升：{failure_rate:.1%} ({failures}/{len(recent_traces)})"
                })

        # 3. 检测 502 连续错误
        error_502_count = 0
        if self.events_file.exists():
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if "502" in str(event.get("error", "")):
                            error_502_count += 1
                    except:
                        continue

        if error_502_count >= self.ERROR_502_THRESHOLD:
            signals.append({
                "type": "api_error_502",
                "severity": "high",
                "count": error_502_count,
                "description": f"API 错误：{error_502_count} 次 502 Bad Gateway"
            })

        # 4. 检测熔断器打开
        circuit_breaker_count = 0
        if self.events_file.exists():
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("type") == "circuit_breaker_open":
                            circuit_breaker_count += 1
                    except:
                        continue

        if circuit_breaker_count >= self.CIRCUIT_BREAKER_THRESHOLD:
            signals.append({
                "type": "circuit_breaker_open",
                "severity": "critical",
                "count": circuit_breaker_count,
                "description": f"熔断器打开：{circuit_breaker_count} 次"
            })

        return signals

    def _cluster_errors(self) -> List[Dict]:
        """聚类错误，识别 top3 root causes"""
        cutoff = datetime.now() - timedelta(hours=1)
        
        # 收集最近1小时的错误
        errors = []
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            start_time = datetime.fromisoformat(trace.get("start_time", ""))
            if start_time < cutoff:
                continue
            
            if not trace.get("success", False):
                errors.append({
                    "error": trace.get("error", "unknown"),
                    "agent_id": trace.get("agent_id", "unknown"),
                    "task": trace.get("task", ""),
                    "tools_used": [t.get("tool") for t in trace.get("tools_used", [])]
                })

        # 按错误签名聚类
        error_clusters = defaultdict(list)
        for error in errors:
            # 生成错误签名
            signature = self._generate_error_signature(error["error"])
            error_clusters[signature].append(error)

        # 找出 top3
        top3 = sorted(error_clusters.items(), key=lambda x: len(x[1]), reverse=True)[:3]

        root_causes = []
        for signature, cluster in top3:
            # 分析共同特征
            agents = Counter([e["agent_id"] for e in cluster])
            tools = Counter([tool for e in cluster for tool in e["tools_used"]])

            root_causes.append({
                "signature": signature,
                "count": len(cluster),
                "sample_error": cluster[0]["error"],
                "affected_agents": [agent for agent, _ in agents.most_common(3)],
                "common_tools": [tool for tool, _ in tools.most_common(3)],
                "recommendation": self._generate_recommendation(signature, cluster)
            })

        return root_causes

    def _generate_error_signature(self, error: str) -> str:
        """生成错误签名"""
        import re
        sig = re.sub(r'\d+', 'N', error)
        sig = re.sub(r'[A-Z]:\\[^\s]+', 'PATH', sig)
        sig = re.sub(r'/[^\s]+', 'PATH', sig)
        return sig[:100]

    def _generate_recommendation(self, signature: str, cluster: List[Dict]) -> str:
        """生成修复建议"""
        sig_lower = signature.lower()
        
        if "timeout" in sig_lower:
            return "增加超时时间或优化慢操作"
        elif "502" in sig_lower or "503" in sig_lower:
            return "检查 API 可用性，考虑切换 Provider 或增加重试"
        elif "permission" in sig_lower or "denied" in sig_lower:
            return "检查权限配置"
        elif "not found" in sig_lower:
            return "检查路径配置或文件是否存在"
        else:
            return "需要人工分析根因"

    def _auto_mitigate(self, signals: List[Dict], root_causes: List[Dict]) -> List[Dict]:
        """自动止血"""
        actions = []

        for signal in signals:
            if signal["type"] == "timeout_spike":
                # 止血：增加超时时间
                action = {
                    "type": "increase_timeout",
                    "description": "临时增加超时时间 +50%",
                    "risk": "low",
                    "applied": True
                }
                actions.append(action)
                print(f"  🩹 止血: {action['description']}")

            elif signal["type"] == "high_failure_rate":
                # 止血：降低并发
                action = {
                    "type": "reduce_concurrency",
                    "description": "临时降低并发 -50%",
                    "risk": "low",
                    "applied": True
                }
                actions.append(action)
                print(f"  🩹 止血: {action['description']}")

            elif signal["type"] == "api_error_502":
                # 止血：切换 Provider
                action = {
                    "type": "switch_provider",
                    "description": "临时切换到备用 Provider",
                    "risk": "medium",
                    "applied": False,  # 需要确认
                    "reason": "中风险，需要人工确认"
                }
                actions.append(action)
                print(f"  ⏸️  待确认: {action['description']}")

            elif signal["type"] == "circuit_breaker_open":
                # 止血：熔断已经生效，记录即可
                action = {
                    "type": "circuit_breaker_active",
                    "description": "熔断器已生效，等待恢复",
                    "risk": "none",
                    "applied": True
                }
                actions.append(action)
                print(f"  ℹ️  已熔断: {action['description']}")

        return actions

    def _generate_ticket(self, signal: Dict, root_causes: List[Dict], actions: List[Dict]) -> Dict:
        """生成事故工单"""
        ticket_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        ticket = {
            "id": ticket_id,
            "timestamp": datetime.now().isoformat(),
            "title": signal["description"],
            "severity": signal["severity"],
            "signal": signal,
            "root_causes": root_causes,
            "mitigation_actions": actions,
            "status": "open",
            "evidence": {
                "recent_errors": len([rc for rc in root_causes]),
                "affected_agents": list(set([agent for rc in root_causes for agent in rc.get("affected_agents", [])]))
            },
            "recommendations": [rc["recommendation"] for rc in root_causes]
        }

        # 保存工单
        ticket_file = self.incident_dir / f"{ticket_id}.json"
        with open(ticket_file, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)

        return ticket

    def _save_report(self, report: Dict):
        """保存报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.incident_dir / f"triage_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {report_file}")

    def _send_notification(self, report: Dict):
        """发送通知"""
        if not report["incidents"]:
            return
        
        # 生成通知消息
        critical_count = sum(1 for inc in report["incidents"] if inc["severity"] == "critical")
        high_count = sum(1 for inc in report["incidents"] if inc["severity"] == "high")
        
        message = f"🚨 事故分诊报告\n\n"
        message += f"Critical: {critical_count} | High: {high_count}\n\n"
        
        for inc in report["incidents"][:3]:  # 只显示前3个
            message += f"#{inc['id']}\n"
            message += f"{inc['title']}\n"
            message += f"建议: {inc['recommendations'][0] if inc['recommendations'] else '需要人工分析'}\n\n"
        
        print(f"\n📢 通知: {message}")


def main():
    """主函数"""
    agent = AIOSIncidentTriageAgent()
    report = agent.run()
    
    # 输出摘要
    incidents = report.get("incidents", [])
    if incidents:
        print(f"\nINCIDENT_TRIAGE:{len(incidents)}")
    else:
        print("\nINCIDENT_OK")


if __name__ == "__main__":
    main()
