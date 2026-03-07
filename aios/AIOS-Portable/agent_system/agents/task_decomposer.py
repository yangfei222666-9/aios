#!/usr/bin/env python3
"""
Task Decomposer Agent
将复杂任务自动拆解为子任务
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class TaskDecomposer:
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.decomposition_rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """加载任务分解规则"""
        return {
            "code": {
                "keywords": ["重构", "实现", "开发", "编写", "修改"],
                "subtasks": [
                    {"type": "analysis", "description": "分析需求和现有代码"},
                    {"type": "code", "description": "编写/修改代码"},
                    {"type": "test", "description": "测试代码功能"},
                    {"type": "code", "description": "代码审查和优化"}
                ]
            },
            "analysis": {
                "keywords": ["分析", "调研", "研究", "评估"],
                "subtasks": [
                    {"type": "research", "description": "收集相关资料"},
                    {"type": "analysis", "description": "分析数据"},
                    {"type": "analysis", "description": "生成报告"}
                ]
            },
            "monitor": {
                "keywords": ["监控", "检查", "巡检", "诊断"],
                "subtasks": [
                    {"type": "monitor", "description": "收集数据"},
                    {"type": "analysis", "description": "分析数据"},
                    {"type": "analysis", "description": "生成报告"}
                ]
            },
            "research": {
                "keywords": ["搜索", "查找", "调研"],
                "subtasks": [
                    {"type": "research", "description": "搜索相关资料"},
                    {"type": "analysis", "description": "分析技术方案"},
                    {"type": "analysis", "description": "生成调研报告"}
                ]
            }
        }
    
    def should_decompose(self, task: Dict[str, Any]) -> bool:
        """判断任务是否需要分解"""
        description = task.get('description', '').lower()
        
        # 复杂度指标
        complexity_indicators = [
            len(description) > 50,  # 描述较长
            '并且' in description or 'and' in description.lower(),  # 包含多个步骤
            '然后' in description or 'then' in description.lower(),
            '最后' in description or 'finally' in description.lower(),
            description.count('，') > 2 or description.count(',') > 2,  # 多个逗号
        ]
        
        return sum(complexity_indicators) >= 2
    
    def decompose(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分解任务"""
        if not self.should_decompose(task):
            return {
                "status": "skip",
                "message": "Task is simple enough, no decomposition needed",
                "original_task": task
            }
        
        task_type = task.get('type', 'unknown')
        description = task.get('description', '')
        
        # 根据任务类型选择分解规则
        rule = self.decomposition_rules.get(task_type)
        
        if not rule:
            # 通用分解：按句子拆分
            subtasks = self._generic_decompose(task)
        else:
            # 使用预定义规则
            subtasks = self._rule_based_decompose(task, rule)
        
        return {
            "status": "success",
            "original_task": task,
            "subtasks": subtasks,
            "subtask_count": len(subtasks)
        }
    
    def _generic_decompose(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """通用分解策略：按句子拆分"""
        description = task.get('description', '')
        task_type = task.get('type', 'unknown')
        priority = task.get('priority', 'normal')
        
        # 按句子分割
        sentences = re.split(r'[，。；,;]', description)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        subtasks = []
        for i, sentence in enumerate(sentences):
            subtask = {
                "id": f"{task['id']}-sub{i+1}",
                "description": sentence,
                "type": task_type,
                "priority": priority,
                "parent_task": task['id'],
                "sequence": i + 1,
                "status": "pending",
                "created_at": datetime.now().timestamp()
            }
            subtasks.append(subtask)
        
        return subtasks
    
    def _rule_based_decompose(self, task: Dict[str, Any], rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于规则的分解"""
        description = task.get('description', '')
        priority = task.get('priority', 'normal')
        
        subtasks = []
        for i, subtask_template in enumerate(rule['subtasks']):
            subtask = {
                "id": f"{task['id']}-{subtask_template['type']}-{i+1}",
                "description": f"{subtask_template['description']}（{description}）",
                "type": subtask_template['type'],
                "priority": priority,
                "parent_task": task['id'],
                "sequence": i + 1,
                "status": "pending",
                "created_at": datetime.now().timestamp(),
                "metadata": {
                    "time_range": task.get('metadata', {}).get('time_range', 'today'),
                    "estimated_duration": task.get('metadata', {}).get('estimated_duration', 20) // len(rule['subtasks'])
                }
            }
            subtasks.append(subtask)
        
        return subtasks
    
    def save_subtasks(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """保存子任务到队列"""
        task_queue = self.data_dir / "task_queue.jsonl"
        
        with open(task_queue, 'a', encoding='utf-8') as f:
            for subtask in subtasks:
                f.write(json.dumps(subtask, ensure_ascii=False) + '\n')
        
        return {
            "status": "success",
            "saved_count": len(subtasks),
            "queue_file": str(task_queue)
        }

def main():
    import sys
    
    decomposer = TaskDecomposer()
    
    if len(sys.argv) < 2:
        print("Usage: python task_decomposer.py [decompose|check] <task_json>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "decompose":
        if len(sys.argv) < 3:
            print("Usage: python task_decomposer.py decompose <task_json>")
            sys.exit(1)
        
        task = json.loads(sys.argv[2])
        result = decomposer.decompose(task)
        
        if result["status"] == "success":
            # 保存子任务
            save_result = decomposer.save_subtasks(result["subtasks"])
            result["save_result"] = save_result
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "check":
        if len(sys.argv) < 3:
            print("Usage: python task_decomposer.py check <task_json>")
            sys.exit(1)
        
        task = json.loads(sys.argv[2])
        should_decompose = decomposer.should_decompose(task)
        
        print(json.dumps({
            "should_decompose": should_decompose,
            "task": task
        }, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
