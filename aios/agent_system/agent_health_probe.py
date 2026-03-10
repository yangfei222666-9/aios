#!/usr/bin/env python3
"""
Agent 健康探测 - 区分"未上报"和"已死亡"
修正版：使用 mode + enabled 字段，不再使用已废弃的 status 字段
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

def load_agents():
    """加载 agents.json"""
    from paths import AGENTS_STATE
    agents_file = AGENTS_STATE
    if not agents_file.exists():
        return []
    with open(agents_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('agents', [])

def check_state_files():
    """检查 state/ 目录下的状态文件"""
    state_dir = Path(__file__).parent / "state"
    if not state_dir.exists():
        return {}
    
    state_files = {}
    for f in state_dir.glob("*_state.json"):
        agent_id = f.stem.replace("_state", "")
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                state_files[agent_id] = {
                    'file': str(f),
                    'last_modified': datetime.fromtimestamp(f.stat().st_mtime),
                    'data': data
                }
        except:
            pass
    return state_files

def check_task_executions():
    """检查 task_executions_v2.jsonl 中的最近活动"""
    from paths import TASK_EXECUTIONS
    exec_file = TASK_EXECUTIONS
    if not exec_file.exists():
        return {}
    
    agent_activity = {}
    cutoff = datetime.now() - timedelta(hours=24)
    
    with open(exec_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                agent_id = record.get('agent_id', '')
                timestamp = datetime.fromisoformat(record.get('timestamp', ''))
                
                if timestamp > cutoff:
                    if agent_id not in agent_activity:
                        agent_activity[agent_id] = []
                    agent_activity[agent_id].append({
                        'timestamp': timestamp,
                        'status': record.get('status', 'unknown')
                    })
            except:
                continue
    
    return agent_activity

def probe_agents():
    """探测所有 agent 的健康状态"""
    agents = load_agents()
    state_files = check_state_files()
    activity = check_task_executions()
    
    results = {
        'alive': [],      # 有状态文件 + 24h内有活动
        'dormant': [],    # 有状态文件但无活动
        'missing': [],    # 无状态文件但有活动记录
        'dead': [],       # 无状态文件 + 无活动
        'shadow': [],     # mode=shadow（已注册未启用）
        'disabled': []    # mode=disabled（已禁用）
    }
    
    for agent in agents:
        agent_id = agent.get('id', agent.get('name', ''))  # 兼容：优先用 id，没有则用 name
        mode = agent.get('mode', 'active')
        enabled = agent.get('enabled', True)
        
        has_state = agent_id in state_files
        has_activity = agent_id in activity
        
        # 先按 mode 分类
        if mode == 'shadow':
            results['shadow'].append({
                'id': agent_id,
                'name': agent.get('name', ''),
                'enabled': enabled,
                'has_state': has_state,
                'has_activity': has_activity
            })
            continue
        elif mode == 'disabled':
            results['disabled'].append({
                'id': agent_id,
                'name': agent.get('name', ''),
                'enabled': enabled,
                'has_state': has_state,
                'has_activity': has_activity
            })
            continue
        
        # mode=active 的 agent 才判断 alive/dormant/missing/dead
        if has_state and has_activity:
            results['alive'].append({
                'id': agent_id,
                'name': agent.get('name', ''),
                'mode': mode,
                'enabled': enabled,
                'last_seen': max(a['timestamp'] for a in activity[agent_id]).isoformat(),
                'state_file': state_files[agent_id]['file']
            })
        elif has_state and not has_activity:
            results['dormant'].append({
                'id': agent_id,
                'name': agent.get('name', ''),
                'mode': mode,
                'enabled': enabled,
                'state_modified': state_files[agent_id]['last_modified'].isoformat(),
                'state_file': state_files[agent_id]['file']
            })
        elif not has_state and has_activity:
            results['missing'].append({
                'id': agent_id,
                'name': agent.get('name', ''),
                'mode': mode,
                'enabled': enabled,
                'last_activity': max(a['timestamp'] for a in activity[agent_id]).isoformat()
            })
        else:
            results['dead'].append({
                'id': agent_id,
                'name': agent.get('name', ''),
                'mode': mode,
                'enabled': enabled
            })
    
    return results

def main():
    print("🔍 Agent 健康探测开始...\n")
    
    results = probe_agents()
    
    print(f"✅ 存活 (Alive): {len(results['alive'])} 个")
    for agent in results['alive'][:5]:  # 只显示前5个
        print(f"   - {agent['name']} ({agent['id']})")
        print(f"     最后活动: {agent.get('last_seen', 'N/A')}")
    if len(results['alive']) > 5:
        print(f"   ... 还有 {len(results['alive']) - 5} 个")
    
    print(f"\n😴 休眠 (Dormant): {len(results['dormant'])} 个")
    for agent in results['dormant']:
        print(f"   - {agent['name']} ({agent['id']})")
        print(f"     状态文件: {agent['state_file']}")
        print(f"     最后修改: {agent['state_modified']}")
    
    print(f"\n⚠️  缺失状态文件 (Missing State): {len(results['missing'])} 个")
    for agent in results['missing']:
        print(f"   - {agent['name']} ({agent['id']})")
        print(f"     最后活动: {agent['last_activity']}")
    
    print(f"\n💀 疑似死亡 (Dead): {len(results['dead'])} 个")
    for agent in results['dead']:
        print(f"   - {agent['name']} ({agent['id']})")
    
    print(f"\n🌑 Shadow 模式: {len(results['shadow'])} 个（已注册未启用）")
    for agent in results['shadow'][:5]:
        print(f"   - {agent['name']} ({agent['id']})")
    if len(results['shadow']) > 5:
        print(f"   ... 还有 {len(results['shadow']) - 5} 个")
    
    print(f"\n🚫 Disabled 模式: {len(results['disabled'])} 个（已禁用）")
    for agent in results['disabled'][:5]:
        print(f"   - {agent['name']} ({agent['id']})")
    if len(results['disabled']) > 5:
        print(f"   ... 还有 {len(results['disabled']) - 5} 个")
    
    # 保存结果
    from paths import AGENT_HEALTH_REPORT
    output_file = AGENT_HEALTH_REPORT
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'alive': len(results['alive']),
                'dormant': len(results['dormant']),
                'missing': len(results['missing']),
                'dead': len(results['dead']),
                'shadow': len(results['shadow']),
                'disabled': len(results['disabled'])
            },
            'details': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 详细报告已保存: {output_file}")
    
    # 返回状态码
    if results['dead']:
        print("\n⚠️  发现疑似死亡的 agent，建议人工检查")
        return 1
    elif results['missing']:
        print("\n⚠️  发现缺失状态文件的 agent，建议补充上报机制")
        return 1
    else:
        print("\n✅ 所有 routable agent 状态正常")
        print(f"   Shadow: {len(results['shadow'])} | Disabled: {len(results['disabled'])} (符合预期)")
        return 0

if __name__ == '__main__':
    exit(main())
