#!/usr/bin/env python3
"""测试真实执行"""
import sys
from pathlib import Path

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.task_submitter import submit_task

# 提交一个简单测试任务
task_id = submit_task(
    description="测试真实执行：输出 'Hello from AIOS'",
    task_type="code",
    priority="high"
)

print(f"Task submitted: {task_id}")
print("Run: python heartbeat_v5.py")
