# -*- coding: utf-8 -*-
"""
Dispatch Log Reader v1.0

作用：读取 dispatch_log.jsonl，提取中枢决策记录。

只关注 5 个字段：
- current_situation
- chosen_handler
- policy_result
- final_status
- fallback_action
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta


class DispatchLogReader:
    """dispatch_log.jsonl 读取器"""
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path(__file__).parent / "data" / "dispatch_log.jsonl"
    
    def read_recent(self, hours: float = 24.0) -> List[Dict[str, Any]]:
        """
        读取最近 N 小时的决策记录
        
        Args:
            hours: 时间窗口（小时）
            
        Returns:
            决策记录列表（只包含 5 个关键字段）
        """
        if not self.log_path.exists():
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        records = []
        
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    timestamp_str = entry.get('timestamp', '')
                    
                    # 解析时间戳
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        continue
                    
                    # 时间窗口过滤
                    if timestamp < cutoff:
                        continue
                    
                    # 提取 5 个关键字段
                    decision_record = entry.get('decision_record', {})
                    policy_result = decision_record.get('policy_result', {})
                    
                    record = {
                        'timestamp': timestamp_str,
                        'current_situation': decision_record.get('current_situation'),
                        'chosen_handler': decision_record.get('chosen_handler'),
                        'policy_result': policy_result.get('policy_result') if policy_result else None,
                        'final_status': decision_record.get('final_status'),
                        'fallback_action': policy_result.get('fallback_action') if policy_result else None,
                    }
                    
                    records.append(record)
                
                except json.JSONDecodeError:
                    continue
        
        return records
    
    def read_all(self) -> List[Dict[str, Any]]:
        """读取所有决策记录"""
        if not self.log_path.exists():
            return []
        
        records = []
        
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    decision_record = entry.get('decision_record', {})
                    policy_result = decision_record.get('policy_result', {})
                    
                    record = {
                        'timestamp': entry.get('timestamp'),
                        'current_situation': decision_record.get('current_situation'),
                        'chosen_handler': decision_record.get('chosen_handler'),
                        'policy_result': policy_result.get('policy_result') if policy_result else None,
                        'final_status': decision_record.get('final_status'),
                        'fallback_action': policy_result.get('fallback_action') if policy_result else None,
                    }
                    
                    records.append(record)
                
                except json.JSONDecodeError:
                    continue
        
        return records
    
    def count_total(self) -> int:
        """统计总记录数"""
        if not self.log_path.exists():
            return 0
        
        count = 0
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    count += 1
        
        return count


def main():
    """测试入口"""
    reader = DispatchLogReader()
    
    print(f"Total records: {reader.count_total()}")
    print()
    
    recent = reader.read_recent(hours=24.0)
    print(f"Recent 24h: {len(recent)} records")
    
    if recent:
        print("\nLast 3 records:")
        for r in recent[-3:]:
            print(f"  [{r['timestamp']}]")
            print(f"    situation: {r['current_situation']}")
            print(f"    handler: {r['chosen_handler']}")
            print(f"    policy: {r['policy_result']}")
            print(f"    status: {r['final_status']}")
            print(f"    fallback: {r['fallback_action']}")
            print()


if __name__ == "__main__":
    main()
