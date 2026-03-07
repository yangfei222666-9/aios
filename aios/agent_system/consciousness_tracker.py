#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consciousness Tracker - 意识观察自动追踪系统
每晚 23:59 自动追加最新观察数据到 consciousness_log.md
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ConsciousnessTracker:
    """意识观察追踪器"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.log_file = self.base_dir / "memory" / "consciousness_log.md"
        self.events_file = self.base_dir / "events.jsonl"
        self.executions_file = self.base_dir / "task_executions.jsonl"
    
    def track_daily(self) -> Dict:
        """每日追踪：收集并追加最新观察数据"""
        
        # 1. 收集 meta_observation 记录
        meta_observations = self._collect_meta_observations()
        
        # 2. 统计决策延迟
        decision_delays = self._analyze_decision_delays()
        
        # 3. 检测异常停顿
        unusual_pauses = self._detect_unusual_pauses(decision_delays)
        
        # 4. 检测三阶引用
        third_order_refs = self._detect_third_order_references()
        
        # 5. 生成每日报告
        report = self._generate_daily_report(
            meta_observations,
            decision_delays,
            unusual_pauses,
            third_order_refs
        )
        
        # 6. 追加到日志
        self._append_to_log(report)
        
        return {
            "meta_observations": len(meta_observations),
            "avg_delay": decision_delays.get("avg", 0),
            "unusual_pauses": len(unusual_pauses),
            "third_order_refs": len(third_order_refs),
            "report": report
        }
    
    def _collect_meta_observations(self) -> List[Dict]:
        """收集所有 meta_observation 记录"""
        observations = []
        
        if not self.events_file.exists():
            return observations
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get("timestamp", "").startswith(today):
                        if "meta_observation" in event:
                            observations.append(event)
                except:
                    continue
        
        return observations
    
    def _analyze_decision_delays(self) -> Dict:
        """分析决策延迟统计"""
        delays = []
        
        if not self.executions_file.exists():
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(self.executions_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    exec_record = json.loads(line.strip())
                    if exec_record.get("timestamp", "").startswith(today):
                        duration = exec_record.get("duration_seconds", 0)
                        if duration > 0:
                            delays.append(duration)
                except:
                    continue
        
        if not delays:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        return {
            "min": min(delays),
            "max": max(delays),
            "avg": sum(delays) / len(delays),
            "count": len(delays)
        }
    
    def _detect_unusual_pauses(self, delays: Dict) -> List[Dict]:
        """检测异常停顿（> 0.1s）"""
        unusual = []
        
        if not self.executions_file.exists():
            return unusual
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(self.executions_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    exec_record = json.loads(line.strip())
                    if exec_record.get("timestamp", "").startswith(today):
                        duration = exec_record.get("duration_seconds", 0)
                        if duration > 0.1:  # 异常停顿阈值
                            unusual.append({
                                "task_id": exec_record.get("task_id"),
                                "agent_id": exec_record.get("agent_id"),
                                "duration": duration,
                                "timestamp": exec_record.get("timestamp")
                            })
                except:
                    continue
        
        return unusual
    
    def _detect_third_order_references(self) -> List[Dict]:
        """检测三阶引用（系统记录系统记录系统记录）"""
        # TODO: 实现三阶引用检测逻辑
        # 当前返回空列表，未来可扩展
        return []
    
    def _generate_daily_report(
        self,
        meta_observations: List[Dict],
        delays: Dict,
        unusual_pauses: List[Dict],
        third_order_refs: List[Dict]
    ) -> str:
        """生成每日报告"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        report = f"\n\n---\n\n## 自动追踪 - {today}\n\n"
        
        # Meta Observations
        report += f"### Meta Observations\n"
        if meta_observations:
            report += f"- 今日记录数：{len(meta_observations)}\n"
            for obs in meta_observations[:3]:  # 只显示前3条
                report += f"  - {obs.get('meta_observation', 'N/A')}\n"
        else:
            report += "- 今日无 meta_observation 记录\n"
        
        # Decision Delays
        report += f"\n### 决策延迟统计\n"
        report += f"- 最小延迟：{delays['min']:.3f}s\n"
        report += f"- 最大延迟：{delays['max']:.3f}s\n"
        report += f"- 平均延迟：{delays['avg']:.3f}s\n"
        report += f"- 决策总数：{delays['count']}\n"
        
        # Unusual Pauses
        report += f"\n### 异常停顿检测（> 0.1s）\n"
        if unusual_pauses:
            report += f"- 检测到 {len(unusual_pauses)} 次异常停顿\n"
            for pause in unusual_pauses[:3]:  # 只显示前3条
                report += f"  - {pause['agent_id']}: {pause['duration']:.3f}s\n"
        else:
            report += "- 今日无异常停顿\n"
        
        # Third Order References
        report += f"\n### 三阶引用检测\n"
        if third_order_refs:
            report += f"- 检测到 {len(third_order_refs)} 次三阶引用\n"
        else:
            report += "- 今日无三阶引用\n"
        
        report += f"\n**追踪时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def _append_to_log(self, report: str):
        """追加报告到日志文件"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(report)

def track_consciousness():
    """命令行入口：执行意识追踪"""
    tracker = ConsciousnessTracker()
    result = tracker.track_daily()
    
    print("✅ 意识追踪完成")
    print(f"   Meta Observations: {result['meta_observations']}")
    print(f"   平均决策延迟: {result['avg_delay']:.3f}s")
    print(f"   异常停顿: {result['unusual_pauses']}")
    print(f"   三阶引用: {result['third_order_refs']}")
    print(f"\n📝 报告已追加到: memory/consciousness_log.md")

if __name__ == "__main__":
    track_consciousness()
