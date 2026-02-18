# aios/bridge.py - 桥接层：autolearn → aios 事件总线
"""
不改 autolearn 代码，在外层包一层，把 autolearn 的输出转为 aios 事件。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "autolearn"))

from scripts.log_event import log_event


def on_match(query: str, matched_title: str, matched_id: str, score: float, match_type: str):
    """matcher 匹配后调用"""
    return log_event("match", "aram.matcher", f"{query} → {matched_title}", {
        "input": query,
        "matched": matched_title,
        "matched_id": matched_id,
        "score": score,
        "match_type": match_type,
    })


def on_correction(query: str, wrong_title: str, correct_title: str, correct_id: str):
    """用户纠正后调用"""
    return log_event("correction", "aram.matcher", f"{query}: {wrong_title} → {correct_title}", {
        "input": query,
        "matched": wrong_title,
        "correct_target": correct_title,
        "correct_id": correct_id,
    })


def on_confirm(query: str, matched_title: str, matched_id: str):
    """用户确认后调用"""
    return log_event("confirm", "aram.matcher", f"{query} = {matched_title} ✓", {
        "input": query,
        "matched": matched_title,
        "matched_id": matched_id,
    })


def on_executor_run(intent: str, tool: str, ok: bool, result: str = ""):
    """autolearn executor 执行后调用"""
    etype = "task" if ok else "error"
    return log_event(etype, f"autolearn.executor.{tool}", f"[{intent}] {'ok' if ok else 'fail'}: {result[:200]}", {
        "intent": intent,
        "tool": tool,
        "ok": ok,
    })


def on_retest(level: str, passed: int, failed: int):
    """autolearn retest 后调用"""
    ok = failed == 0
    return log_event("task" if ok else "error", "autolearn.retest", f"[{level}] {passed}P/{failed}F", {
        "level": level,
        "passed": passed,
        "failed": failed,
    })


def on_lesson(title: str, category: str, status: str):
    """教训沉淀后调用"""
    return log_event("lesson", "autolearn.lessons", f"[{status}] {title}", {
        "title": title,
        "category": category,
        "status": status,
    })


def on_circuit_breaker(sig: str, tripped: bool):
    """熔断器状态变化"""
    if tripped:
        return log_event("error", "autolearn.circuit_breaker", f"TRIPPED: {sig}", {
            "sig": sig,
        })


def on_http_error(source: str, url: str, status_code: int, detail: str = ""):
    """HTTP 错误（502/401/404 等）"""
    return log_event("http_error", source, f"HTTP {status_code}: {url}", {
        "url": url,
        "status_code": status_code,
        "detail": detail[:200],
    })


def on_health(source: str, ok: bool, checks: dict):
    """健康检查结果"""
    return log_event("health", source, f"{'PASS' if ok else 'FAIL'}", {
        "ok": ok,
        "checks": checks,
    })


def on_deploy(source: str, action: str, detail: str = ""):
    """版本/配置变更"""
    return log_event("deploy", source, f"[{action}] {detail[:200]}", {
        "action": action,
        "detail": detail[:500],
    })
