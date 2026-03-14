"""
Learning Rule Extractor - 从失败事件中自动提炼可复用规则

核心能力：
1. 从 task_executions 中识别失败模式
2. 分析失败原因和上下文
3. 生成可执行的规则（if-then 格式）
4. 自动应用规则到后续任务

设计原则：
- 规则必须可验证（有明确的触发条件和预期结果）
- 规则必须可回滚（保留原始状态）
- 规则必须有置信度（基于样本数量和成功率）
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict

from paths import TASK_EXECUTIONS, LESSONS_FILE, RULES_FILE


@dataclass
class FailurePattern:
    """失败模式"""
    pattern_id: str
    error_type: str
    error_message_pattern: str
    occurrence_count: int
    affected_tasks: List[str]
    first_seen: str
    last_seen: str
    confidence: float  # 0.0-1.0


@dataclass
class LearningRule:
    """学习规则"""
    rule_id: str
    name: str
    description: str
    trigger_condition: Dict[str, Any]  # 触发条件
    action: Dict[str, Any]  # 执行动作
    confidence: float
    created_at: str
    applied_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    enabled: bool = True


class LearningRuleExtractor:
    """学习规则提取器"""
    
    def __init__(self):
        self.executions_file = TASK_EXECUTIONS
        self.lessons_file = LESSONS_FILE
        self.rules_file = RULES_FILE
        
    def extract_failure_patterns(self, min_occurrences: int = 2) -> List[FailurePattern]:
        """提取失败模式"""
        if not self.executions_file.exists():
            return []
        
        # 读取所有执行记录
        executions = []
        with open(self.executions_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    executions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        # 筛选失败记录
        failures = [e for e in executions if e.get('status') in ['failed', 'permanently_failed']]
        
        # 按错误类型分组
        error_groups = defaultdict(list)
        for failure in failures:
            error_type = failure.get('error_type', 'unknown')
            error_msg = failure.get('error_message', '')
            key = f"{error_type}:{self._normalize_error_message(error_msg)}"
            error_groups[key].append(failure)
        
        # 生成失败模式
        patterns = []
        for key, group in error_groups.items():
            if len(group) >= min_occurrences:
                error_type, error_pattern = key.split(':', 1)
                pattern = FailurePattern(
                    pattern_id=f"pattern_{hash(key) & 0xFFFFFFFF:08x}",
                    error_type=error_type,
                    error_message_pattern=error_pattern,
                    occurrence_count=len(group),
                    affected_tasks=[e.get('task_id', 'unknown') for e in group],
                    first_seen=min(e.get('started_at', '') for e in group),
                    last_seen=max(e.get('completed_at', e.get('started_at', '')) for e in group),
                    confidence=min(1.0, len(group) / 10.0)  # 10次以上置信度为1.0
                )
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.occurrence_count, reverse=True)
    
    def _normalize_error_message(self, msg: str) -> str:
        """归一化错误消息（去除变化部分）"""
        # 移除数字、路径、时间戳等变化部分
        import re
        msg = re.sub(r'\d+', 'N', msg)  # 数字 -> N
        msg = re.sub(r'[A-Z]:\\[^\s]+', 'PATH', msg)  # Windows路径
        msg = re.sub(r'/[^\s]+', 'PATH', msg)  # Unix路径
        msg = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', msg)  # 日期
        return msg[:100]  # 限制长度
    
    def generate_rules_from_patterns(self, patterns: List[FailurePattern]) -> List[LearningRule]:
        """从失败模式生成规则"""
        rules = []
        
        for pattern in patterns:
            # 根据错误类型生成不同的规则
            if pattern.error_type == 'timeout':
                rule = self._create_timeout_rule(pattern)
            elif pattern.error_type == 'dependency_missing':
                rule = self._create_dependency_rule(pattern)
            elif pattern.error_type == 'rate_limit':
                rule = self._create_rate_limit_rule(pattern)
            else:
                rule = self._create_generic_retry_rule(pattern)
            
            if rule:
                rules.append(rule)
        
        return rules
    
    def _create_timeout_rule(self, pattern: FailurePattern) -> Optional[LearningRule]:
        """创建超时规则"""
        return LearningRule(
            rule_id=f"rule_timeout_{pattern.pattern_id}",
            name=f"增加超时时间 - {pattern.error_type}",
            description=f"检测到 {pattern.occurrence_count} 次超时失败，自动增加超时时间",
            trigger_condition={
                "error_type": "timeout",
                "error_pattern": pattern.error_message_pattern
            },
            action={
                "type": "increase_timeout",
                "multiplier": 2.0,
                "max_timeout": 300
            },
            confidence=pattern.confidence,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
    
    def _create_dependency_rule(self, pattern: FailurePattern) -> Optional[LearningRule]:
        """创建依赖检查规则"""
        return LearningRule(
            rule_id=f"rule_dependency_{pattern.pattern_id}",
            name=f"依赖检查 - {pattern.error_type}",
            description=f"检测到 {pattern.occurrence_count} 次依赖缺失，添加前置检查",
            trigger_condition={
                "error_type": "dependency_missing",
                "error_pattern": pattern.error_message_pattern
            },
            action={
                "type": "add_dependency_check",
                "check_before_execution": True
            },
            confidence=pattern.confidence,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
    
    def _create_rate_limit_rule(self, pattern: FailurePattern) -> Optional[LearningRule]:
        """创建限流规则"""
        return LearningRule(
            rule_id=f"rule_ratelimit_{pattern.pattern_id}",
            name=f"限流保护 - {pattern.error_type}",
            description=f"检测到 {pattern.occurrence_count} 次限流，添加延迟和重试",
            trigger_condition={
                "error_type": "rate_limit",
                "error_pattern": pattern.error_message_pattern
            },
            action={
                "type": "add_delay",
                "delay_seconds": 60,
                "exponential_backoff": True
            },
            confidence=pattern.confidence,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
    
    def _create_generic_retry_rule(self, pattern: FailurePattern) -> Optional[LearningRule]:
        """创建通用重试规则"""
        return LearningRule(
            rule_id=f"rule_retry_{pattern.pattern_id}",
            name=f"智能重试 - {pattern.error_type}",
            description=f"检测到 {pattern.occurrence_count} 次失败，调整重试策略",
            trigger_condition={
                "error_type": pattern.error_type,
                "error_pattern": pattern.error_message_pattern
            },
            action={
                "type": "adjust_retry",
                "max_retries": 5,
                "backoff_multiplier": 2.0
            },
            confidence=pattern.confidence,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
    
    def save_rules(self, rules: List[LearningRule]) -> None:
        """保存规则到文件"""
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取现有规则
        existing_rules = {}
        if self.rules_file.exists():
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    existing_rules = {r['rule_id']: r for r in data.get('rules', [])}
                except json.JSONDecodeError:
                    pass
        
        # 合并新规则（保留现有规则的统计数据）
        for rule in rules:
            if rule.rule_id in existing_rules:
                old_rule = existing_rules[rule.rule_id]
                rule.applied_count = old_rule.get('applied_count', 0)
                rule.success_count = old_rule.get('success_count', 0)
                rule.failure_count = old_rule.get('failure_count', 0)
                rule.enabled = old_rule.get('enabled', True)
            existing_rules[rule.rule_id] = asdict(rule)
        
        # 写入文件
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump({
                'rules': list(existing_rules.values()),
                'metadata': {
                    'last_updated': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    'total_rules': len(existing_rules)
                }
            }, f, indent=2, ensure_ascii=False)
    
    def run_extraction(self) -> Dict[str, Any]:
        """运行完整的规则提取流程"""
        print("🔍 开始提取失败模式...")
        patterns = self.extract_failure_patterns(min_occurrences=2)
        print(f"✅ 发现 {len(patterns)} 个失败模式")
        
        if not patterns:
            return {
                'status': 'no_patterns',
                'patterns_found': 0,
                'rules_generated': 0
            }
        
        print("\n📋 失败模式详情:")
        for p in patterns[:5]:  # 只显示前5个
            print(f"  - {p.error_type}: {p.occurrence_count} 次 (置信度: {p.confidence:.2f})")
        
        print("\n🧠 生成学习规则...")
        rules = self.generate_rules_from_patterns(patterns)
        print(f"✅ 生成 {len(rules)} 条规则")
        
        print("\n💾 保存规则...")
        self.save_rules(rules)
        print(f"✅ 规则已保存到 {self.rules_file}")
        
        return {
            'status': 'success',
            'patterns_found': len(patterns),
            'rules_generated': len(rules),
            'rules': [asdict(r) for r in rules]
        }


def main():
    """主函数"""
    extractor = LearningRuleExtractor()
    result = extractor.run_extraction()
    
    print("\n" + "="*60)
    print(f"📊 提取结果: {result['status']}")
    print(f"   失败模式: {result['patterns_found']}")
    print(f"   生成规则: {result['rules_generated']}")
    print("="*60)


if __name__ == '__main__':
    main()
