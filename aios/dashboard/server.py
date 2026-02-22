"""AIOS Dashboard Server v2.0 - WebSocket 实时推送
替换 30s 轮询为 WebSocket 推送，数据变化即时送达前端。

依赖: pip install websockets (如果没装会 fallback 到 HTTP 轮询)
"""
import asyncio
import http.server
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

PORT_HTTP = 9090
PORT_WS = 9091
DIR = os.path.dirname(os.path.abspath(__file__))
GENERATE_SCRIPT = os.path.join(DIR, "generate_data.py")
DATA_FILE = os.path.join(DIR, "dashboard_data.json")
PYTHON = r"C:\Program Files\Python312\python.exe"
REFRESH_INTERVAL = 10  # 数据刷新间隔（秒）

# WebSocket 客户端集合
ws_clients = set()
last_data_hash = None


def generate_data() -> dict:
    """运行 generate_data.py 并返回数据"""
    try:
        subprocess.run(
            [PYTHON, GENERATE_SCRIPT],
            capture_output=True, timeout=30,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def data_hash(data: dict) -> str:
    """简单哈希判断数据是否变化"""
    if not data:
        return ""
    # 只比较关键字段
    key = json.dumps({
        "overview": data.get("overview"),
        "events_count": len(data.get("events", {}).get("recent", [])),
    }, sort_keys=True)
    return str(hash(key))


# ── WebSocket 服务 ──

async def ws_handler(websocket):
    """处理 WebSocket 连接"""
    global ws_clients
    ws_clients.add(websocket)
    try:
        # 连接时立即推送当前数据
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            await websocket.send(json.dumps({"type": "full", "data": data}))

        # 保持连接，接收 ping
        async for message in websocket:
            if message == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
            elif message == "refresh":
                data = generate_data()
                if data:
                    await websocket.send(json.dumps({"type": "full", "data": data}))
    except Exception:
        pass
    finally:
        ws_clients.discard(websocket)


async def broadcast(data: dict):
    """向所有连接的客户端广播数据"""
    global ws_clients
    if not ws_clients:
        return
    message = json.dumps({"type": "update", "data": data})
    disconnected = set()
    for ws in ws_clients.copy():
        try:
            await ws.send(message)
        except Exception:
            disconnected.add(ws)
    ws_clients -= disconnected


async def data_refresh_loop():
    """定期刷新数据，有变化时广播"""
    global last_data_hash
    while True:
        await asyncio.sleep(REFRESH_INTERVAL)
        data = generate_data()
        if data:
            h = data_hash(data)
            if h != last_data_hash:
                last_data_hash = h
                await broadcast(data)


async def start_ws_server():
    """启动 WebSocket 服务"""
    try:
        import websockets
        server = await websockets.serve(ws_handler, "127.0.0.1", PORT_WS)
        print(f"  WebSocket: ws://127.0.0.1:{PORT_WS}")
        asyncio.create_task(data_refresh_loop())
        await server.wait_closed()
    except ImportError:
        print("  WebSocket: 未安装 websockets，使用 HTTP 轮询模式")
        print("  安装: pip install websockets")
        # fallback: 只跑数据刷新
        while True:
            generate_data()
            await asyncio.sleep(REFRESH_INTERVAL)


# ── HTTP 服务 ──

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        pass


def run_http():
    """HTTP 服务线程"""
    server = http.server.HTTPServer(("127.0.0.1", PORT_HTTP), Handler)
    server.serve_forever()


# ── 主入口 ──

def main():
    # 启动时先刷新一次
    generate_data()

    print(f"🐾 AIOS Dashboard v2.0")
    print(f"  HTTP:      http://127.0.0.1:{PORT_HTTP}")

    # HTTP 在后台线程
    http_thread = threading.Thread(target=run_http, daemon=True)
    http_thread.start()

    # WebSocket 在主线程 asyncio
    asyncio.run(start_ws_server())


if __name__ == "__main__":
    main()
