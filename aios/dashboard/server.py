"""AIOS Dashboard Server - 带自动数据刷新"""
import http.server
import json
import os
import subprocess
import time
import threading

PORT = 9090
DIR = os.path.dirname(os.path.abspath(__file__))
GENERATE_SCRIPT = os.path.join(DIR, "generate_data.py")
PYTHON = r"C:\Program Files\Python312\python.exe"
REFRESH_INTERVAL = 60  # 每60秒刷新一次数据


def refresh_data():
    """后台线程定期刷新数据"""
    while True:
        try:
            subprocess.run(
                [PYTHON, GENERATE_SCRIPT],
                capture_output=True, timeout=30,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
        except Exception:
            pass
        time.sleep(REFRESH_INTERVAL)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        # 禁用缓存
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # 静默日志


if __name__ == "__main__":
    # 启动时先刷新一次
    try:
        subprocess.run(
            [PYTHON, GENERATE_SCRIPT],
            capture_output=True, timeout=30,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
    except Exception:
        pass

    # 后台刷新线程
    t = threading.Thread(target=refresh_data, daemon=True)
    t.start()

    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"AIOS Dashboard running at http://127.0.0.1:{PORT}")
    server.serve_forever()
