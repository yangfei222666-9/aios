"""
Execution History - 执行历史持久化
职责：记录所有执行历史，支持查询和分析
"""

import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class ExecutionHistory:
    """执行历史管理"""
    
    def __init__(self, history_file: str = "execution_history.jsonl"):
        self.history_file = Path(history_file)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保历史文件存在"""
        if not self.history_file.exists():
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history_file.touch()
    
    def save(self, execution: Dict[str, Any]) -> None:
        """
        保存执行记录
        
        Args:
            execution: 执行记录
        """
        # 添加时间戳
        if 'timestamp' not in execution:
            execution['timestamp'] = time.time()
        
        # 添加日期（便于查询）
        if 'date' not in execution:
            execution['date'] = datetime.fromtimestamp(execution['timestamp']).strftime('%Y-%m-%d')
        
        # 添加唯一 ID
        if 'id' not in execution:
            execution['id'] = f"{int(execution['timestamp'] * 1000)}"
        
        # 追加到文件
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(execution, ensure_ascii=False) + '\n')
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的执行记录
        
        Args:
            limit: 返回数量
            
        Returns:
            执行记录列表
        """
        if not self.history_file.exists():
            return []
        
        records = []
        with open(self.history_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except:
                        pass
        
        return list(reversed(records))  # 最新的在前
    
    def get_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        获取指定日期的执行记录
        
        Args:
            date: 日期（YYYY-MM-DD）
            
        Returns:
            执行记录列表
        """
        if not self.history_file.exists():
            return []
        
        records = []
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if record.get('date') == date:
                            records.append(record)
                    except:
                        pass
        
        return records
    
    def get_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取执行记录
        
        Args:
            execution_id: 执行 ID
            
        Returns:
            执行记录
        """
        if not self.history_file.exists():
            return None
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if record.get('id') == execution_id:
                            return record
                    except:
                        pass
        
        return None
    
    def search(
        self,
        user_input: Optional[str] = None,
        success: Optional[bool] = None,
        agent: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        搜索执行记录
        
        Args:
            user_input: 用户输入关键词
            success: 是否成功
            agent: Agent 名称
            date_from: 开始日期（YYYY-MM-DD）
            date_to: 结束日期（YYYY-MM-DD）
            limit: 返回数量
            
        Returns:
            执行记录列表
        """
        if not self.history_file.exists():
            return []
        
        records = []
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        
                        # 过滤条件
                        if user_input and user_input.lower() not in record.get('user_input', '').lower():
                            continue
                        
                        if success is not None and record.get('success') != success:
                            continue
                        
                        if agent:
                            plan = record.get('plan', {})
                            steps = plan.get('steps', [])
                            if not any(agent in step.get('agent', '') for step in steps):
                                continue
                        
                        if date_from and record.get('date', '') < date_from:
                            continue
                        
                        if date_to and record.get('date', '') > date_to:
                            continue
                        
                        records.append(record)
                        
                        if len(records) >= limit:
                            break
                    except:
                        pass
        
        return list(reversed(records))  # 最新的在前
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        if not self.history_file.exists():
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "total_steps": 0
            }
        
        total = 0
        success = 0
        failed = 0
        total_duration = 0
        total_steps = 0
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        total += 1
                        
                        if record.get('success'):
                            success += 1
                        else:
                            failed += 1
                        
                        total_duration += record.get('duration', 0)
                        
                        result = record.get('result', {})
                        workflow_result = result.get('workflow_result', {})
                        total_steps += workflow_result.get('steps_executed', 0)
                    except:
                        pass
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": round(success / total * 100, 1) if total > 0 else 0,
            "avg_duration": round(total_duration / total, 2) if total > 0 else 0,
            "total_steps": total_steps
        }


# 测试代码
if __name__ == "__main__":
    history = ExecutionHistory("test_execution_history.jsonl")
    
    # 测试保存
    print("=== 测试 1: 保存执行记录 ===")
    execution1 = {
        "user_input": "检查系统健康",
        "plan": {
            "intent": "health_check",
            "steps": [{"agent": "aios_health_check"}]
        },
        "result": {
            "success": True,
            "workflow_result": {
                "steps_executed": 1,
                "steps_failed": 0
            }
        },
        "success": True,
        "duration": 0.05
    }
    history.save(execution1)
    print("[OK] 保存成功")
    
    # 测试获取最近记录
    print("\n=== 测试 2: 获取最近记录 ===")
    recent = history.get_recent(limit=5)
    print(f"最近 {len(recent)} 条记录:")
    for record in recent:
        print(f"  - {record['user_input']} (成功: {record['success']}, 耗时: {record['duration']}s)")
    
    # 测试统计
    print("\n=== 测试 3: 统计信息 ===")
    stats = history.get_stats()
    print(f"总执行次数: {stats['total']}")
    print(f"成功次数: {stats['success']}")
    print(f"失败次数: {stats['failed']}")
    print(f"成功率: {stats['success_rate']}%")
    print(f"平均耗时: {stats['avg_duration']}s")
    print(f"总步骤数: {stats['total_steps']}")
    
    # 测试搜索
    print("\n=== 测试 4: 搜索 ===")
    results = history.search(user_input="健康", success=True)
    print(f"搜索结果: {len(results)} 条")
    
    # 清理测试文件
    import os
    if os.path.exists("test_execution_history.jsonl"):
        os.remove("test_execution_history.jsonl")
        print("\n[OK] 测试文件已清理")
