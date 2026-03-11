#!/usr/bin/env python3
"""Agent 分层分类器 - 严格唯一归属"""

import json
from pathlib import Path

def classify_agents():
    """对 30 个 Agent 进行严格分层"""
    
    # 读取 agents.json
    agents_path = Path(__file__).parent / "data" / "agents.json"
    with open(agents_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 读取 execution_record
    exec_path = Path(__file__).parent / "data" / "agent_execution_record.jsonl"
    exec_records = {}
    if exec_path.exists():
        with open(exec_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    agent_name = record.get('agent_name')
                    if agent_name:
                        if agent_name not in exec_records:
                            exec_records[agent_name] = []
                        exec_records[agent_name].append(record)
    
    # 分层
    real_chain = []
    candidate = []
    dormant = []
    
    for agent in data['agents']:
        name = agent['name']
        enabled = agent.get('enabled', False)
        mode = agent.get('mode', 'unknown')
        routable = agent.get('routable', False)
        production_ready = agent.get('production_ready', False)
        validated = agent.get('validation_status') == 'validated'
        
        # 检查执行记录（两个来源）
        has_exec_record = name in exec_records
        exec_record_count = len(exec_records.get(name, []))
        
        # 检查 stats（dispatcher 的执行记录在这里）
        stats = agent.get('stats', {})
        stats_total = stats.get('tasks_total', 0)
        
        # 综合判断：有 execution_record 或 stats.tasks_total > 0
        has_exec = has_exec_record or stats_total > 0
        exec_count = max(exec_record_count, stats_total)
        
        # 分层逻辑
        if has_exec and exec_count > 0:
            # 有真实执行记录 → 真链
            evidence = f'{exec_count} execution records'
            if validated:
                evidence += ', validated'
            real_chain.append({
                'agent_name': name,
                'tier': 'real_chain',
                'evidence': evidence,
                'notes': f'production_ready={production_ready}, mode={mode}'
            })
        elif enabled and routable and mode == 'active':
            # 已注册、可路由、但从未执行 → 候选链
            evidence = 'registered, enabled, routable, never executed'
            candidate.append({
                'agent_name': name,
                'tier': 'candidate',
                'evidence': evidence,
                'notes': f'production_ready={production_ready}, needs execution script'
            })
        else:
            # disabled 或 shadow → 休眠壳
            evidence = f'mode={mode}, enabled={enabled}'
            dormant.append({
                'agent_name': name,
                'tier': 'dormant',
                'evidence': evidence,
                'notes': 'no execution plan'
            })
    
    # 验证总数
    total = len(real_chain) + len(candidate) + len(dormant)
    
    print('分层统计：')
    print(f'  真链：{len(real_chain)}')
    print(f'  候选链：{len(candidate)}')
    print(f'  休眠壳：{len(dormant)}')
    print(f'  总计：{total} (预期 30)')
    print()
    
    # 输出每层详情
    print('=== 真链 ===')
    for a in real_chain:
        print(f'{a["agent_name"]}: {a["evidence"]}')
    print()
    
    print('=== 候选链 ===')
    for a in candidate:
        print(f'{a["agent_name"]}: {a["evidence"]}')
    print()
    
    print('=== 休眠壳 ===')
    for a in dormant:
        print(f'{a["agent_name"]}: {a["evidence"]}')
    print()
    
    # 返回结果
    return {
        'real_chain': real_chain,
        'candidate': candidate,
        'dormant': dormant,
        'summary': {
            'real_chain_count': len(real_chain),
            'candidate_count': len(candidate),
            'dormant_count': len(dormant),
            'total': total
        }
    }

if __name__ == '__main__':
    result = classify_agents()
    
    # 写入 agent_tiers.json
    output_path = Path(__file__).parent / "agent_tiers.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f'✅ 分层结果已写入：{output_path}')
