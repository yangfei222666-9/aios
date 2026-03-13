"""
main.py - 桌面观察器主循环

Phase 1: 纯行为映射（采集 + 判断）
Phase 2: 触发后截图 → 仆多模态感知 → 主决策 → 通知

运行：
    python main.py
    python main.py --config config.local.json
"""
import argparse
import json
import sys
import time
import threading
from pathlib import Path

# 路径修正
sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.active_window import get_active_window
from src.collectors.mouse_tracker import MouseTracker
from src.collectors.keyboard_activity import KeyboardTracker
from src.collectors.window_capture import capture_active_window
from src.master.behavior_judge import BehaviorJudge
from src.master.trigger_handler import TriggerHandler
from src.vision.vision_client import VisionClient
from src.runtime.telegram_notify import TelegramNotifier
from src.learning.event_store import EventStore


def load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='桌面观察器')
    parser.add_argument('--config', default='config.json')
    args = parser.parse_args()

    config = load_config(args.config)
    poll_interval = config.get('collectors', {}).get('poll_interval_sec', 5)

    # 初始化组件
    mouse_tracker = MouseTracker(
        history_size=config.get('collectors', {}).get('mouse_history_size', 100)
    )
    keyboard_tracker = KeyboardTracker(
        history_size=config.get('collectors', {}).get('keyboard_history_size', 100)
    )
    behavior_judge = BehaviorJudge(config)
    vision_client = VisionClient(config.get('vision', {}))
    notifier = TelegramNotifier(
        bot_token=config.get('notifier', {}).get('telegram', {}).get('bot_token', ''),
        chat_id=config.get('notifier', {}).get('telegram', {}).get('chat_id', '')
    )
    event_store = EventStore()
    trigger_handler = TriggerHandler(vision_client, notifier, event_store)

    # 启动鼠标/键盘监听（后台线程）
    try:
        from pynput import mouse, keyboard

        mouse_listener = mouse.Listener(
            on_move=mouse_tracker.on_move,
            on_click=lambda x, y, btn, pressed: mouse_tracker.on_click(x, y, str(btn), pressed)
        )
        keyboard_listener = keyboard.Listener(
            on_press=keyboard_tracker.on_press
        )
        mouse_listener.start()
        keyboard_listener.start()
        print("✅ 鼠标/键盘监听已启动")
    except ImportError:
        print("⚠️  pynput 未安装，鼠标/键盘监听跳过（pip install pynput）")
        mouse_listener = None
        keyboard_listener = None

    print(f"🚀 桌面观察器已启动，轮询间隔 {poll_interval}s")
    print("   Ctrl+C 退出\n")

    try:
        while True:
            # 1. 采集
            aw = get_active_window()
            mouse_activity = mouse_tracker.get_recent(seconds=10)
            kb_count = keyboard_tracker.get_activity(aw.get('app', ''), seconds=10)

            # 同步上下文
            mouse_tracker.update_context(aw.get('app', ''), aw.get('window_title', ''))
            keyboard_tracker.update_current_app(aw.get('app', ''))

            # 2. 行为判断（不截图，只看信号）
            # 先用上次的 hash 判断，避免每轮都截图
            triggers = behavior_judge.judge(
                active_window=aw,
                mouse_activity=mouse_activity,
                keyboard_count=kb_count,
                window_hash=None  # Phase 1 先不截图
            )

            # 3. 有触发 → 截图 → 交给 handler
            if triggers:
                capture = capture_active_window()
                window_hash = capture['hash'] if capture else None

                # 用真实 hash 重新判断 stuck
                triggers = behavior_judge.judge(
                    active_window=aw,
                    mouse_activity=mouse_activity,
                    keyboard_count=kb_count,
                    window_hash=window_hash
                )

                for trigger in triggers:
                    print(f"  🔔 触发: {trigger['type']} (confidence={trigger['confidence']})")
                    trigger_handler.handle(trigger, capture)
            else:
                # 无触发时也更新 hash（用于 stuck 检测）
                capture = capture_active_window()
                if capture:
                    behavior_judge.judge(aw, mouse_activity, kb_count, capture['hash'])

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n正在停止...")
    finally:
        if mouse_listener:
            mouse_listener.stop()
        if keyboard_listener:
            keyboard_listener.stop()
        print("已停止。")


if __name__ == '__main__':
    main()
