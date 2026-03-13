"""
window_capture.py - 活跃窗口截图

Windows: mss（比 PIL.ImageGrab 快，支持多显示器）
macOS:   Quartz CGWindowListCreateImage

只在触发时调用，不做轮询截图。
"""
import hashlib
import platform
import time
from io import BytesIO

PLATFORM = platform.system()


def capture_active_window() -> dict | None:
    """
    返回:
        {
            'image_bytes': bytes,   # PNG bytes
            'hash': str,            # MD5
            'width': int,
            'height': int,
            'timestamp': float,
        }
    或 None（截图失败）
    """
    try:
        if PLATFORM == "Windows":
            return _capture_windows()
        elif PLATFORM == "Darwin":
            return _capture_macos()
        else:
            return None
    except Exception:
        return None


def _capture_windows() -> dict | None:
    """用 mss 截取前台窗口"""
    try:
        import ctypes
        import ctypes.wintypes
        import mss

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()

        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        x, y = rect.left, rect.top
        w, h = rect.right - rect.left, rect.bottom - rect.top

        if w <= 0 or h <= 0:
            return None

        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": w, "height": h}
            shot = sct.grab(monitor)
            # mss → PNG bytes
            from mss.tools import to_png
            png_bytes = to_png(shot.rgb, shot.size)

        img_hash = hashlib.md5(png_bytes).hexdigest()
        return {
            'image_bytes': png_bytes,
            'hash': img_hash,
            'width': w,
            'height': h,
            'timestamp': time.time(),
        }
    except ImportError:
        # mss 未安装，降级到 PIL
        return _capture_windows_pil()


def _capture_windows_pil() -> dict | None:
    from PIL import ImageGrab
    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    x, y, r, b = rect.left, rect.top, rect.right, rect.bottom

    img = ImageGrab.grab(bbox=(x, y, r, b))
    buf = BytesIO()
    img.save(buf, format='PNG')
    png_bytes = buf.getvalue()
    img_hash = hashlib.md5(png_bytes).hexdigest()
    return {
        'image_bytes': png_bytes,
        'hash': img_hash,
        'width': r - x,
        'height': b - y,
        'timestamp': time.time(),
    }


def _capture_macos() -> dict | None:
    import Quartz
    from PIL import Image

    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly |
        Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )
    for win in window_list:
        if win.get('kCGWindowLayer', 999) == 0:
            bounds = win['kCGWindowBounds']
            x, y = int(bounds['X']), int(bounds['Y'])
            w, h = int(bounds['Width']), int(bounds['Height'])
            if w <= 0 or h <= 0:
                continue
            cg_img = Quartz.CGWindowListCreateImage(
                Quartz.CGRectMake(x, y, w, h),
                Quartz.kCGWindowListOptionIncludingWindow,
                win['kCGWindowNumber'],
                Quartz.kCGWindowImageDefault
            )
            pil_img = Image.frombytes('RGB', (w, h), cg_img)
            buf = BytesIO()
            pil_img.save(buf, format='PNG')
            png_bytes = buf.getvalue()
            return {
                'image_bytes': png_bytes,
                'hash': hashlib.md5(png_bytes).hexdigest(),
                'width': w,
                'height': h,
                'timestamp': time.time(),
            }
    return None
