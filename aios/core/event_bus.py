# aios/core/event_bus.py - 进程内事件总线 v0.1
"""
轻量级 pub/sub 事件总线，支持：
- 同步订阅/发布（当前进程内）
- 通配符订阅（sensor.* 匹配 sensor.file_change）
- 事件持久化到 JSONL（可选）
- 事件过滤器（按优先级/来源）

设计原则：
- 零外部依赖，纯 Python stdlib
- 不引入线程/异步，保持简单（OpenClaw 本身是单线程）
- 通过文件队列实现跨会话通信
"""
import json, time, fnmatch
from pathlib import Path
from typing import Callable, Optional

# 事件优先级
PRIORITY_LOW = 0
PRIORITY_NORMAL = 1
PRIORITY_HIGH = 2
PRIORITY_CRITICAL = 3

# 事件队列文件（跨会话通信）
QUEUE_DIR = Path(__file__).resolve().parent.parent / "events" / "queue"


class Event:
    __slots__ = ("topic", "payload", "priority", "ts", "source")

    def __init__(self, topic: str, payload: dict = None,
                 priority: int = PRIORITY_NORMAL, source: str = ""):
        self.topic = topic
        self.payload = payload or {}
        self.priority = priority
        self.ts = time.time()
        self.source = source

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "payload": self.payload,
            "priority": self.priority,
            "ts": self.ts,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        e = cls(d["topic"], d.get("payload", {}),
                d.get("priority", PRIORITY_NORMAL), d.get("source", ""))
        e.ts = d.get("ts", time.time())
        return e


class EventBus:
    """进程内事件总线 + 文件队列"""

    def __init__(self, persist: bool = True):
        self._subs: list[tuple[str, Callable, int]] = []  # (pattern, handler, min_priority)
        self._persist = persist
        self._history: list[Event] = []

    def subscribe(self, pattern: str, handler: Callable,
                  min_priority: int = PRIORITY_LOW):
        """订阅事件。pattern 支持通配符（如 sensor.*）"""
        self._subs.append((pattern, handler, min_priority))

    def unsubscribe(self, handler: Callable):
        self._subs = [(p, h, mp) for p, h, mp in self._subs if h is not handler]

    def publish(self, event: Event) -> int:
        """发布事件，返回触发的 handler 数量"""
        self._history.append(event)
        if self._persist:
            self._persist_event(event)

        triggered = 0
        for pattern, handler, min_pri in self._subs:
            if event.priority < min_pri:
                continue
            if fnmatch.fnmatch(event.topic, pattern):
                try:
                    handler(event)
                    triggered += 1
                except Exception as e:
                    # handler 异常不阻塞其他订阅者
                    self._persist_event(Event(
                        "bus.handler_error",
                        {"handler": handler.__name__, "error": str(e)[:200],
                         "original_topic": event.topic},
                        PRIORITY_HIGH, "event_bus"
                    ))
        return triggered

    def emit(self, topic: str, payload: dict = None,
             priority: int = PRIORITY_NORMAL, source: str = "") -> int:
        """便捷发布"""
        return self.publish(Event(topic, payload, priority, source))

    def _persist_event(self, event: Event):
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        path = QUEUE_DIR / f"{time.strftime('%Y-%m-%d')}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    # --- 跨会话队列 ---

    def enqueue(self, event: Event):
        """写入文件队列，供其他会话消费"""
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        path = QUEUE_DIR / "pending.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def drain_queue(self, limit: int = 20) -> list[Event]:
        """消费文件队列中的待处理事件"""
        path = QUEUE_DIR / "pending.jsonl"
        if not path.exists():
            return []

        lines = path.read_text(encoding="utf-8").splitlines()
        events = []
        remaining = []

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            if len(events) < limit:
                try:
                    events.append(Event.from_dict(json.loads(line)))
                except Exception:
                    continue
            else:
                remaining.append(line)

        # 写回未消费的
        if remaining:
            path.write_text("\n".join(remaining) + "\n", encoding="utf-8")
        else:
            path.unlink(missing_ok=True)

        return events

    def pending_count(self) -> int:
        path = QUEUE_DIR / "pending.jsonl"
        if not path.exists():
            return 0
        return sum(1 for l in path.read_text(encoding="utf-8").splitlines() if l.strip())

    def recent(self, limit: int = 10, topic_filter: str = None) -> list[dict]:
        """最近的事件（内存中）"""
        out = self._history[-limit * 3:]
        if topic_filter:
            out = [e for e in out if fnmatch.fnmatch(e.topic, topic_filter)]
        return [e.to_dict() for e in out[-limit:]]


# 全局单例
_bus: Optional[EventBus] = None

def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
