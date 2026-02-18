# core/rules.py - 规则引擎：在错误发生前拦截+改写 (v1.0)
import re, os, json
from pathlib import Path
from core.logger import log_event

DATA = Path(__file__).parent.parent / "data"
LOCAL_RULES_FILE = DATA / "rules.local.jsonl"

# 规则注册表
_RULES = []
_LOCAL_RULES = []

def rule(name, tags=None, reason=""):
    """装饰器：注册一条内置规则"""
    def decorator(fn):
        _RULES.append({"rule_id": f"builtin:{name}", "name": name, "tags": tags or [], "reason": reason, "fn": fn})
        return fn
    return decorator

def _load_local_rules():
    """从 data/rules.local.jsonl 加载外置规则（启动时一次）"""
    global _LOCAL_RULES
    _LOCAL_RULES = []
    if not LOCAL_RULES_FILE.exists():
        return
    for line in LOCAL_RULES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            if r.get("pattern") and r.get("replacement"):
                _LOCAL_RULES.append(r)
        except Exception:
            pass

def _apply_local_rule(r, payload):
    """应用一条外置规则（正则替换）"""
    fields = r.get("fields", ["cmd", "command"])
    changed = False
    new_payload = {**payload}
    for field in fields:
        val = new_payload.get(field, "")
        if not isinstance(val, str):
            continue
        new_val = re.sub(r["pattern"], r["replacement"], val)
        if new_val != val:
            new_payload[field] = new_val
            changed = True
    return new_payload, changed

# 启动时加载
_load_local_rules()

def apply_rules(intent: str, tool: str, payload: dict) -> dict:
    """对 payload 应用所有匹配规则，返回改写后的 payload"""
    rewrites = []
    
    # 内置规则
    for r in _RULES:
        try:
            new_payload, changed, detail = r["fn"](intent, tool, payload)
            if changed:
                rewrites.append({
                    "rule_id": r["rule_id"],
                    "rule": r["name"],
                    "detail": detail,
                    "reason": r["reason"],
                })
                payload = new_payload
        except Exception:
            pass
    
    # 外置规则
    for r in _LOCAL_RULES:
        try:
            new_payload, changed = _apply_local_rule(r, payload)
            if changed:
                rewrites.append({
                    "rule_id": r.get("rule_id", f"local:{r.get('name', '?')}"),
                    "rule": r.get("name", "unnamed"),
                    "detail": r.get("description", ""),
                    "reason": r.get("reason", "matched local rule pattern"),
                })
                payload = new_payload
        except Exception:
            pass
    
    if rewrites:
        log_event(type="rewrite", intent=intent, tool=tool, rewrites=rewrites)
    
    return payload

# === 内置规则 ===

@rule("ps_dir_b", tags=["powershell"], reason="dir /b is cmd.exe syntax, not PowerShell; Get-ChildItem -Name is the PS equivalent")
def _rule_ps_dir_b(intent, tool, payload):
    """PowerShell dir /b → Get-ChildItem -Name"""
    cmd = payload.get("cmd") or payload.get("command") or ""
    if not cmd:
        return payload, False, ""
    
    # 匹配 dir "path" /flags 或 dir path /flags（含 /b）
    pattern = r'\bdir\s+("(?:[^"]+)"|[^\s/]+)(?:\s+/[A-Za-z-]+)*\s*/[A-Za-z-]*[bB][A-Za-z-]*(?:\s+/[A-Za-z-]+)*'
    match = re.search(pattern, cmd)
    if not match:
        return payload, False, ""
    
    path_part = match.group(1).strip().strip('"')
    new_cmd = cmd[:match.start()] + f'Get-ChildItem "{path_part}" -Name' + cmd[match.end():]
    
    new_payload = {**payload}
    if "cmd" in new_payload:
        new_payload["cmd"] = new_cmd
    if "command" in new_payload:
        new_payload["command"] = new_cmd
    
    return new_payload, True, "dir /b → Get-ChildItem -Name"

@rule("expand_tilde", tags=["path"], reason="~ only expands in interactive shell; scripts and external tools need absolute paths")
def _rule_expand_tilde(intent, tool, payload):
    r"""~/ 或 ~\ → 绝对路径"""
    changed = False
    detail = []
    new_payload = {}
    home = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    
    for k, v in payload.items():
        if isinstance(v, str) and re.search(r'(?:^|[\s"\'=])~[/\\]', v):
            new_v = re.sub(r'~([/\\])', home.replace('\\', '\\\\') + r'\1', v)
            new_payload[k] = new_v
            changed = True
            detail.append(f"{k}: ~ → {home}")
        else:
            new_payload[k] = v
    
    return new_payload, changed, "; ".join(detail) if detail else ""
