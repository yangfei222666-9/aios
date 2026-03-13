"""
mouse_tracker.py - 鼠标轨迹 + 点击采集

存 (x, y, t) 三元组，支持：
- 停留判断（速度 < 阈值）
- 振荡判断（来回移动）
- 点击记录（含前台 app + 窗口标题）
"""
import time
import threading
from collections import deque


class MouseTracker:
    def __init__(self, history_size: int = 100):
        self.positions: deque = deque(maxlen=history_size)   # (x, y, t)
        self.clicks: deque = deque(maxlen=history_size)      # (x, y, t, button, app, title)
        self._lock = threading.Lock()
        self._current_app = ''
        self._current_title = ''

    def update_context(self, app: str, title: str):
        self._current_app = app
        self._current_title = title

    def on_move(self, x: int, y: int):
        with self._lock:
            self.positions.append((x, y, time.time()))

    def on_click(self, x: int, y: int, button: str, pressed: bool):
        if not pressed:
            return
        with self._lock:
            self.clicks.append((x, y, time.time(), button,
                                 self._current_app, self._current_title))

    def get_recent(self, seconds: float = 10.0) -> dict:
        now = time.time()
        with self._lock:
            pos = [(x, y, t) for x, y, t in self.positions if now - t <= seconds]
            clk = [(x, y, t, b, a, ti) for x, y, t, b, a, ti in self.clicks if now - t <= seconds]

        is_idle = len(pos) < 5
        avg_speed = _avg_speed(pos)

        return {
            'positions': pos,
            'clicks': clk,
            'is_idle': is_idle,
            'avg_speed': avg_speed,
        }


def _avg_speed(positions: list) -> float:
    """像素/秒"""
    if len(positions) < 2:
        return 0.0
    total_dist = 0.0
    for i in range(1, len(positions)):
        x0, y0, t0 = positions[i - 1]
        x1, y1, t1 = positions[i]
        dt = t1 - t0
        if dt > 0:
            dist = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            total_dist += dist / dt
    return total_dist / (len(positions) - 1)
