"""
event_store.py - 事件存储

用 JSONL 追加写，简单可靠，方便后续分析。
"""
import json
import os
import time
from pathlib import Path


class EventStore:
    def __init__(self, data_dir: str = 'data/events'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save(self, event: dict):
        """追加写入当天的事件文件"""
        date_str = time.strftime('%Y-%m-%d')
        path = self.data_dir / f"events_{date_str}.jsonl"
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    def load_today(self) -> list[dict]:
        date_str = time.strftime('%Y-%m-%d')
        path = self.data_dir / f"events_{date_str}.jsonl"
        if not path.exists():
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f if line.strip()]
