"""
Action Lock - 防止 Agent 互打的轻量级锁机制

核心功能：
1. 资源级锁（同一资源同时只能有一个 action）
2. 超时自动释放（防死锁）
3. Idempotency 检查（防重复执行）

Usage:
    from action_lock import ActionLock
    
    lock = ActionLock()
    if lock.acquire("service-api", "action-123", timeout=300):
        try:
            # 执行操作
            pass
        finally:
            lock.release("service-api", "action-123")
"""

import json
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any

from paths import LOCKS_DIR, EXECUTED_ACTIONS

LOCK_DIR = LOCKS_DIR
EXECUTED_ACTIONS_FILE = EXECUTED_ACTIONS


class ActionLock:
    """轻量级 Action 锁管理器"""
    
    def __init__(self):
        self.locks: Dict[str, Any] = {}
    
    def acquire(self, resource_id: str, action_id: str, timeout: int = 300) -> bool:
        """
        获取资源锁
        
        Args:
            resource_id: 资源标识（如 "service-api", "coder-dispatcher"）
            action_id: 动作标识（如 "action-123"）
            timeout: 超时时间（秒），默认 5 分钟
        
        Returns:
            True: 获取成功
            False: 资源被占用或已执行过
        """
        # 1. Idempotency 检查
        if self._is_executed(action_id):
            print(f"[LOCK] Action {action_id} already executed (idempotent)")
            return False
        
        # 2. 检查现有锁
        lock_file = LOCK_DIR / f"{resource_id}.lock"
        
        # 3. 尝试获取锁
        if lock_file.exists():
            lock_data = self._read_lock(lock_file)
            if lock_data:
                # 检查是否超时（使用锁自己的 timeout，不是当前请求的 timeout）
                age = time.time() - lock_data.get("timestamp", 0)
                lock_timeout = lock_data.get("timeout", 300)
                if age < lock_timeout:
                    print(f"[LOCK] Resource {resource_id} locked by {lock_data.get('action_id')} ({age:.1f}s ago)")
                    return False
                else:
                    print(f"[LOCK] Stale lock detected ({age:.1f}s), recovering...")
                    self._remove_lock(lock_file)
        
        # 4. 创建新锁
        lock_data = {
            "resource_id": resource_id,
            "action_id": action_id,
            "timestamp": time.time(),
            "timeout": timeout
        }
        
        self._write_lock(lock_file, lock_data)
        print(f"[LOCK] Acquired lock for {resource_id} (action: {action_id})")
        return True
    
    def release(self, resource_id: str, action_id: str, success: bool = True):
        """
        释放资源锁
        
        Args:
            resource_id: 资源标识
            action_id: 动作标识
            success: 是否执行成功（成功则记录到 executed_actions）
        """
        lock_file = LOCK_DIR / f"{resource_id}.lock"
        
        # 验证锁的所有者
        if lock_file.exists():
            lock_data = self._read_lock(lock_file)
            if lock_data and lock_data.get("action_id") == action_id:
                self._remove_lock(lock_file)
                print(f"[LOCK] Released lock for {resource_id} (action: {action_id})")
                
                # 记录已执行（仅成功时）
                if success:
                    self._mark_executed(action_id, resource_id)
            else:
                print(f"[LOCK] Warning: Lock owner mismatch for {resource_id}")
    
    def _is_executed(self, action_id: str) -> bool:
        """检查 action 是否已执行过"""
        if not EXECUTED_ACTIONS_FILE.exists():
            return False
        
        with open(EXECUTED_ACTIONS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get("action_id") == action_id:
                        return True
                except:
                    continue
        return False
    
    def _mark_executed(self, action_id: str, resource_id: str):
        """标记 action 为已执行"""
        record = {
            "action_id": action_id,
            "resource_id": resource_id,
            "timestamp": time.time()
        }
        
        with open(EXECUTED_ACTIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _read_lock(self, lock_file: Path) -> Optional[Dict]:
        """读取锁文件"""
        try:
            with open(lock_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    
    def _write_lock(self, lock_file: Path, data: Dict):
        """写入锁文件（原子操作）"""
        tmp_file = lock_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 原子重命名
        tmp_file.replace(lock_file)
    
    def _remove_lock(self, lock_file: Path):
        """删除锁文件"""
        try:
            lock_file.unlink()
        except:
            pass
    
    def cleanup_stale_locks(self, max_age: int = 3600):
        """清理过期锁（默认 1 小时）"""
        cleaned = 0
        for lock_file in LOCK_DIR.glob("*.lock"):
            lock_data = self._read_lock(lock_file)
            if lock_data:
                age = time.time() - lock_data.get("timestamp", 0)
                if age > max_age:
                    self._remove_lock(lock_file)
                    cleaned += 1
                    print(f"[LOCK] Cleaned stale lock: {lock_file.stem} ({age:.1f}s old)")
        
        if cleaned > 0:
            print(f"[LOCK] Cleaned {cleaned} stale locks")
        return cleaned


def test_action_lock():
    """测试 Action Lock"""
    print("=== Testing Action Lock ===\n")
    
    lock = ActionLock()
    
    # Test 1: 正常获取和释放
    print("Test 1: Normal acquire/release")
    assert lock.acquire("service-api", "action-001", timeout=10)
    lock.release("service-api", "action-001", success=True)
    print("✓ Test 1 passed\n")
    
    # Test 2: Idempotency（重复执行）
    print("Test 2: Idempotency check")
    assert not lock.acquire("service-api", "action-001", timeout=10)
    print("✓ Test 2 passed\n")
    
    # Test 3: 资源冲突
    print("Test 3: Resource conflict")
    assert lock.acquire("service-api", "action-002", timeout=10)
    assert not lock.acquire("service-api", "action-003", timeout=10)
    lock.release("service-api", "action-002", success=True)
    print("✓ Test 3 passed\n")
    
    # Test 4: 超时恢复
    print("Test 4: Timeout recovery")
    assert lock.acquire("service-api", "action-004", timeout=1)
    time.sleep(2)
    assert lock.acquire("service-api", "action-005", timeout=10)
    lock.release("service-api", "action-005", success=True)
    print("✓ Test 4 passed\n")
    
    # Test 5: 清理过期锁
    print("Test 5: Cleanup stale locks")
    lock.acquire("service-api", "action-006", timeout=1)
    time.sleep(2)
    cleaned = lock.cleanup_stale_locks(max_age=1)
    assert cleaned >= 1
    print("✓ Test 5 passed\n")
    
    print("=== All tests passed! ===")


if __name__ == "__main__":
    test_action_lock()
