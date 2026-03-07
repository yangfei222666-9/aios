"""
Runtime Runner - Shadow Loop

职责：
- 运行 dispatcher.tick() 循环
- 不做任何业务逻辑

运行模式：
- shadow mode（不影响现有系统）
- 每 5 秒 tick 一次
- 可以通过 Ctrl+C 停止
"""

import time
import signal
import sys

from .dispatcher import get_dispatcher
from .worker import get_worker


class RuntimeRunner:
    def __init__(self, tick_interval: int = 5):
        self.dispatcher = get_dispatcher()
        self.worker = get_worker()
        self.tick_interval = tick_interval
        self.running = False
    
    def start(self):
        """启动 runtime loop"""
        self.running = True
        
        # 注册信号处理（Ctrl+C 优雅退出）
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("[RUNTIME] Starting runtime loop...")
        print(f"[RUNTIME] Tick interval: {self.tick_interval}s")
        print("[RUNTIME] Press Ctrl+C to stop")
        print()
        
        tick_count = 0
        while self.running:
            tick_count += 1
            print(f"[RUNTIME] Tick #{tick_count}")
            
            # Dispatcher tick
            result = self.dispatcher.tick()
            print(f"  Pending: {result['pending']}")
            print(f"  Running: {result['running']}")
            print(f"  Spawned: {result['spawned']}")
            
            # 如果有 spawned 任务，立即执行（第一版同步执行）
            # 未来可以改成异步执行
            if result['spawned'] > 0:
                from .state import get_state
                state = get_state()
                running_tasks = state.list_running_tasks()
                
                for task in running_tasks:
                    # 只执行刚刚 spawned 的任务（last_event 是 task_started）
                    if task["last_event"]["event_type"] == "task_started":
                        self.worker.execute(task)
            
            print()
            time.sleep(self.tick_interval)
        
        print("[RUNTIME] Runtime loop stopped")
    
    def stop(self):
        """停止 runtime loop"""
        self.running = False
    
    def _signal_handler(self, signum, frame):
        """信号处理（Ctrl+C）"""
        print("\n[RUNTIME] Received stop signal, shutting down...")
        self.stop()
        sys.exit(0)


def run_runtime(tick_interval: int = 5):
    """启动 runtime（便捷函数）"""
    runner = RuntimeRunner(tick_interval=tick_interval)
    runner.start()


if __name__ == "__main__":
    # 直接运行：python -m aios.runtime_v2.runner
    run_runtime()
