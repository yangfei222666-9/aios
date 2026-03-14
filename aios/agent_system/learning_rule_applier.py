"""
Learning Rule Applier - 应用学习规则到任务执行

核心能力：
1. 在任务执行前检查是否有匹配的规则
2. 应用规则调整任务参数（超时、重试、延迟等）
3. 记录规则应用效果
4. 根据效果调整规则置信度
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from paths import RULES_FILE, TASK_EXECUTIONS


@dataclass
class RuleApplication:
    """规则应用记录"""
    rule_id: str
    task_id: str
    applied_at: str
    action_taken: Dict[str, Any]
    result: Optional[str] = None  # success/failure/pending


class LearningRuleApplier:
    """学习规则应用器"""
    
    def __init__(self):
        self.rules_file = RULES_FILE
        self.executions_file = TASK_EXECUTIONS
        self.rules_cache = None
        self.cache_time = 0
        self.cache_ttl = 60  # 缓存60秒
    
    def load_rules(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """加载规则（带缓存）"""
        now = time.time()
        
        if not force_reload and self.rules_cache and (now - self.cache_time) < self.cache_ttl:
            return self.rules_cache
        
        if not self.rules_file.exists():
            return []
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('rules', [])
                # 只返回启用的规则
                enabled_rules = [r for r in rules if r.get('enabled', True)]
                self.rules_cache = enabled_rules
                self.cache_time = now
                return enabled_rules
        except (json.JSONDecodeError, IOError):
            return []
    
    def find_matching_rules(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找匹配的规则"""
        rules = self.load_rules()
        matching = []
        
        for rule in rules:
            if self._rule_matches_task(rule, task):
                matching.append(rule)
        
        return sorted(matching, key=lambda r: r.get('confidence', 0), reverse=True)
    
    def _rule_matches_task(self, rule: Dict[str, Any], task: Dict[str, Any]) -> bool:
        """检查规则是否匹配任务"""
        trigger = rule.get('trigger_condition', {})
        
        # 检查错误类型
        if 'error_type' in trigger:
            if task.get('error_type') != trigger['error_type']:
                return False
        
        # 检查错误模式
        if 'error_pattern' in trigger:
            error_msg = task.get('error_message', '')
            if trigger['error_pattern'] not in error_msg:
                return False
        
        # 检查任务类型
        if 'task_type' in trigger:
            if task.get('task_type') != trigger['task_type']:
                return False
        
        return True
    
    def apply_rule(self, rule: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """应用规则到任务"""
        action = rule.get('action', {})
        action_type = action.get('type')
        
        modified_task = task.copy()
        
        if action_type == 'increase_timeout':
            current_timeout = modified_task.get('timeout', 60)
            multiplier = action.get('multiplier', 2.0)
            max_timeout = action.get('max_timeout', 300)
            new_timeout = min(current_timeout * multiplier, max_timeout)
            modified_task['timeout'] = new_timeout
            modified_task['_rule_applied'] = {
                'rule_id': rule['rule_id'],
                'action': 'increase_timeout',
                'old_timeout': current_timeout,
                'new_timeout': new_timeout
            }
        
        elif action_type == 'adjust_retry':
            max_retries = action.get('max_retries', 5)
            backoff_multiplier = action.get('backoff_multiplier', 2.0)
            modified_task['max_retries'] = max_retries
            modified_task['backoff_multiplier'] = backoff_multiplier
            modified_task['_rule_applied'] = {
                'rule_id': rule['rule_id'],
                'action': 'adjust_retry',
                'max_retries': max_retries,
                'backoff_multiplier': backoff_multiplier
            }
        
        elif action_type == 'add_delay':
            delay_seconds = action.get('delay_seconds', 60)
            modified_task['pre_execution_delay'] = delay_seconds
            modified_task['_rule_applied'] = {
                'rule_id': rule['rule_id'],
                'action': 'add_delay',
                'delay_seconds': delay_seconds
            }
        
        elif action_type == 'add_dependency_check':
            modified_task['check_dependencies'] = True
            modified_task['_rule_applied'] = {
                'rule_id': rule['rule_id'],
                'action': 'add_dependency_check'
            }
        
        return modified_task
    
    def record_application(self, rule_id: str, task_id: str, action: Dict[str, Any], result: str):
        """记录规则应用结果"""
        rules = self.load_rules(force_reload=True)
        
        for rule in rules:
            if rule['rule_id'] == rule_id:
                rule['applied_count'] = rule.get('applied_count', 0) + 1
                
                if result == 'success':
                    rule['success_count'] = rule.get('success_count', 0) + 1
                elif result == 'failure':
                    rule['failure_count'] = rule.get('failure_count', 0) + 1
                
                # 更新置信度
                total = rule['applied_count']
                success = rule['success_count']
                if total > 0:
                    rule['confidence'] = success / total
                
                # 如果失败率过高，禁用规则
                if total >= 10 and rule['confidence'] < 0.3:
                    rule['enabled'] = False
                    print(f"⚠️ 规则 {rule_id} 失败率过高，已自动禁用")
                
                break
        
        # 保存更新后的规则
        self._save_rules(rules)
    
    def _save_rules(self, rules: List[Dict[str, Any]]):
        """保存规则"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump({
                'rules': rules,
                'metadata': {
                    'last_updated': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    'total_rules': len(rules)
                }
            }, f, indent=2, ensure_ascii=False)
        
        # 清除缓存
        self.rules_cache = None
    
    def process_task_with_rules(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务并应用规则"""
        matching_rules = self.find_matching_rules(task)
        
        if not matching_rules:
            return task
        
        # 应用置信度最高的规则
        best_rule = matching_rules[0]
        print(f"📋 应用规则: {best_rule['name']} (置信度: {best_rule.get('confidence', 0):.2f})")
        
        modified_task = self.apply_rule(best_rule, task)
        return modified_task


def main():
    """测试规则应用"""
    applier = LearningRuleApplier()
    
    # 测试任务
    test_task = {
        'task_id': 'test-123',
        'task_type': 'code',
        'error_type': 'timeout',
        'error_message': 'Task timed out after 60 seconds',
        'timeout': 60
    }
    
    print("原始任务:")
    print(json.dumps(test_task, indent=2, ensure_ascii=False))
    
    print("\n查找匹配规则...")
    matching = applier.find_matching_rules(test_task)
    print(f"找到 {len(matching)} 条匹配规则")
    
    if matching:
        print("\n应用规则...")
        modified = applier.process_task_with_rules(test_task)
        print("\n修改后的任务:")
        print(json.dumps(modified, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
