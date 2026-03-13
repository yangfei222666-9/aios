"""
active_window.py - 获取前台应用和窗口标题

Windows 实现：用 win32gui / ctypes
macOS 实现：用 Quartz + AppleScript
"""
import time
import platform

PLATFORM = platform.system()


def get_active_window() -> dict:
    """
    返回:
        {
            'app': str,           # 应用名
            'window_title': str,  # 窗口标题
            'timestamp': float,
            'error': str | None
        }
    """
    try:
        if PLATFORM == "Windows":
            return _get_active_window_windows()
        elif PLATFORM == "Darwin":
            return _get_active_window_macos()
        else:
            return _stub("linux not implemented")
    except Exception as e:
        return {'app': None, 'window_title': None, 'timestamp': time.time(), 'error': str(e)}


def _get_active_window_windows() -> dict:
    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()

    # 窗口标题
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    window_title = buf.value

    # 进程名
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        import psutil
        proc = psutil.Process(pid.value)
        app_name = proc.name()
    except Exception:
        app_name = f"pid:{pid.value}"

    return {
        'app': app_name,
        'window_title': window_title,
        'timestamp': time.time(),
        'error': None
    }


def _get_active_window_macos() -> dict:
    import subprocess
    script = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        tell process frontApp
            try
                set windowTitle to name of front window
            on error
                set windowTitle to ""
            end try
        end tell
    end tell
    return frontApp & "|" & windowTitle
    '''
    result = subprocess.run(['osascript', '-e', script],
                            capture_output=True, text=True, timeout=2)
    parts = result.stdout.strip().split('|', 1)
    return {
        'app': parts[0] if parts else None,
        'window_title': parts[1] if len(parts) > 1 else '',
        'timestamp': time.time(),
        'error': None
    }


def _stub(reason: str) -> dict:
    return {'app': 'stub', 'window_title': reason, 'timestamp': time.time(), 'error': None}
