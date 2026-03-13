"""
behavior_judge.py - 行为模式判断

综合 4 个信号判断当前状态：
1. 鼠标停留
2. 键盘低活跃
3. 窗口标题命中关键词
4. 窗口 hash 静止时长

输出触发列表，每个触发带 type + confidence + context。
"""
import time


class BehaviorJudge:
    def __init__(self, config: dict):
        cfg = config.get('triggers', {})
        self._cfg_report = cfg.get('reading_report', {})
        self._cfg_terminal = cfg.get('terminal_error', {})
        self._cfg_stuck = cfg.get('stuck', {})

        self._last_hash: str | None = None
        self._hash_stable_since: float | None = None

    def judge(
        self,
        active_window: dict,
        mouse_activity: dict,
        keyboard_count: int,
        window_hash: str | None
    ) -> list[dict]:
        triggers = []

        if self._cfg_report.get('enabled', True):
            t = self._check_reading_report(active_window, mouse_activity, keyboard_count)
            if t:
                triggers.append(t)

        if self._cfg_terminal.get('enabled', True):
            t = self._check_terminal_error(active_window)
            if t:
                triggers.append(t)

        if self._cfg_stuck.get('enabled', True):
            t = self._check_stuck(active_window, mouse_activity, window_hash)
            if t:
                triggers.append(t)

        return triggers

    # ── 判断逻辑 ──────────────────────────────────────────────

    def _check_reading_report(self, aw, mouse, kb_count) -> dict | None:
        keywords = self._cfg_report.get('keywords', ['report', '报告', '分析', 'dashboard'])
        mouse_thr = self._cfg_report.get('mouse_idle_threshold', 5)
        kb_thr = self._cfg_report.get('keyboard_idle_threshold', 10)

        title = (aw.get('window_title') or '').lower()
        mouse_idle = mouse.get('is_idle', False) or mouse.get('avg_speed', 999) < 50
        kb_idle = kb_count < kb_thr
        title_hit = any(kw.lower() in title for kw in keywords)

        if mouse_idle and kb_idle and title_hit:
            return {
                'type': 'reading_report',
                'confidence': 0.8,
                'context': {
                    'app': aw.get('app'),
                    'window_title': aw.get('window_title'),
                    'matched_keyword': next((kw for kw in keywords if kw.lower() in title), None)
                }
            }
        return None

    def _check_terminal_error(self, aw) -> dict | None:
        terminal_apps = self._cfg_terminal.get(
            'terminal_apps',
            ['WindowsTerminal', 'cmd', 'powershell', 'Code', 'PyCharm']
        )
        error_keywords = ['error', 'failed', 'exception', 'traceback', 'fatal']

        app = aw.get('app', '')
        title = (aw.get('window_title') or '').lower()

        app_hit = any(t.lower() in app.lower() for t in terminal_apps)
        title_hit = any(kw in title for kw in error_keywords)

        if app_hit and title_hit:
            return {
                'type': 'terminal_error_maybe',
                'confidence': 0.7,
                'context': {
                    'app': app,
                    'window_title': aw.get('window_title')
                }
            }
        return None

    def _check_stuck(self, aw, mouse, window_hash) -> dict | None:
        threshold = self._cfg_stuck.get('stuck_duration_sec', 60)

        if window_hash is None:
            return None

        now = time.time()

        if window_hash != self._last_hash:
            self._last_hash = window_hash
            self._hash_stable_since = now
            return None

        if self._hash_stable_since is None:
            self._hash_stable_since = now
            return None

        stuck_sec = now - self._hash_stable_since
        # 人在（鼠标有活动）但窗口没变
        if stuck_sec >= threshold and not mouse.get('is_idle', True):
            return {
                'type': 'stuck_on_same_window',
                'confidence': 0.6,
                'context': {
                    'app': aw.get('app'),
                    'stuck_sec': int(stuck_sec)
                }
            }
        return None
