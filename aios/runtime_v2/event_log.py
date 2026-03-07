"""
Event Log - Append-Only Event Storage

职责：
- 只做两件事：append_event() 和 read_events()
- 不做 filter / state / queue logic
- 每个 event 有 event_id（uuid4）

Event Schema:
{
    "event_id": "uuid4",
    "timestamp": "ISO8601",
    "event_type": "task_created|task_started|task_completed|task_failed|task_timeout",
    "task_id": "t123",
    "data": {...}
}
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class EventLog:
    def __init__(self, log_path: str = None):
        if log_path is None:
            log_path = Path(__file__).parent / "event_log.jsonl"
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果文件不存在，创建空文件
        if not self.log_path.exists():
            self.log_path.touch()
    
    def append_event(self, event_type: str, task_id: str, data: Dict[str, Any] = None) -> str:
        """
        追加一个 event 到 log
        
        Args:
            event_type: task_created|task_started|task_completed|task_failed|task_timeout
            task_id: 任务 ID
            data: 额外数据
        
        Returns:
            event_id
        """
        event_id = str(uuid.uuid4())
        event = {
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "task_id": task_id,
            "data": data or {}
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        return event_id
    
    def read_events(self) -> List[Dict[str, Any]]:
        """
        读取所有 events
        
        Returns:
            List of events（按时间顺序）
        """
        events = []
        if not self.log_path.exists():
            return events
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        return events


# 全局单例
_event_log = None

def get_event_log() -> EventLog:
    """获取全局 EventLog 实例"""
    global _event_log
    if _event_log is None:
        _event_log = EventLog()
    return _event_log
