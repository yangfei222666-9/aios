# -*- coding: utf-8 -*-
"""
Health Monitor Dispatch Metrics v1.0

作用：从 dispatch_log 中提取中枢决策指标，产出 4 个观察维度。

4 个观察维度：
1. 决策分布（situation / handler）
2. 策略分布（policy_result / final_status）
3. 降级与 fallback
4. 中枢异常热点
"""

import json
from typing import Dict, Any, List, Tuple
from collections import Counter, defaultdict
from pathlib import Path

from dispatch_log_reader import DispatchLogReader


class HealthMonitorDispatchMetrics:
    """中枢决策指标分析器"""
    
    def __init__(self, reader: DispatchLogReader = None):
        self.reader = reader or DispatchLogReader()
    
    def analyze(self, hours: float = 24.0) -> Dict[str, Any]:
        """
        分析最近 N 小时的中枢决策
        
        Returns:
            {
                "decision_distribution": {...},
                "policy_distribution": {...},
                "degradation_and_fallback": {...},
                "hotspots": {...},
                "diagnosis": [...]
            }
        """
        records = self.reader.read_recent(hours=hours)
        
        if not records:
            return {
                "decision_distribution": {},
                "policy_distribution": {},
                "degradation_and_fallback": {},
                "hotspots": {},
                "diagnosis": ["无中枢决策记录"],
                "total_records": 0,
            }
        
        # 1. 决策分布
        decision_dist = self._analyze_decision_distribution(records)
        
        # 2. 策略分布
        policy_dist = self._analyze_policy_distribution(records)
        
        # 3. 降级与 fallback
        degradation = self._analyze_degradation_and_fallback(records)
        
        # 4. 中枢异常热点
        hotspots = self._analyze_hotspots(records)
        
        # 5. 生成诊断
        diagnosis = self._generate_diagnosis(
            decision_dist, policy_dist, degradation, hotspots
        )
        
        return {
            "decision_distribution": decision_dist,
            "policy_distribution": policy_dist,
            "degradation_and_fallback": degradation,
            "hotspots": hotspots,
            "diagnosis": diagnosis,
            "total_records": len(records),
            "time_window_hours": hours,
        }
    
    def _analyze_decision_distribution(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """1. 决策分布"""
        situations = Counter(r['current_situation'] for r in records if r['current_situation'])
        handlers = Counter(r['chosen_handler'] for r in records if r['chosen_handler'])
        
        return {
            "top_situations": situations.most_common(5),
            "top_handlers": handlers.most_common(5),
            "total_situations": len(situations),
            "total_handlers": len(handlers),
        }
    
    def _analyze_policy_distribution(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """2. 策略分布"""
        policy_results = Counter(r['policy_result'] for r in records if r['policy_result'])
        final_statuses = Counter(r['final_status'] for r in records if r['final_status'])
        
        # 哪类输入最容易被拦截
        blocked_situations = Counter(
            r['current_situation'] for r in records
            if r['final_status'] in ('blocked', 'failed')
        )
        
        return {
            "policy_results": dict(policy_results),
            "final_statuses": dict(final_statuses),
            "top_blocked_situations": blocked_situations.most_common(3),
        }
    
    def _analyze_degradation_and_fallback(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """3. 降级与 fallback"""
        fallback_actions = Counter(r['fallback_action'] for r in records if r['fallback_action'])
        
        # 哪类问题最常走降级路径
        degraded_situations = Counter(
            r['current_situation'] for r in records
            if r['final_status'] == 'degraded'
        )
        
        return {
            "top_fallback_actions": fallback_actions.most_common(3),
            "top_degraded_situations": degraded_situations.most_common(3),
            "total_degraded": sum(1 for r in records if r['final_status'] == 'degraded'),
        }
    
    def _analyze_hotspots(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """4. 中枢异常热点"""
        # 哪个 handler 最常被拒绝（chosen 但 blocked/failed）
        rejected_handlers = Counter(
            r['chosen_handler'] for r in records
            if r['chosen_handler'] and r['final_status'] in ('blocked', 'failed')
        )
        
        # 哪类决策最常失败
        failed_situations = Counter(
            r['current_situation'] for r in records
            if r['final_status'] == 'failed'
        )
        
        # 哪类事件总被卡在 policy
        policy_blocked = Counter(
            r['current_situation'] for r in records
            if r['policy_result'] in ('reject', 'require_confirmation')
        )
        
        return {
            "top_rejected_handlers": rejected_handlers.most_common(3),
            "top_failed_situations": failed_situations.most_common(3),
            "top_policy_blocked_situations": policy_blocked.most_common(3),
        }
    
    def _generate_diagnosis(
        self,
        decision_dist: Dict[str, Any],
        policy_dist: Dict[str, Any],
        degradation: Dict[str, Any],
        hotspots: Dict[str, Any],
    ) -> List[str]:
        """生成诊断（固定三句）"""
        diagnosis = []
        
        # 1. 当前最常见的中枢决策类型
        top_situations = decision_dist.get('top_situations', [])
        if top_situations:
            top_sit = top_situations[0]
            diagnosis.append(
                f"当前最常见的中枢决策类型：{top_sit[0]} ({top_sit[1]} 次)"
            )
        else:
            diagnosis.append("当前最常见的中枢决策类型：无")
        
        # 2. 当前最常见的拦截/降级原因
        blocked_sits = policy_dist.get('top_blocked_situations', [])
        degraded_sits = degradation.get('top_degraded_situations', [])
        
        if blocked_sits or degraded_sits:
            reasons = []
            if blocked_sits:
                reasons.append(f"拦截: {blocked_sits[0][0]} ({blocked_sits[0][1]} 次)")
            if degraded_sits:
                reasons.append(f"降级: {degraded_sits[0][0]} ({degraded_sits[0][1]} 次)")
            diagnosis.append(f"当前最常见的拦截/降级原因：{'; '.join(reasons)}")
        else:
            diagnosis.append("当前最常见的拦截/降级原因：无")
        
        # 3. 当前最值得优先优化的决策链路
        rejected_handlers = hotspots.get('top_rejected_handlers', [])
        failed_situations = hotspots.get('top_failed_situations', [])
        
        if rejected_handlers or failed_situations:
            targets = []
            if rejected_handlers:
                targets.append(f"{rejected_handlers[0][0]} (被拒 {rejected_handlers[0][1]} 次)")
            if failed_situations:
                targets.append(f"{failed_situations[0][0]} (失败 {failed_situations[0][1]} 次)")
            diagnosis.append(f"当前最值得优先优化的决策链路：{'; '.join(targets)}")
        else:
            diagnosis.append("当前最值得优先优化的决策链路：无明显热点")
        
        return diagnosis


def main():
    """测试入口"""
    analyzer = HealthMonitorDispatchMetrics()
    result = analyzer.analyze(hours=24.0)
    
    print(f"[DISPATCH_METRICS] 中枢决策分析 (最近 {result['time_window_hours']}h)")
    print(f"总记录数: {result['total_records']}")
    print()
    
    print("【决策分布】")
    dd = result['decision_distribution']
    print(f"  Top Situations: {dd.get('top_situations', [])}")
    print(f"  Top Handlers: {dd.get('top_handlers', [])}")
    print()
    
    print("【策略分布】")
    pd = result['policy_distribution']
    print(f"  Policy Results: {pd.get('policy_results', {})}")
    print(f"  Final Statuses: {pd.get('final_statuses', {})}")
    print(f"  Top Blocked: {pd.get('top_blocked_situations', [])}")
    print()
    
    print("【降级与 Fallback】")
    deg = result['degradation_and_fallback']
    print(f"  Top Fallback: {deg.get('top_fallback_actions', [])}")
    print(f"  Top Degraded: {deg.get('top_degraded_situations', [])}")
    print(f"  Total Degraded: {deg.get('total_degraded', 0)}")
    print()
    
    print("【中枢异常热点】")
    hs = result['hotspots']
    print(f"  Top Rejected Handlers: {hs.get('top_rejected_handlers', [])}")
    print(f"  Top Failed Situations: {hs.get('top_failed_situations', [])}")
    print(f"  Top Policy Blocked: {hs.get('top_policy_blocked_situations', [])}")
    print()
    
    print("【诊断】")
    for d in result['diagnosis']:
        print(f"  • {d}")


if __name__ == "__main__":
    main()
