#!/usr/bin/env python3
"""
memory_server.py - Lightweight HTTP server for memory retrieval.
Keeps the embedding model warm in memory.

Usage:
  python memory_server.py          # start on port 7788
  python memory_server.py --port 7788

Endpoints:
  GET  /status
  POST /query   {"text": "...", "task_type": "code", "top_k": 3}
  POST /ingest  {"text": "...", "task_type": "code", "outcome": "success", "record_id": "..."}
  POST /feedback {"record_id": "...", "helpful": true}
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 7788
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Pre-load on import (happens once at server start)
print("[MEMORY_SERVER] Loading embedding model...", flush=True)
from memory_retrieval import query, ingest, feedback, _get_model
_get_model()  # warm up
print("[MEMORY_SERVER] Model ready.", flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default access log

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _respond(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            self._respond({"status": "ok", "model": "all-MiniLM-L6-v2", "port": PORT})
        else:
            self._respond({"error": "not found"}, 404)

    def do_POST(self):
        try:
            body = self._read_body()
        except Exception as e:
            self._respond({"error": str(e)}, 400)
            return

        if self.path == "/query":
            import time as _time
            _t0 = _time.time()
            hits = query(
                body.get("text", ""),
                top_k=body.get("top_k", 3),
                task_type=body.get("task_type") or None,
            )
            _elapsed = round((_time.time() - _t0) * 1000, 1)
            # 记录到 retrieval log（供 Gate 采集）
            try:
                from datetime import datetime as _dt, timezone as _tz, timedelta as _td
                _log_entry = json.dumps({
                    "timestamp": _dt.now(_tz(_td(hours=8))).isoformat(),
                    "latency_ms": _elapsed,
                    "result_count": len(hits),
                    "query_text": body.get("text", "")[:80],
                }, ensure_ascii=False)
                with open(Path(__file__).parent / "memory_retrieval_log.jsonl", "a", encoding="utf-8") as _f:
                    _f.write(_log_entry + "\n")
            except Exception:
                pass
            self._respond({"hits": hits, "elapsed_ms": _elapsed})

        elif self.path == "/ingest":
            rid = ingest(
                text=body.get("text", ""),
                task_type=body.get("task_type", ""),
                outcome=body.get("outcome", "success"),
                tags=body.get("tags", []),
                record_id=body.get("record_id"),
            )
            self._respond({"record_id": rid})

        elif self.path == "/feedback":
            ok = feedback(body.get("record_id", ""), helpful=body.get("helpful", True))
            # 记录 feedback（供 Gate 质量采集）
            try:
                from datetime import datetime as _dt, timezone as _tz, timedelta as _td
                _fb_entry = json.dumps({
                    "timestamp": _dt.now(_tz(_td(hours=8))).isoformat(),
                    "record_id": body.get("record_id", ""),
                    "helpful": body.get("helpful", True),
                    "helpfulness": 0.6 if body.get("helpful", True) else 0.4,
                }, ensure_ascii=False)
                with open(Path(__file__).parent / "reports" / "feedback_log.jsonl", "a", encoding="utf-8") as _f:
                    _f.write(_fb_entry + "\n")
            except Exception:
                pass
            self._respond({"ok": ok})

        else:
            self._respond({"error": "not found"}, 404)


def run(port=PORT):
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"[MEMORY_SERVER] Listening on http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    port = PORT
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
    run(port)
