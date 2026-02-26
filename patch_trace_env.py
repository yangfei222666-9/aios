#!/usr/bin/env python3
"""给历史 trace 数据打 env 补丁"""

import json
from pathlib import Path

TRACE_LOG = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\traces\agent_traces.jsonl")

if not TRACE_LOG.exists():
    print("❌ trace 文件不存在")
    exit(1)

# 读取所有记录
lines = []
with open(TRACE_LOG, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            trace = json.loads(line.strip())
            
            # 如果没有 env 字段，根据 agent_id 推断
            if 'env' not in trace:
                agent_id = trace.get('agent_id', '')
                if 'test' in agent_id.lower():
                    trace['env'] = 'test'
                else:
                    trace['env'] = 'prod'
            
            lines.append(json.dumps(trace, ensure_ascii=False))
        except json.JSONDecodeError:
            continue

# 写回
with open(TRACE_LOG, 'w', encoding='utf-8') as f:
    for line in lines:
        f.write(line + '\n')

print(f"✅ 已更新 {len(lines)} 条记录")
