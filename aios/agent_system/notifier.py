#!/usr/bin/env python3
"""
AIOS Alert Writer - Write alerts to alerts.jsonl for OpenClaw to pick up and send via Telegram.
"""
import json
from datetime import datetime
from pathlib import Path

ALERTS_FILE = Path(__file__).parent / "alerts.jsonl"


def write_alert(level: str, title: str, body: str):
    """Write an alert to alerts.jsonl.
    
    Args:
        level: "info", "warning", "critical"
        title: Short title
        body: Full message text
    """
    alert = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "title": title,
        "body": body,
        "sent": False,
    }
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")


def get_unsent() -> list:
    """Read all unsent alerts."""
    if not ALERTS_FILE.exists():
        return []
    alerts = []
    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
                if not a.get("sent", False):
                    alerts.append(a)
            except json.JSONDecodeError:
                continue
    return alerts


def mark_all_sent():
    """Mark all alerts as sent by rewriting the file."""
    if not ALERTS_FILE.exists():
        return
    lines = []
    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
                a["sent"] = True
                lines.append(json.dumps(a, ensure_ascii=False))
            except json.JSONDecodeError:
                lines.append(line)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n" if lines else "")


# Convenience functions for process_monitor
def process_down(name, details=""):
    write_alert("critical", f"Process Down: {name}", f"{name} is not running. {details}".strip())

def process_restarted(name):
    write_alert("info", f"Process Restarted: {name}", f"{name} is back online.")

def process_restart_failed(name, attempt, max_retries):
    write_alert("warning", f"Restart Failed: {name}", f"{name} restart attempt {attempt}/{max_retries} failed.")

def process_circuit_break(name, max_retries):
    write_alert("critical", f"CIRCUIT BREAK: {name}", f"{name} failed {max_retries} times. Stopped retrying. Needs manual intervention.")

# Convenience functions for git_test_runner
def test_passed(commit, author, message, passed, total, duration):
    write_alert("info", "Tests Passed", f"Commit {commit[:7]} by {author}: {message}\nResult: {passed}/{total} passed ({duration:.1f}s)")

def test_failed(commit, author, message, passed, failed, total, duration, failures=None):
    body = f"Commit {commit[:7]} by {author}: {message}\nResult: {passed}/{total} passed, {failed} failed ({duration:.1f}s)"
    if failures:
        body += "\nFailed:\n" + "\n".join(f"- {f}" for f in failures[:5])
    write_alert("critical", "Tests Failed", body)
