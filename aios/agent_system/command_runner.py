# command_runner.py - 带资源限制的命令执行器
from __future__ import annotations

import asyncio
import os
import signal
import time
import sys
from audit_context import audit_event_auto
from resource_limits import (
    DEFAULT_TASK_TIMEOUT_SEC,
    MAX_STDOUT_BYTES,
    MAX_STDERR_BYTES,
)


class CommandLimitExceeded(Exception):
    """命令执行超限异常"""
    pass


async def run_command_limited(
    cmd: str,
    *,
    cwd: str | None = None,
    timeout_sec: int = DEFAULT_TASK_TIMEOUT_SEC,
    max_stdout_bytes: int = MAX_STDOUT_BYTES,
    max_stderr_bytes: int = MAX_STDERR_BYTES,
    agent_id: str | None = None,
    session_id: str | None = None,
):
    """
    执行命令，带超时、输出限制、自动 kill
    
    Args:
        cmd: 命令字符串
        cwd: 工作目录
        timeout_sec: 超时时间（秒）
        max_stdout_bytes: stdout 最大字节数
        max_stderr_bytes: stderr 最大字节数
        agent_id: Agent ID（用于审计）
        session_id: Session ID（用于审计）
    
    Returns:
        (exit_code, stdout, stderr)
    
    Raises:
        CommandLimitExceeded: 超时或输出超限
    """
    start = time.time()
    
    # 创建子进程
    if sys.platform == "win32":
        # Windows: 不支持 preexec_fn
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    else:
        # Unix: 使用 process group 方便整组 kill
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setsid,
        )
    
    async def read_limited(stream, limit):
        """读取流，超限则抛异常"""
        chunks = []
        total = 0
        while True:
            chunk = await stream.read(4096)
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise CommandLimitExceeded(f"output exceeded {limit} bytes")
            chunks.append(chunk)
        return b"".join(chunks)
    
    try:
        # 并发读取 stdout/stderr，带超时
        stdout_task = asyncio.create_task(read_limited(proc.stdout, max_stdout_bytes))
        stderr_task = asyncio.create_task(read_limited(proc.stderr, max_stderr_bytes))
        
        stdout_b, stderr_b = await asyncio.wait_for(
            asyncio.gather(stdout_task, stderr_task),
            timeout=timeout_sec
        )
        
        rc = await proc.wait()
        duration_ms = int((time.time() - start) * 1000)
        
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")
        
        # 审计日志
        audit_event_auto(
            action_type="command.exec",
            target=cmd,
            params={
                "cwd": cwd,
                "timeout_sec": timeout_sec,
                "max_stdout_bytes": max_stdout_bytes,
                "max_stderr_bytes": max_stderr_bytes,
            },
            result="success" if rc == 0 else "failed",
            exit_code=rc,
            duration_ms=duration_ms,
            risk_level="medium" if rc == 0 else "high",
            extra={
                "stdout_preview": stdout[:1000],
                "stderr_preview": stderr[:1000],
            },
        )
        
        return rc, stdout, stderr
    
    except asyncio.TimeoutError:
        # 超时 kill
        if sys.platform == "win32":
            proc.kill()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        
        duration_ms = int((time.time() - start) * 1000)
        
        audit_event_auto(
            action_type="command.exec",
            target=cmd,
            params={"cwd": cwd, "timeout_sec": timeout_sec},
            result="killed",
            exit_code=None,
            duration_ms=duration_ms,
            risk_level="high",
            reason="timeout exceeded",
        )
        
        raise CommandLimitExceeded(f"Command timeout after {timeout_sec}s: {cmd}")
    
    except CommandLimitExceeded as e:
        # 输出超限 kill
        if sys.platform == "win32":
            proc.kill()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        
        duration_ms = int((time.time() - start) * 1000)
        
        audit_event_auto(
            action_type="command.exec",
            target=cmd,
            params={
                "cwd": cwd,
                "max_stdout_bytes": max_stdout_bytes,
                "max_stderr_bytes": max_stderr_bytes,
            },
            result="killed",
            exit_code=None,
            duration_ms=duration_ms,
            risk_level="high",
            reason=str(e),
        )
        
        raise


if __name__ == "__main__":
    # 测试
    from audit_context import set_audit_context
    
    async def test():
        set_audit_context("test-agent", "test-session")
        
        # 测试正常命令
        print("[TEST] Running normal command...")
        rc, stdout, stderr = await run_command_limited("echo hello", timeout_sec=5)
        print(f"[OK] Exit code: {rc}, stdout: {stdout.strip()}")
        
        # 测试超时命令（Windows 用 timeout，Unix 用 sleep）
        if sys.platform == "win32":
            timeout_cmd = "timeout /t 10"
        else:
            timeout_cmd = "sleep 10"
        
        print(f"\n[TEST] Running timeout command: {timeout_cmd}")
        try:
            await run_command_limited(timeout_cmd, timeout_sec=2)
        except CommandLimitExceeded as e:
            print(f"[OK] Caught timeout: {e}")
    
    asyncio.run(test())
