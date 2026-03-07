#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Site Monitor - 融合版本
- 支持 list_regex / json_key / github_atom / pypi
- 零依赖（urllib + json）
- OpenClaw 原生集成（文件通信）
- 可选 Telegram Bot API
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(os.getenv("MONITOR_TZ", "Asia/Shanghai"))
except ImportError:
    # Python < 3.9 fallback
    TZ = None

try:
    import yaml
except ImportError:
    yaml = None

UA = os.getenv("MONITOR_UA", "OpenClaw-SiteMonitor/1.0")

@dataclass
class Event:
    name: str
    url: str
    priority: str  # "high" | "daily"
    changed: bool
    value: str
    message: str

def now_iso() -> str:
    if TZ:
        return dt.datetime.now(TZ).isoformat(timespec="seconds")
    return dt.datetime.now().isoformat(timespec="seconds")

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    if path.endswith((".yml", ".yaml")):
        if yaml is None:
            raise RuntimeError("需要 YAML 配置但未安装 pyyaml：pip install pyyaml")
        return yaml.safe_load(raw) or {}
    return json.loads(raw)

def load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_state(path: str, state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def http_get(url: str, timeout: int = 20) -> str:
    """零依赖 HTTP GET"""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*"
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content = response.read()
        try:
            return content.decode('utf-8')
        except:
            return content.decode('latin-1')

def json_get(url: str, timeout: int = 20) -> Any:
    text = http_get(url, timeout=timeout)
    return json.loads(text)

def json_path_get(obj: Any, path: str) -> Any:
    """
    支持 path:
    - "0" / "[0]" 访问数组
    - "n.champion" / "info.version" 访问 dict
    - 混合："a.b[0].c"
    """
    cur = obj
    tokens = []
    s = path.strip()
    
    # 将 a.b[0].c -> ["a","b","[0]","c"]
    i = 0
    buf = ""
    while i < len(s):
        ch = s[i]
        if ch == ".":
            if buf:
                tokens.append(buf)
            buf = ""
            i += 1
            continue
        if ch == "[":
            if buf:
                tokens.append(buf)
            buf = ""
            j = s.find("]", i)
            if j == -1:
                raise ValueError(f"json_path 缺少 ]：{path}")
            tokens.append(s[i : j + 1])
            i = j + 1
            continue
        buf += ch
        i += 1
    if buf:
        tokens.append(buf)
    
    for t in tokens:
        if t.startswith("[") and t.endswith("]"):
            idx = int(t[1:-1])
            cur = cur[idx]
        else:
            # 允许 "0" 作为数组索引
            if isinstance(cur, list) and re.fullmatch(r"\d+", t):
                cur = cur[int(t)]
            else:
                cur = cur[t]
    return cur

def minutes_since(iso: Optional[str]) -> Optional[int]:
    if not iso:
        return None
    try:
        t = dt.datetime.fromisoformat(iso)
        if TZ:
            delta = dt.datetime.now(TZ) - t.astimezone(TZ)
        else:
            delta = dt.datetime.now() - t
        return int(delta.total_seconds() // 60)
    except Exception:
        return None

def within_min_interval(last_notified_at: Optional[str], min_hours: int) -> bool:
    if min_hours <= 0:
        return False
    mins = minutes_since(last_notified_at)
    if mins is None:
        return False
    return mins < (min_hours * 60)

def extract_latest_by_regex(text: str, pattern: str) -> Tuple[str, str, str]:
    """
    pattern 必须能匹配到 named group: title
    可选 named group: date, link
    返回：(title, date, link)
    """
    m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        raise ValueError("regex 未匹配到任何内容（检查 pattern）")
    title = (m.groupdict().get("title") or "").strip()
    date = (m.groupdict().get("date") or "").strip()
    link = (m.groupdict().get("link") or "").strip()
    return title, date, link

def parse_atom_latest_entry(xml_text: str) -> Tuple[str, str]:
    """
    轻量 atom 解析：抓 <entry> 的 <id> 或 <link href> + <updated>
    返回：(id_or_link, updated)
    """
    entry = re.search(r"<entry>(.*?)</entry>", xml_text, flags=re.DOTALL | re.IGNORECASE)
    if not entry:
        raise ValueError("atom 未找到 entry")
    block = entry.group(1)
    
    _id = ""
    m_id = re.search(r"<id>(.*?)</id>", block, flags=re.DOTALL | re.IGNORECASE)
    if m_id:
        _id = re.sub(r"\s+", " ", m_id.group(1)).strip()
    
    href = ""
    m_link = re.search(r'<link[^>]+href="([^"]+)"', block, flags=re.IGNORECASE)
    if m_link:
        href = m_link.group(1).strip()
    
    updated = ""
    m_upd = re.search(r"<updated>(.*?)</updated>", block, flags=re.DOTALL | re.IGNORECASE)
    if m_upd:
        updated = re.sub(r"\s+", " ", m_upd.group(1)).strip()
    
    key = _id or href
    if not key:
        raise ValueError("atom 未解析到 id/link")
    return key, updated

def send_telegram(text: str) -> None:
    """
    使用 Telegram Bot API：
    export TG_BOT_TOKEN="xxx"
    export TG_CHAT_ID="123456789"
    """
    token = os.getenv("TG_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TG_CHAT_ID", "").strip()
    if not token or not chat_id:
        return  # 未配置则静默跳过
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=15)

def queue_openclaw_notification(message: str, notify_file: str) -> None:
    """队列 OpenClaw 通知（文件通信）"""
    notifications = []
    if os.path.exists(notify_file):
        with open(notify_file, 'r', encoding='utf-8') as f:
            try:
                notifications = json.load(f)
            except:
                notifications = []
    
    notifications.append({
        'timestamp': now_iso(),
        'message': message
    })
    
    with open(notify_file, 'w', encoding='utf-8') as f:
        json.dump(notifications, f, indent=2, ensure_ascii=False)

def append_heartbeat(path: str, lines: list[str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    header = f"\n## {now_iso()}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(header)
        for ln in lines:
            f.write(f"- {ln}\n")

def run_monitor(m: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Optional[Event], Dict[str, Any]]:
    name = m["name"]
    url = m["url"]
    mtype = m["type"]
    priority = m.get("priority", "daily")
    min_interval_hours = int(m.get("min_interval_hours", 24))
    
    st = state.get(name, {})
    last_value = st.get("last_value")
    last_notified_at = st.get("last_notified_at")
    checked_at = now_iso()
    
    try:
        if mtype == "json_key":
            obj = json_get(url)
            key_path = m["json_path"]
            v = json_path_get(obj, key_path)
            value = str(v)
            changed = (value != str(last_value)) if last_value is not None else True
            msg = f"[{name}] JSON key changed: {key_path} -> {value}"
        
        elif mtype == "list_regex":
            text = http_get(url)
            title, date, link = extract_latest_by_regex(text, m["pattern"])
            value = f"{title}|{date}".strip("|")
            changed = (value != str(last_value)) if last_value is not None else True
            msg = f"[{name}] Latest changed: {title} ({date})" + (f" {link}" if link else "")
        
        elif mtype == "github_atom":
            feed_url = m.get("feed_url", url)
            xml = http_get(feed_url)
            key, updated = parse_atom_latest_entry(xml)
            value = f"{key}|{updated}".strip("|")
            changed = (value != str(last_value)) if last_value is not None else True
            msg = f"[{name}] GitHub feed latest: {updated} {key}"
        
        elif mtype == "pypi":
            pkg = m["package"]
            api = f"https://pypi.org/pypi/{pkg}/json"
            obj = json_get(api)
            ver = json_path_get(obj, "info.version")
            value = str(ver)
            changed = (value != str(last_value)) if last_value is not None else True
            msg = f"[{name}] PyPI version: {value}"
        
        else:
            raise ValueError(f"未知 monitor type: {mtype}")
        
        # 更新 state
        st.update({
            "last_checked_at": checked_at,
            "last_value": value,
            "last_error": None,
        })
        
        # 触发事件（带 min_interval）
        if changed:
            if within_min_interval(last_notified_at, min_interval_hours):
                # 变化了但在窗口内：不重复通知，只记录已看到
                st["suppressed_at"] = checked_at
                state[name] = st
                return None, state
            
            ev = Event(
                name=name,
                url=url,
                priority=priority,
                changed=True,
                value=value,
                message=msg,
            )
            st["last_notified_at"] = checked_at
            state[name] = st
            return ev, state
        
        state[name] = st
        return None, state
    
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        st.update({"last_checked_at": checked_at, "last_error": err})
        
        # 错误也走 min_interval（避免刷屏）
        last_err_notified = st.get("last_error_notified_at")
        if not within_min_interval(last_err_notified, min_interval_hours):
            ev = Event(
                name=name,
                url=url,
                priority="daily",
                changed=True,
                value="ERROR",
                message=f"[{name}] ERROR: {err}",
            )
            st["last_error_notified_at"] = checked_at
            state[name] = st
            return ev, state
        
        state[name] = st
        return None, state

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="monitors.yaml / monitors.json")
    ap.add_argument("--state", default="last_seen.json", help="state json path")
    ap.add_argument("--heartbeat", default="reports/heartbeat_monitor.md", help="heartbeat md path")
    ap.add_argument("--notify-file", default="site_monitor_notify.json", help="OpenClaw notify queue")
    ap.add_argument("--dry-run", action="store_true", help="do not send telegram")
    ap.add_argument("--only", default="", help="comma-separated monitor names filter")
    ap.add_argument("--use-telegram-bot", action="store_true", help="use Telegram Bot API instead of OpenClaw")
    args = ap.parse_args()
    
    cfg = load_config(args.config)
    monitors = cfg.get("monitors", [])
    if not isinstance(monitors, list) or not monitors:
        print("config.monitors 为空", file=sys.stderr)
        return 2
    
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    if only:
        monitors = [m for m in monitors if m.get("name") in only]
    
    state = load_state(args.state)
    events: list[Event] = []
    
    for m in monitors:
        ev, state = run_monitor(m, state)
        if ev:
            events.append(ev)
    
    # 通知分级
    tg_msgs: list[str] = []
    hb_lines: list[str] = []
    
    for ev in events:
        hb_lines.append(ev.message + f" | {ev.url}")
        if ev.priority == "high":
            tg_msgs.append(ev.message + f"\n{ev.url}")
    
    if hb_lines:
        append_heartbeat(args.heartbeat, hb_lines)
    
    if tg_msgs and (not args.dry_run):
        text = "🔔 Monitor Alerts\n\n" + "\n\n".join(tg_msgs)
        try:
            if args.use_telegram_bot:
                send_telegram(text)
            else:
                queue_openclaw_notification(text, args.notify_file)
        except Exception as e:
            append_heartbeat(args.heartbeat, [f"[TELEGRAM] send failed: {type(e).__name__}: {e}"])
    
    save_state(args.state, state)
    
    # 终端输出一份简报
    if events:
        print(f"{len(events)} event(s):")
        for ev in events:
            print("-", ev.message)
    else:
        print("no changes.")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
