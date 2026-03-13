"""
trigger_handler.py - 触发事件处理

流程：
  触发 → 仆（豆包 1.6 Flash）看图 → 主（豆包 2.0 Lite）判断 → 通知 / 入库

每种触发类型有独立的 prompt 和后处理逻辑。
"""
import time


SERVANT_PROMPTS = {
    'reading_report': (
        "这张截图是一个报告/分析页面吗？"
        "请返回 JSON：{\"is_report\": bool, \"title\": str, \"key_findings\": [str], \"page_type\": str}"
    ),
    'terminal_error_maybe': (
        "这张截图里有错误信息吗？"
        "请返回 JSON：{\"has_error\": bool, \"error_type\": str, \"key_line\": str, \"language\": str}"
    ),
    'stuck_on_same_window': (
        "这张截图显示的是什么界面？用户可能在做什么？"
        "请返回 JSON：{\"page_type\": str, \"possible_action\": str, \"looks_stuck\": bool}"
    ),
}

MASTER_PROMPTS = {
    'reading_report': (
        "用户正在看一份报告，仆的分析结果如下：{servant_result}\n"
        "请判断：是否需要主动提醒用户？如果需要，提醒什么？"
        "返回 JSON：{\"should_notify\": bool, \"message\": str, \"reason\": str}"
    ),
    'terminal_error_maybe': (
        "用户终端可能有报错，仆的分析结果如下：{servant_result}\n"
        "请判断：这个错误是否需要关注？有没有明显的修复建议？"
        "返回 JSON：{\"should_notify\": bool, \"message\": str, \"fix_hint\": str}"
    ),
    'stuck_on_same_window': (
        "用户可能卡住了，仆的分析结果如下：{servant_result}\n"
        "请判断：是否需要主动询问用户？"
        "返回 JSON：{\"should_notify\": bool, \"message\": str}"
    ),
}


class TriggerHandler:
    def __init__(self, vision_client, notifier, event_store):
        self.vision = vision_client
        self.notifier = notifier
        self.store = event_store
        self._last_trigger_time: dict = {}  # type → last notify timestamp
        self._cooldown_sec = 120  # 同类触发冷却 2 分钟

    def handle(self, trigger: dict, capture: dict | None):
        trigger_type = trigger['type']

        # 冷却检查
        if self._is_cooling_down(trigger_type):
            return

        servant_result = {}
        master_result = {}

        if capture and capture.get('image_bytes'):
            # 仆：快速感知
            servant_prompt = SERVANT_PROMPTS.get(trigger_type, "描述这张截图")
            servant_result = self.vision.analyze(
                image_bytes=capture['image_bytes'],
                prompt=servant_prompt,
                role='servant'
            )

            # 主：深层判断
            master_prompt = MASTER_PROMPTS.get(trigger_type, "需要通知用户吗？").format(
                servant_result=servant_result
            )
            master_result = self.vision.analyze(
                image_bytes=capture['image_bytes'],
                prompt=master_prompt,
                role='master'
            )

        # 决定是否通知
        should_notify = master_result.get('should_notify', False)
        message = master_result.get('message', '')

        # 兜底：如果主没给出结论，用触发类型默认消息
        if not master_result and trigger_type == 'stuck_on_same_window':
            should_notify = True
            message = f"🤔 你在同一个窗口停留了 {trigger['context'].get('stuck_sec', '?')} 秒，需要帮助吗？"

        if should_notify and message:
            self.notifier.send(message)
            self._last_trigger_time[trigger_type] = time.time()

        # 入库
        self.store.save({
            'trigger': trigger,
            'servant_result': servant_result,
            'master_result': master_result,
            'notified': should_notify,
            'timestamp': time.time()
        })

    def _is_cooling_down(self, trigger_type: str) -> bool:
        last = self._last_trigger_time.get(trigger_type, 0)
        return (time.time() - last) < self._cooldown_sec
