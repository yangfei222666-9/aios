#!/usr/bin/env python3
"""
Error Pattern Learner Agent
从失败任务中学习错误模式，自动生成修复策略
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Any

class ErrorPatternLearner:
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.patterns_file = self.data_dir / "error_patterns.json"
        self.strategies_file = self.data_dir / "fix_strategies.json"
        self.load_patterns()
        
    def load_patterns(self):
        """加载已知的错误模式"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                self.patterns = json.load(f)
        else:
            self.patterns = {
                "patterns": [],
                "last_updated": None
            }
            
        if self.strategies_file.exists():
            with open(self.strategies_file, 'r', encoding='utf-8') as f:
                self.strategies = json.load(f)
        else:
            self.strategies = {
                "strategies": [],
                "last_updated": None
            }
    
    def analyze_failed_tasks(self) -> Dict[str, Any]:
        """分析失败任务，提取错误模式"""
        task_queue = self.data_dir / "task_queue.jsonl"
        if not task_queue.exists():
            return {"error": "task_queue.jsonl not found"}
        
        failed_tasks = []
        with open(task_queue, 'r', encoding='utf-8') as f:
            for line in f:
                task = json.loads(line)
                if task.get('status') == 'failed':
                    failed_tasks.append(task)
        
        if not failed_tasks:
            return {
                "status": "success",
                "message": "No failed tasks found",
                "failed_count": 0
            }
        
        # 提取错误模式
        error_types = Counter()
        error_messages = []
        agent_failures = Counter()
        
        for task in failed_tasks:
            result = task.get('result', {})
            error = result.get('error', '')
            agent = result.get('agent', 'unknown')
            
            # 分类错误类型
            error_type = self._classify_error(error)
            error_types[error_type] += 1
            error_messages.append({
                "task_id": task['id'],
                "type": error_type,
                "message": error,
                "agent": agent
            })
            agent_failures[agent] += 1
        
        # 生成新模式
        new_patterns = []
        for error_type, count in error_types.most_common():
            if count >= 2:  # 至少出现2次才算模式
                pattern = {
                    "type": error_type,
                    "count": count,
                    "first_seen": datetime.now().isoformat(),
                    "examples": [msg for msg in error_messages if msg['type'] == error_type][:3]
                }
                new_patterns.append(pattern)
        
        # 保存模式
        self.patterns["patterns"].extend(new_patterns)
        self.patterns["last_updated"] = datetime.now().isoformat()
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "failed_count": len(failed_tasks),
            "error_types": dict(error_types),
            "agent_failures": dict(agent_failures),
            "new_patterns": len(new_patterns),
            "patterns_file": str(self.patterns_file)
        }
    
    def _classify_error(self, error: str) -> str:
        """分类错误类型"""
        error_lower = error.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return 'timeout'
        elif 'keyerror' in error_lower or 'key error' in error_lower:
            return 'missing_key'
        elif 'typeerror' in error_lower or 'type error' in error_lower:
            return 'type_mismatch'
        elif 'valueerror' in error_lower or 'value error' in error_lower:
            return 'invalid_value'
        elif 'filenotfound' in error_lower or 'no such file' in error_lower:
            return 'file_not_found'
        elif 'permission' in error_lower or 'access denied' in error_lower:
            return 'permission_denied'
        elif 'connection' in error_lower or 'network' in error_lower:
            return 'network_error'
        elif 'memory' in error_lower or 'out of memory' in error_lower:
            return 'memory_error'
        elif 'syntax' in error_lower or 'syntaxerror' in error_lower:
            return 'syntax_error'
        elif 'import' in error_lower or 'module' in error_lower:
            return 'import_error'
        else:
            return 'unknown'
    
    def generate_fix_strategies(self) -> Dict[str, Any]:
        """根据错误模式生成修复策略"""
        if not self.patterns["patterns"]:
            return {
                "status": "success",
                "message": "No patterns to generate strategies from",
                "strategies_count": 0
            }
        
        # 预定义的修复策略
        strategy_templates = {
            "timeout": {
                "strategy": "increase_timeout",
                "description": "增加任务超时时间",
                "actions": [
                    "将超时时间从 60s 增加到 120s",
                    "对于复杂任务，考虑拆分为子任务"
                ]
            },
            "missing_key": {
                "strategy": "validate_input",
                "description": "验证输入数据完整性",
                "actions": [
                    "在任务执行前验证必需字段",
                    "为缺失字段提供默认值",
                    "添加数据 Schema 验证"
                ]
            },
            "type_mismatch": {
                "strategy": "type_conversion",
                "description": "自动类型转换",
                "actions": [
                    "添加类型检查和转换逻辑",
                    "使用 Pydantic 进行数据验证"
                ]
            },
            "file_not_found": {
                "strategy": "path_validation",
                "description": "验证文件路径",
                "actions": [
                    "在执行前检查文件是否存在",
                    "提供更清晰的错误提示",
                    "自动创建必需的目录"
                ]
            },
            "network_error": {
                "strategy": "retry_with_backoff",
                "description": "重试机制",
                "actions": [
                    "实现指数退避重试",
                    "最多重试 3 次",
                    "添加网络连接检查"
                ]
            },
            "import_error": {
                "strategy": "dependency_check",
                "description": "依赖检查",
                "actions": [
                    "在启动时检查依赖",
                    "提供依赖安装指南",
                    "使用虚拟环境隔离依赖"
                ]
            }
        }
        
        new_strategies = []
        for pattern in self.patterns["patterns"]:
            error_type = pattern["type"]
            if error_type in strategy_templates:
                strategy = strategy_templates[error_type].copy()
                strategy["pattern_type"] = error_type
                strategy["occurrences"] = pattern["count"]
                strategy["created_at"] = datetime.now().isoformat()
                new_strategies.append(strategy)
        
        # 保存策略
        self.strategies["strategies"] = new_strategies
        self.strategies["last_updated"] = datetime.now().isoformat()
        with open(self.strategies_file, 'w', encoding='utf-8') as f:
            json.dump(self.strategies, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "strategies_count": len(new_strategies),
            "strategies": new_strategies,
            "strategies_file": str(self.strategies_file)
        }
    
    def get_fix_recommendation(self, error: str) -> Dict[str, Any]:
        """根据错误获取修复建议"""
        error_type = self._classify_error(error)
        
        # 查找匹配的策略
        matching_strategies = [
            s for s in self.strategies.get("strategies", [])
            if s.get("pattern_type") == error_type
        ]
        
        if matching_strategies:
            return {
                "status": "success",
                "error_type": error_type,
                "recommendation": matching_strategies[0]
            }
        else:
            return {
                "status": "no_match",
                "error_type": error_type,
                "message": "No fix strategy found for this error type"
            }

def main():
    import sys
    
    learner = ErrorPatternLearner()
    
    if len(sys.argv) < 2:
        print("Usage: python error_pattern_learner.py [analyze|generate|recommend]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "analyze":
        result = learner.analyze_failed_tasks()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "generate":
        result = learner.generate_fix_strategies()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "recommend":
        if len(sys.argv) < 3:
            print("Usage: python error_pattern_learner.py recommend <error_message>")
            sys.exit(1)
        error = sys.argv[2]
        result = learner.get_fix_recommendation(error)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
