#!/usr/bin/env python3
"""
Dispatch Pattern Detector - 从决策日志识别中枢模式

识别 4 类决策模式：
1. decision_input_pattern - 哪类输入最常被拦截/降级
2. handler_rejection_pattern - 哪类 handler 最常被淘汰
3. policy_pattern - 哪类 policy 最常触发
4. fallback_pattern - 哪类 fallback 最常被走

Version: 1.0.0
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter, defaultdict
from datetime import datetime
from enum import Enum


class DecisionPatternType(Enum):
    """决策模式类型"""
    INPUT_DEGRADATION = "decision_input_pattern"
    HANDLER_REJECTION = "handler_rejection_pattern"
    POLICY_TRIGGER = "policy_pattern"
    FALLBACK_ROUTE = "fallback_pattern"


class DispatchPatternDetector:
    """中枢决策模式检测器"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / "data"
        self.dispatch_log = self.data_dir / "dispatch_log.jsonl"
        
        # 模式计数器
        self.degraded_situations = Counter()
        self.rejected_handlers = Counter()
        self.rejection_reasons = defaultdict(list)
        self.policy_triggers = Counter()
        self.fallback_routes = Counter()
        
        # 原始记录
        self.records = []
    
    def load_dispatch_log(self) -> List[Dict[str, Any]]:
        """加载决策日志"""
        if not self.dispatch_log.exists():
            return []
        
        records = []
        with open(self.dispatch_log, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        
                        # 支持两种格式：
                        # 1. 嵌套格式（有 decision_record 字段）
                        # 2. 扁平格式（直接包含字段）
                        if 'decision_record' in entry:
                            decision_record = entry['decision_record']
                            policy_result = decision_record.get('policy_result', {})
                            router_result = decision_record.get('router_result', {})
                            
                            record = {
                                'timestamp': entry.get('timestamp', ''),
                                'current_situation': decision_record.get('current_situation', 'unknown'),
                                'rejected_handlers': [
                                    h['handler'] for h in router_result.get('rejected_handlers', [])
                                ],
                                'chosen_handler': decision_record.get('chosen_handler', 'none'),
                                'policy_result': policy_result.get('policy_result', 'unknown') if isinstance(policy_result, dict) else 'unknown',
                                'policy_reason': policy_result.get('policy_reason', 'unknown') if isinstance(policy_result, dict) else 'unknown',
                                'fallback_action': policy_result.get('fallback_action', 'none') if isinstance(policy_result, dict) else 'none',
                                'final_status': decision_record.get('final_status', 'unknown')
                            }
                        else:
                            # 扁平格式（测试用）
                            record = entry
                        
                        records.append(record)
                    except json.JSONDecodeError:
                        continue
        
        self.records = records
        return records
    
    def detect_input_degradation_patterns(self):
        """检测输入降级模式"""
        for record in self.records:
            situation = record.get('current_situation', 'unknown')
            status = record.get('final_status', 'unknown')
            
            if status in ['blocked', 'degraded', 'failed']:
                key = f"{situation} → {status}"
                self.degraded_situations[key] += 1
    
    def detect_handler_rejection_patterns(self):
        """检测 handler 淘汰模式"""
        for record in self.records:
            rejected = record.get('rejected_handlers', [])
            chosen = record.get('chosen_handler', 'none')
            
            for handler in rejected:
                self.rejected_handlers[handler] += 1
                self.rejection_reasons[handler].append({
                    'chosen_instead': chosen,
                    'situation': record.get('current_situation', 'unknown')
                })
    
    def detect_policy_trigger_patterns(self):
        """检测 policy 触发模式"""
        for record in self.records:
            policy_result = record.get('policy_result', 'unknown')
            policy_reason = record.get('policy_reason', 'unknown')
            
            if policy_result in ['degrade', 'require_confirmation', 'reject']:
                key = f"{policy_result}: {policy_reason}"
                self.policy_triggers[key] += 1
    
    def detect_fallback_route_patterns(self):
        """检测 fallback 路径模式"""
        for record in self.records:
            fallback = record.get('fallback_action', 'none')
            status = record.get('final_status', 'unknown')
            
            if fallback != 'none':
                key = f"{fallback} (→ {status})"
                self.fallback_routes[key] += 1
    
    def analyze(self) -> Dict[str, Any]:
        """执行完整分析"""
        self.load_dispatch_log()
        
        if not self.records:
            return {
                'status': 'no_data',
                'message': 'dispatch_log.jsonl 为空或不存在'
            }
        
        # 检测 4 类模式
        self.detect_input_degradation_patterns()
        self.detect_handler_rejection_patterns()
        self.detect_policy_trigger_patterns()
        self.detect_fallback_route_patterns()
        
        # 生成报告
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成分析报告"""
        # Top 5 degraded situations
        top_degraded = self.degraded_situations.most_common(5)
        
        # Top 5 rejected handlers
        top_rejected = self.rejected_handlers.most_common(5)
        
        # Top 5 policy triggers
        top_policies = self.policy_triggers.most_common(5)
        
        # Top 5 fallback routes
        top_fallbacks = self.fallback_routes.most_common(5)
        
        # 生成优化建议
        optimization_target = self._identify_optimization_target(
            top_degraded, top_rejected, top_policies, top_fallbacks
        )
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(self.records),
            'patterns': {
                'input_degradation': {
                    'type': DecisionPatternType.INPUT_DEGRADATION.value,
                    'top_5': [
                        {'pattern': pattern, 'count': count}
                        for pattern, count in top_degraded
                    ]
                },
                'handler_rejection': {
                    'type': DecisionPatternType.HANDLER_REJECTION.value,
                    'top_5': [
                        {
                            'handler': handler,
                            'count': count,
                            'sample_reasons': self.rejection_reasons[handler][:3]
                        }
                        for handler, count in top_rejected
                    ]
                },
                'policy_trigger': {
                    'type': DecisionPatternType.POLICY_TRIGGER.value,
                    'top_5': [
                        {'pattern': pattern, 'count': count}
                        for pattern, count in top_policies
                    ]
                },
                'fallback_route': {
                    'type': DecisionPatternType.FALLBACK_ROUTE.value,
                    'top_5': [
                        {'pattern': pattern, 'count': count}
                        for pattern, count in top_fallbacks
                    ]
                }
            },
            'summary': self._generate_summary(
                top_degraded, top_rejected, top_policies, top_fallbacks
            ),
            'optimization_target': optimization_target
        }
        
        return report
    
    def _generate_summary(self, top_degraded, top_rejected, top_policies, top_fallbacks) -> str:
        """生成固定句式总结"""
        lines = []
        
        # 1. 最常被降级的输入类型
        if top_degraded:
            lines.append(f"当前最常被降级的输入类型：{top_degraded[0][0]}")
        else:
            lines.append("当前最常被降级的输入类型：无")
        
        # 2. 最常被淘汰的 handler
        if top_rejected:
            handler = top_rejected[0][0]
            reasons = self.rejection_reasons[handler]
            reason_summary = reasons[0]['chosen_instead'] if reasons else 'unknown'
            lines.append(f"当前最常被淘汰的 handler：{handler} (原因: 被 {reason_summary} 替代)")
        else:
            lines.append("当前最常被淘汰的 handler：无")
        
        # 3. 最常触发的 policy 原因
        if top_policies:
            lines.append(f"当前最常触发的 policy 原因：{top_policies[0][0]}")
        else:
            lines.append("当前最常触发的 policy 原因：无")
        
        # 4. 最常走的 fallback 路径
        if top_fallbacks:
            lines.append(f"当前最常走的 fallback 路径：{top_fallbacks[0][0]}")
        else:
            lines.append("当前最常走的 fallback 路径：无")
        
        return "\n".join(lines)
    
    def _identify_optimization_target(self, top_degraded, top_rejected, 
                                     top_policies, top_fallbacks) -> str:
        """识别最值得优化的中枢决策模式"""
        # 简单启发式：哪个模式出现频率最高
        max_count = 0
        target = "当前决策模式正常，无明显优化点"
        
        if top_degraded and top_degraded[0][1] > max_count:
            max_count = top_degraded[0][1]
            target = f"输入降级模式过于频繁：{top_degraded[0][0]}（出现 {max_count} 次）"
        
        if top_rejected and top_rejected[0][1] > max_count:
            max_count = top_rejected[0][1]
            target = f"handler 淘汰过于集中：{top_rejected[0][0]}（被淘汰 {max_count} 次）"
        
        if top_policies and top_policies[0][1] > max_count:
            max_count = top_policies[0][1]
            target = f"policy 触发过于频繁：{top_policies[0][0]}（触发 {max_count} 次）"
        
        if top_fallbacks and top_fallbacks[0][1] > max_count:
            max_count = top_fallbacks[0][1]
            target = f"fallback 路径过于单一：{top_fallbacks[0][0]}（使用 {max_count} 次）"
        
        return target
    
    def save_report(self, report: Dict[str, Any], output_path: Path = None):
        """保存报告"""
        if output_path is None:
            output_path = self.data_dir / "dispatch_pattern_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 报告已保存：{output_path}")
    
    def print_summary(self, report: Dict[str, Any]):
        """打印总结"""
        print("\n" + "="*60)
        print("中枢决策模式分析报告")
        print("="*60)
        print(f"\n总记录数：{report['total_records']}")
        print("\n" + report['summary'])
        print(f"\n当前最值得优先优化的中枢决策模式：")
        print(f"  {report['optimization_target']}")
        print("\n" + "="*60)


def main():
    """主函数"""
    detector = DispatchPatternDetector()
    report = detector.analyze()
    
    if report.get('status') == 'no_data':
        print(f"⚠️  {report['message']}")
        return
    
    detector.save_report(report)
    detector.print_summary(report)


if __name__ == '__main__':
    main()
