#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试健康报告输出
"""
import sys
from pathlib import Path

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from heartbeat_v5 import _print_learning_agents_status

print("=" * 60)
print("健康报告输出测试")
print("=" * 60)
print()

_print_learning_agents_status()

print("=" * 60)
print("测试完成")
print("=" * 60)
