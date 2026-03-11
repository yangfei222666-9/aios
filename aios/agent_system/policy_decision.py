"""
Policy Decision - 策略决策器

作用：在自动执行前把风险判断、降级策略、fallback 钉死

必须回答的 4 句：
1. 这个动作能不能直接做
2. 为什么能做 / 不能做
3. 不能直接做时该怎么降级
4. 失败后下一步走哪条 fallback
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from policy_decision_schema import (
    PolicyInput, PolicyOutput, PolicyDecision,
    PolicyResult, FallbackAction, RiskLevel, SystemHealth
)


class PolicyDecisionEngine:
    """策略决策引擎 v1.0"""
    
    VERSION = "1.0.0"
    
    def __init__(self, rules_path: Optional[Path] = None):
        """
        初始化策略引擎
        
        Args:
            rules_path: 规则配置路径（可选）
        """
        self.rules_path = rules_path or Path(__file__).parent / "policy_rules.json"
        self.rules = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Any]:
        """加载策略规则"""
        if not self.rules_path.exists():
            raise FileNotFoundError(f"规则文件不存在: {self.rules_path}")
        
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def decide(self, policy_input: PolicyInput) -> PolicyOutput:
        """
        执行策略决策
        
        Args:
            policy_input: 策略输入
            
        Returns:
            PolicyOutput: 策略决策结果
        """
        # 评估风险
        risk_summary = self._assess_risk(policy_input)
        
        # 匹配规则
        matched_rules = self._match_rules(policy_input, risk_summary)
        
        # 选择最高优先级规则
        if matched_rules:
            chosen_rule = matched_rules[0]
            policy_result = chosen_rule['result']
            fallback_action = chosen_rule.get('fallback')
            policy_reason = self._build_reason(chosen_rule, policy_input, risk_summary)
            matched_rule_names = [r['name'] for r in matched_rules]
        else:
            # 使用默认策略
            default = self.rules['default_policy']
            policy_result = default['result']
            fallback_action = default['fallback']
            policy_reason = default['reason']
            matched_rule_names = ['default']
        
        return PolicyOutput(
            policy_result=policy_result,
            fallback_action=fallback_action,
            policy_reason=policy_reason,
            matched_rules=matched_rule_names,
            risk_summary=risk_summary
        )
    
    def _assess_risk(self, policy_input: PolicyInput) -> Dict[str, Any]:
        """评估风险"""
        risk_factors = []
        risk_score = 0
        
        # 风险等级
        risk_level = policy_input.risk_level
        if risk_level == RiskLevel.CRITICAL.value:
            risk_score += 40
            risk_factors.append("风险等级: critical")
        elif risk_level == RiskLevel.HIGH.value:
            risk_score += 30
            risk_factors.append("风险等级: high")
        elif risk_level == RiskLevel.MEDIUM.value:
            risk_score += 15
            risk_factors.append("风险等级: medium")
        
        # 系统健康状态
        system_health = policy_input.system_health
        if system_health == SystemHealth.CRITICAL.value:
            risk_score += 30
            risk_factors.append("系统状态: critical")
        elif system_health == SystemHealth.DEGRADED.value:
            risk_score += 15
            risk_factors.append("系统状态: degraded")
        
        # 已知失败模式
        if policy_input.known_failure_patterns:
            risk_score += len(policy_input.known_failure_patterns) * 5
            risk_factors.append(f"已知失败模式: {len(policy_input.known_failure_patterns)} 个")
        
        # 操作类型
        if policy_input.operation_type in ["backup_restore", "code_modify"]:
            risk_score += 10
            risk_factors.append(f"破坏性操作: {policy_input.operation_type}")
        
        # 路由决策置信度
        router_confidence = policy_input.router_decision.get('confidence', 100)
        if router_confidence < 70:
            risk_score += 10
            risk_factors.append(f"路由置信度低: {router_confidence:.1f}")
        
        return {
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'risk_level': self._classify_risk_score(risk_score)
        }
    
    def _classify_risk_score(self, score: int) -> str:
        """分类风险分数"""
        if score >= 70:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"
    
    def _match_rules(self, policy_input: PolicyInput, risk_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """匹配规则"""
        matched = []
        
        for rule in self.rules['rules']:
            if self._check_rule_conditions(rule['conditions'], policy_input, risk_summary):
                matched.append(rule)
        
        # 按优先级排序（数字越大优先级越高）
        matched.sort(key=lambda r: r.get('priority', 0), reverse=True)
        
        return matched
    
    def _check_rule_conditions(
        self, 
        conditions: Dict[str, Any], 
        policy_input: PolicyInput,
        risk_summary: Dict[str, Any]
    ) -> bool:
        """检查规则条件"""
        # 检查风险等级
        if 'risk_level' in conditions:
            if policy_input.risk_level not in conditions['risk_level']:
                return False
        
        # 检查系统健康状态
        if 'system_health' in conditions:
            if policy_input.system_health not in conditions['system_health']:
                return False
        
        # 检查操作类型
        if 'operation_type' in conditions:
            if policy_input.operation_type not in conditions['operation_type']:
                return False
        
        # 检查是否有已知失败
        if 'has_known_failures' in conditions:
            has_failures = len(policy_input.known_failure_patterns) > 0
            if has_failures != conditions['has_known_failures']:
                return False
        
        # 检查是否无关键失败
        if 'no_critical_failures' in conditions:
            critical_failures = [f for f in policy_input.known_failure_patterns 
                               if 'critical' in f.lower() or 'fatal' in f.lower()]
            if conditions['no_critical_failures'] and critical_failures:
                return False
        
        # 检查是否有备用处理器
        if 'no_backup_handler' in conditions:
            fallback_handlers = policy_input.router_decision.get('fallback_handlers', [])
            has_backup = len(fallback_handlers) > 0
            if conditions['no_backup_handler'] and has_backup:
                return False
        
        return True
    
    def _build_reason(
        self, 
        rule: Dict[str, Any], 
        policy_input: PolicyInput,
        risk_summary: Dict[str, Any]
    ) -> str:
        """构建策略原因"""
        parts = []
        
        # 规则描述
        parts.append(f"匹配规则: {rule['description']}")
        
        # 风险摘要
        if risk_summary['risk_factors']:
            parts.append(f"风险因素: {'; '.join(risk_summary['risk_factors'][:3])}")
        
        # 风险分数
        parts.append(f"风险评分: {risk_summary['risk_score']}/100 ({risk_summary['risk_level']})")
        
        return " | ".join(parts)
    
    def decide_and_log(self, policy_input: PolicyInput, log_path: Optional[Path] = None) -> PolicyDecision:
        """
        执行策略决策并记录
        
        Args:
            policy_input: 策略输入
            log_path: 日志路径（可选）
            
        Returns:
            PolicyDecision: 完整策略决策记录
        """
        policy_output = self.decide(policy_input)
        
        decision = PolicyDecision(
            policy_input=policy_input,
            policy_output=policy_output,
            timestamp=datetime.now().isoformat(),
            policy_version=self.VERSION
        )
        
        # 记录日志
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(decision.to_dict(), ensure_ascii=False) + '\n')
        
        return decision
    
    def explain_decision(self, policy_output: PolicyOutput) -> str:
        """
        解释策略决策（回答4句话）
        
        1. 这个动作能不能直接做
        2. 为什么能做 / 不能做
        3. 不能直接做时该怎么降级
        4. 失败后下一步走哪条 fallback
        """
        lines = []
        
        # 1. 这个动作能不能直接做
        result_map = {
            PolicyResult.AUTO_EXECUTE.value: "✅ 可以直接执行",
            PolicyResult.REQUIRE_CONFIRMATION.value: "⚠️ 需要确认后执行",
            PolicyResult.DEGRADE.value: "⬇️ 需要降级执行",
            PolicyResult.REJECT.value: "❌ 拒绝执行"
        }
        lines.append(f"【决策】{result_map.get(policy_output.policy_result, policy_output.policy_result)}")
        
        # 2. 为什么能做 / 不能做
        lines.append(f"【原因】{policy_output.policy_reason}")
        
        # 3. 不能直接做时该怎么降级
        if policy_output.policy_result != PolicyResult.AUTO_EXECUTE.value:
            if policy_output.fallback_action:
                fallback_map = {
                    FallbackAction.RETRY_LATER.value: "稍后重试",
                    FallbackAction.USE_BACKUP_HANDLER.value: "使用备用处理器",
                    FallbackAction.SWITCH_TO_READONLY.value: "切换到只读模式",
                    FallbackAction.REQUIRE_HUMAN.value: "需要人工介入"
                }
                lines.append(f"【降级】{fallback_map.get(policy_output.fallback_action, policy_output.fallback_action)}")
            else:
                lines.append("【降级】无降级方案")
        
        # 4. 失败后下一步走哪条 fallback
        if policy_output.fallback_action:
            lines.append(f"【Fallback】{policy_output.fallback_action}")
        else:
            lines.append("【Fallback】无")
        
        return '\n'.join(lines)


def main():
    """测试入口"""
    engine = PolicyDecisionEngine()
    
    # 测试用例：低风险监控任务
    policy_input = PolicyInput(
        operation_type="monitor",
        handler_type="skill",
        handler_name="aios-health-monitor",
        risk_level="low",
        system_health="healthy",
        known_failure_patterns=[],
        user_policy={},
        router_decision={"confidence": 99.4, "fallback_handlers": []}
    )
    
    output = engine.decide(policy_input)
    print(engine.explain_decision(output))


if __name__ == "__main__":
    main()
