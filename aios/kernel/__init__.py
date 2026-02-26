"""
AIOS Kernel - The operating system core.

The kernel manages system resources and provides services to agents
through the System Call interface. Agents never access kernel internals
directly; they go through aios.syscall.

Components:
- EventBus:   event routing and persistence
- Scheduler:  priority queue task scheduling
- Reactor:    automatic fault detection and repair
- Queues:     resource queues (LLM, Memory, Storage)
- ScoreEngine: system health scoring
- CircuitBreaker: fault isolation
"""

from core.event import Event, EventType, create_event
from core.event_bus import EventBus, get_event_bus
from core.scheduler_v2 import SchedulerV2, Task, Priority, start_scheduler
from core.queues import (
    LLMQueue,
    MemoryQueue,
    StorageQueue,
    ThreadPoolManager,
    QueueRequest,
    RequestPriority,
    SchedulingPolicy,
)
from core.queued_router import QueuedRouter, get_queued_router, queued_route_model

__all__ = [
    # Events
    "Event", "EventType", "create_event",
    "EventBus", "get_event_bus",
    # Scheduler
    "SchedulerV2", "Task", "Priority", "start_scheduler",
    # Queues
    "LLMQueue", "MemoryQueue", "StorageQueue", "ThreadPoolManager",
    "QueueRequest", "RequestPriority", "SchedulingPolicy",
    # Router
    "QueuedRouter", "get_queued_router", "queued_route_model",
]
