"""
keyboard_activity.py - 键盘活跃度采集

按 app 维度记录，支持：
- 最近 N 秒按键数
- 当前 app 是否在"输入态"
"""
import time
import threading
from collections import defaultdict, deque


class KeyboardTracker:
    def __init__(self, history_size: int = 200):
        # {app_name: deque of timestamps}
        self._events: dict = defaultdict(lambda: deque(maxlen=history_size))
        self._current_app = ''
        self._lock = threading.Lock()

    def update_current_app(self, app: str):
        self._current_app = app

    def on_press(self, key):
        with self._lock:
            if self._current_app:
                self._events[self._current_app].append(time.time())

    def get_activity(self, app: str, seconds: float = 10.0) -> int:
        """返回指定 app 最近 N 秒的按键数"""
        now = time.time()
        with self._lock:
            events = self._events.get(app, deque())
            return sum(1 for t in events if now - t <= seconds)

    def is_typing(self, app: str, seconds: float = 10.0, threshold: int = 5) -> bool:
        return self.get_activity(app, seconds) >= threshold
