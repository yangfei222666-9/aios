"""
Phase 2.5 Spawn Bridge - 桥接spawn_requests.jsonl到真实执行

这个脚本应该在OpenClaw主会话的heartbeat中调用，
因为只有OpenClaw主会话才能访问sessions_spawn工具。

使用方式：
在HEARTBEAT.md中添加：
```
if current_minute == 0:  # 每小时整点
    exec("cd C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system; python spawn_bridge.py")
```
"""
import json
import os
from pathlib import Path
from datetime import datetime


from paths import SPAWN_REQUESTS


def read_spawn_requests():
    """读取spawn_requests.jsonl"""
    spawn_file = SPAWN_REQUESTS
    
    if not spawn_file.exists():
        return []
    
    requests = []
    with open(spawn_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    requests.append(json.loads(line))
                except:
                    pass
    
    return requests


def generate_openclaw_commands():
    """
    生成OpenClaw可以执行的命令列表
    
    输出格式：
    SPAWN_REQUEST:task_id:label:task_description
    """
    requests = read_spawn_requests()
    
    if not requests:
        print("✅ [BRIDGE] 无待执行的spawn请求")
        return
    
    print(f"[BRIDGE] 发现 {len(requests)} 个spawn请求")
    print("=" * 60)
    
    for req in requests:
        task_id = req.get('task_id', 'unknown')
        label = req.get('label', 'LowSuccess_Regen')
        task = req.get('task', '')
        timeout = req.get('runTimeoutSeconds', 120)
        
        # 输出格式化的spawn命令
        print(f"SPAWN_REQUEST:{task_id}")
        print(f"  Label: {label}")
        print(f"  Timeout: {timeout}s")
        print(f"  Task: {task[:100]}...")
        print("-" * 60)
    
    print("=" * 60)
    print(f"[INFO] 请在OpenClaw主会话中执行以下命令来真实执行这些spawn请求：")
    print()
    print("sessions_spawn(")
    print(f"  task='执行spawn_requests.jsonl中的所有请求',")
    print(f"  label='spawn-bridge-executor',")
    print(f"  cleanup='keep',")
    print(f"  runTimeoutSeconds=300")
    print(")")


def mark_as_processed():
    """标记spawn请求为已处理（移动到历史文件）"""
    spawn_file = SPAWN_REQUESTS
    history_file = Path(__file__).parent / 'spawn_requests_history.jsonl'
    
    if not spawn_file.exists():
        return
    
    # 追加到历史文件
    with open(spawn_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(history_file, 'a', encoding='utf-8') as f:
        f.write(content)
    
    # 清空当前文件
    with open(spawn_file, 'w', encoding='utf-8') as f:
        f.write('')
    
    print(f"✅ [BRIDGE] spawn请求已移动到历史文件")


if __name__ == "__main__":
    generate_openclaw_commands()
