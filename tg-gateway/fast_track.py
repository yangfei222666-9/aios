# tg-gateway/fast_track.py - 快车道执行器
"""
本地执行简单命令（打开/关闭应用），不经过 LLM。
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "aios"))
from core.executor import execute, SUCCESS, NOOP_ALREADY_RUNNING, NOOP_DEDUP
from core.app_alias import action_summary


def _open_app(exe_path: str):
    """启动应用"""
    def _do():
        try:
            subprocess.Popen(exe_path, shell=True)
            return True, f"已启动 {exe_path}"
        except Exception as e:
            return False, str(e)
    return _do


def _close_app(process_name: str):
    """关闭应用"""
    def _do():
        try:
            r = subprocess.run(
                ["taskkill", "/IM", process_name, "/F"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                return True, f"已关闭 {process_name}"
            return False, r.stderr.strip() or r.stdout.strip()
        except Exception as e:
            return False, str(e)
    return _do


def execute_fast(resolve_result: dict) -> str:
    """
    执行快车道命令，返回用户可见的回复文本。
    """
    action = resolve_result["action"]
    canonical = resolve_result["canonical"]
    exe_path = resolve_result.get("exe_path")
    process_name = resolve_result.get("process_name")
    command_key = f"{action}_{canonical}"

    if action == "open":
        if not exe_path:
            return f"找不到 {canonical} 的启动路径"
        result = execute(
            command_key, _open_app(exe_path),
            dedup_window=30,
            process_name=process_name
        )
    elif action == "close":
        if not process_name:
            return f"找不到 {canonical} 的进程名"
        result = execute(command_key, _close_app(process_name), dedup_window=10)
    else:
        return f"不支持的操作: {action}"

    state = result.get("terminal_state", "")
    if state == SUCCESS:
        return action_summary(resolve_result["raw"])
    elif state == NOOP_ALREADY_RUNNING:
        return f"{canonical} 已经在运行了"
    elif state == NOOP_DEDUP:
        return f"刚刚已经执行过了"
    else:
        detail = result.get("detail", "未知错误")
        return f"执行失败: {detail}"
