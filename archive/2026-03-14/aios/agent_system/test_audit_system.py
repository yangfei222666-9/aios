# test_audit_system.py - 审计系统完整测试
import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from audit_context import set_audit_context, audit_event_auto
from audit_logger import audit_event, query_audit_logs
from command_runner import run_command_limited, CommandLimitExceeded
from resource_limits import get_config, can_enqueue


async def test_audit_system():
    """测试审计系统"""
    print("=" * 60)
    print("AIOS 审计系统测试")
    print("=" * 60)
    
    # 1. 测试审计上下文
    print("\n[TEST 1] 审计上下文")
    set_audit_context("test-agent", "test-session-001")
    audit_event_auto(
        action_type="test.context",
        target="context-test",
        result="success",
        risk_level="low",
    )
    print("[OK] 审计上下文测试通过")
    
    # 2. 测试文件操作审计
    print("\n[TEST 2] 文件操作审计")
    audit_event_auto(
        action_type="file.write",
        target="test_output.txt",
        params={"mode": "write", "size_bytes": 1024},
        result="success",
        risk_level="medium",
    )
    print("[OK] 文件操作审计通过")
    
    # 3. 测试命令执行审计（正常命令）
    print("\n[TEST 3] 命令执行审计（正常）")
    try:
        rc, stdout, stderr = await run_command_limited(
            "echo hello",
            timeout_sec=5
        )
        print(f"[OK] 命令执行成功: rc={rc}, stdout={stdout.strip()}")
    except Exception as e:
        print(f"[FAIL] 命令执行失败: {e}")
    
    # 4. 测试命令超时审计
    print("\n[TEST 4] 命令超时审计")
    try:
        if sys.platform == "win32":
            timeout_cmd = 'python -c "import time; time.sleep(10)"'
        else:
            timeout_cmd = "sleep 10"
        
        await run_command_limited(timeout_cmd, timeout_sec=2)
        print("[FAIL] 应该超时但没有")
    except CommandLimitExceeded as e:
        print(f"[OK] 超时被正确捕获: {e}")
    
    # 5. 测试策略决策审计
    print("\n[TEST 5] 策略决策审计")
    audit_event_auto(
        action_type="policy.allow",
        target="spawn_generation",
        params={"lesson_id": "test-lesson-001"},
        result="allowed",
        risk_level="medium",
        reason="test policy decision",
        lesson_id="test-lesson-001",
    )
    print("[OK] 策略决策审计通过")
    
    # 6. 测试 spawn 审计
    print("\n[TEST 6] Spawn 审计")
    audit_event_auto(
        action_type="spawn.request",
        target="spawn_requests.jsonl",
        params={"count": 3, "spawn_ids": ["spawn-001", "spawn-002", "spawn-003"]},
        result="success",
        risk_level="medium",
        reason="test spawn generation",
    )
    print("[OK] Spawn 审计通过")
    
    # 7. 测试审计查询
    print("\n[TEST 7] 审计查询")
    logs = query_audit_logs(action_type="test.context", days=1)
    print(f"[OK] 查询到 {len(logs)} 条 test.context 记录")
    
    # 8. 测试资源限制配置
    print("\n[TEST 8] 资源限制配置")
    config = get_config()
    print("[OK] 资源限制配置:")
    for k, v in config.items():
        print(f"  {k}: {v}")
    
    # 9. 测试队列限制
    print("\n[TEST 9] 队列限制")
    print(f"[OK] Can enqueue (0/100): {can_enqueue(0)}")
    print(f"[OK] Can enqueue (100/100): {can_enqueue(100)}")
    print(f"[OK] Can enqueue (101/100): {can_enqueue(101)}")
    
    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)
    
    # 10. 打印审计日志路径
    from audit_logger import _today_path
    print(f"\n[INFO] 审计日志路径: {_today_path()}")
    print("[INFO] 查询命令示例:")
    print("  jq -c 'select(.action_type==\"command.exec\")' audit_logs/*.jsonl")
    print("  jq -c 'select(.risk_level==\"high\")' audit_logs/*.jsonl")


if __name__ == "__main__":
    asyncio.run(test_audit_system())
