"""
AIOS Dashboard Server
WebSocket + HTTP fallback for real-time monitoring
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="AIOS Dashboard")

# Paths
BASE_DIR = Path(__file__).parent.parent
EVENTS_FILE = BASE_DIR / "events.jsonl"
AGENTS_FILE = BASE_DIR / "agent_system" / "data" / "agents.jsonl"
ACTIONS_FILE = BASE_DIR / "pending_actions.jsonl"
ALERTS_FILE = BASE_DIR / "alert_fsm.jsonl"

# WebSocket connections
active_connections: List[WebSocket] = []


class DashboardData:
    """Data aggregator for dashboard"""

    @staticmethod
    def load_jsonl(path: Path, limit: int = 100) -> List[Dict]:
        """Load recent lines from JSONL"""
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        return [json.loads(line) for line in lines[-limit:] if line.strip()]

    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """System health summary"""
        events = DashboardData.load_jsonl(EVENTS_FILE, limit=1000)
        now = datetime.now()
        last_hour = now - timedelta(hours=1)

        recent = [
            e
            for e in events
            if datetime.fromisoformat(e.get("ts", "2000-01-01")) > last_hour
        ]

        errors = [e for e in recent if e.get("level") == "ERROR"]
        warnings = [e for e in recent if e.get("level") == "WARN"]

        return {
            "status": (
                "critical"
                if len(errors) > 10
                else "warning" if len(errors) > 0 else "healthy"
            ),
            "events_1h": len(recent),
            "errors_1h": len(errors),
            "warnings_1h": len(warnings),
            "last_event": events[-1] if events else None,
        }

    @staticmethod
    def get_agents_status() -> Dict[str, Any]:
        """Agent system status"""
        agents = DashboardData.load_jsonl(AGENTS_FILE)
        if not agents:
            return {"total": 0, "active": 0, "archived": 0, "agents": []}

        now = datetime.now()
        active = []
        archived = []

        for a in agents:
            if a.get("status") == "archived":
                archived.append(a)
            else:
                last_seen = datetime.fromisoformat(a.get("last_active", "2000-01-01"))
                if (now - last_seen).total_seconds() < 3600:  # Active in last hour
                    active.append(a)

        # 计算总任务数
        total_tasks = sum(a.get("stats", {}).get("tasks_completed", 0) for a in agents)

        return {
            "total": len(agents),
            "active": len(active),
            "archived": len(archived),
            "total_tasks": total_tasks,
            "agents": agents,  # 返回所有 Agent
        }

    @staticmethod
    def get_pending_actions() -> List[Dict]:
        """Pending actions queue"""
        return DashboardData.load_jsonl(ACTIONS_FILE, limit=20)

    @staticmethod
    def get_alerts() -> Dict[str, Any]:
        """Alert status"""
        alerts = DashboardData.load_jsonl(ALERTS_FILE)
        open_alerts = [a for a in alerts if a.get("state") == "OPEN"]
        ack_alerts = [a for a in alerts if a.get("state") == "ACK"]

        return {
            "open": len(open_alerts),
            "acknowledged": len(ack_alerts),
            "recent": alerts[-10:],
        }

    @staticmethod
    def get_event_stream(limit: int = 50) -> List[Dict]:
        """Recent event stream"""
        return DashboardData.load_jsonl(EVENTS_FILE, limit=limit)


@app.get("/", response_class=HTMLResponse)
async def dashboard_ui():
    """Serve dashboard HTML"""
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Dashboard UI not found</h1>"


@app.get("/api/snapshot")
async def get_snapshot():
    """HTTP fallback: full dashboard snapshot"""
    return JSONResponse(
        {
            "timestamp": datetime.now().isoformat(),
            "health": DashboardData.get_system_health(),
            "agents": DashboardData.get_agents_status(),
            "actions": DashboardData.get_pending_actions(),
            "alerts": DashboardData.get_alerts(),
            "events": DashboardData.get_event_stream(limit=30),
        }
    )


@app.post("/api/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        alerts = DashboardData.load_jsonl(ALERTS_FILE)
        updated = False

        for alert in alerts:
            if alert.get("id") == alert_id and alert.get("state") == "OPEN":
                alert["state"] = "ACK"
                alert["ack_ts"] = datetime.now().isoformat()
                updated = True
                break

        if updated:
            ALERTS_FILE.write_text(
                "\n".join(json.dumps(a) for a in alerts) + "\n", encoding="utf-8"
            )
            return JSONResponse({"success": True, "message": "Alert acknowledged"})
        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": "Alert not found or already acknowledged",
                },
                status_code=404,
            )
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        alerts = DashboardData.load_jsonl(ALERTS_FILE)
        updated = False

        for alert in alerts:
            if alert.get("id") == alert_id and alert.get("state") in ["OPEN", "ACK"]:
                alert["state"] = "RESOLVED"
                alert["resolved_ts"] = datetime.now().isoformat()
                updated = True
                break

        if updated:
            ALERTS_FILE.write_text(
                "\n".join(json.dumps(a) for a in alerts) + "\n", encoding="utf-8"
            )
            return JSONResponse({"success": True, "message": "Alert resolved"})
        else:
            return JSONResponse(
                {"success": False, "message": "Alert not found or already resolved"},
                status_code=404,
            )
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/trigger/pipeline")
async def trigger_pipeline():
    """Manually trigger AIOS Pipeline"""
    import subprocess

    try:
        result = subprocess.run(
            [
                "C:\\Program Files\\Python312\\python.exe",
                "-X",
                "utf8",
                str(BASE_DIR / "pipeline.py"),
                "run",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        return JSONResponse(
            {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
            }
        )
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/trigger/agent_queue")
async def trigger_agent_queue():
    """Manually trigger Agent task queue processing"""
    import subprocess

    try:
        result = subprocess.run(
            [
                "C:\\Program Files\\Python312\\python.exe",
                str(BASE_DIR / "agent_system" / "auto_dispatcher.py"),
                "heartbeat",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        return JSONResponse(
            {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
            }
        )
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send initial snapshot
        snapshot = {
            "type": "snapshot",
            "data": {
                "health": DashboardData.get_system_health(),
                "agents": DashboardData.get_agents_status(),
                "actions": DashboardData.get_pending_actions(),
                "alerts": DashboardData.get_alerts(),
                "events": DashboardData.get_event_stream(limit=30),
            },
        }
        await websocket.send_json(snapshot)

        # Keep connection alive and send updates
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5s
                update = {
                    "type": "update",
                    "data": {
                        "health": DashboardData.get_system_health(),
                        "agents": DashboardData.get_agents_status(),
                        "actions": DashboardData.get_pending_actions(),
                        "alerts": DashboardData.get_alerts(),
                        "events": DashboardData.get_event_stream(limit=10),
                    },
                }
                await websocket.send_json(update)
            except Exception as e:
                print(f"Error sending update: {e}")
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


def run_server(host: str = "127.0.0.1", port: int = 9091):
    """Start dashboard server"""
    print(f"AIOS Dashboard starting at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
