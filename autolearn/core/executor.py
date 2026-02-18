# core/executor.py - 统一执行入口 (v1.0 稳定 API)
import traceback, sys, os, platform, time
from core.logger import log_event
from core.errors import sign_strict, sign_loose
from core.lessons import find
from core.circuit_breaker import check_and_trip, allow, get_checklist
from core.rules import apply_rules
from core.version import MODULE_VERSION, SCHEMA_VERSION

# aios 事件总线（可选）
try:
    sys.path.insert(0, os.path.join(os.environ.get("USERPROFILE", ""), ".openclaw", "workspace", "aios"))
    from bridge import on_executor_run as _aios_exec, on_circuit_breaker as _aios_cb
except Exception:
    _aios_exec = _aios_cb = None

def _env_fingerprint() -> dict:
    env = {
        "python": sys.version.split()[0],
        "os": f"{platform.system()} {platform.version()}",
        "arch": platform.machine(),
        "module_version": MODULE_VERSION,
    }
    try:
        import subprocess
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, timeout=3,
                          cwd=os.path.join(os.environ.get("USERPROFILE", ""), ".openclaw", "workspace"))
        if r.returncode == 0:
            env["git"] = r.stdout.strip()
    except Exception:
        pass
    try:
        import subprocess
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_VideoController | Where-Object {$_.Name -like '*NVIDIA*'}).DriverVersion"],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            env["gpu_driver"] = r.stdout.strip()
    except Exception:
        pass
    return env

# === v1.0 STABLE API ===

def run(intent: str, tool: str, payload: dict, do_task) -> dict:
    """
    统一执行入口。
    do_task(intent, payload) → {"ok": True, "result": ...} 或抛异常
    返回 dict: {ok, result?, error?, error_sig?, tips?, tripped?, checklist?}
    """
    env = _env_fingerprint()
    
    # 规则引擎：在执行前拦截+改写
    payload = apply_rules(intent, tool, payload)
    
    log_event(type="start", intent=intent, tool=tool, env=env)
    
    t0 = time.time()
    try:
        out = do_task(intent, payload)
        elapsed_ms = int((time.time() - t0) * 1000)
        if isinstance(out, dict) and out.get("ok"):
            log_event(type="done", intent=intent, tool=tool, ok=True, elapsed_ms=elapsed_ms, env=env)
            # → aios
            if _aios_exec:
                try: _aios_exec(intent, tool, True, str(out.get("result", ""))[:200], elapsed_ms)
                except Exception: pass
            return out

        msg = ""
        if isinstance(out, dict):
            msg = out.get("error", "unknown error")
        else:
            msg = "unknown error"
        raise RuntimeError(msg)

    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        sig_s = sign_strict(type(e).__name__, str(e))
        loose = sign_loose(str(e))
        sig_l = loose["sig"]
        tips = find(sig_s, sig_loose=sig_l)
        
        tripped = check_and_trip(sig_s)
        
        log_event(
            type="done",
            intent=intent,
            tool=tool,
            ok=False,
            error=str(e)[:500],
            error_sig=sig_s,
            sig_loose=sig_l,
            loose_keywords=loose["keywords"],
            tips_count=len(tips),
            tripped=tripped,
            elapsed_ms=elapsed_ms,
            env=env,
        )
        
        result = {
            "ok": False,
            "error": str(e)[:500],
            "error_sig": sig_s,
            "sig_loose": sig_l,
            "tips": tips,
        }
        
        if tripped:
            result["tripped"] = True
            result["checklist"] = get_checklist()
            # → aios 熔断事件
            if _aios_cb:
                try: _aios_cb(sig_s, True)
                except Exception: pass
        
        # → aios 错误事件
        if _aios_exec:
            try: _aios_exec(intent, tool, False, str(e)[:200], elapsed_ms)
            except Exception: pass
        
        return result
