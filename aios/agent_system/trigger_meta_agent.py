"""
触发 Meta-Agent 缺口检测的场景生成器
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))

from auto_dispatcher import AutoDispatcher

def create_failure_pattern():
    """创建失败模式（触发缺口检测）"""
    workspace = Path(__file__).parent.parent.parent
    dispatcher = AutoDispatcher(workspace)
    
    print("=" * 60)
    print("[FIRE] 创建失败模式（触发 Meta-Agent 缺口检测）")
    print("=" * 60)
    
    # 场景 1：某类任务频繁失败（≥3次/7天）
    print("\n场景 1：数据库任务频繁失败")
    for i in range(5):
        task = {
            "type": "database",
            "message": f"数据库备份任务 #{i+1}",
            "priority": "high"
        }
        dispatcher.enqueue_task(task)
        print(f"  ✓ 入队: {task['message']}")
    
    # 场景 2：某类任务积压超过 1 小时
    print("\n场景 2：安全审计任务积压")
    for i in range(3):
        task = {
            "type": "security",
            "message": f"安全审计任务 #{i+1}",
            "priority": "normal"
        }
        dispatcher.enqueue_task(task)
        print(f"  ✓ 入队: {task['message']}")
    
    # 场景 3：新类型任务（没有对应 Agent）
    print("\n场景 3：新类型任务（deployment）")
    for i in range(2):
        task = {
            "type": "deployment",
            "message": f"部署任务 #{i+1}",
            "priority": "high"
        }
        dispatcher.enqueue_task(task)
        print(f"  ✓ 入队: {task['message']}")
    
    print("\n" + "=" * 60)
    print("[OK] 场景创建完成")
    print("=" * 60)
    print(f"总任务数: {dispatcher.status()['queue_size']}")
    print("\n下一步：运行 meta_agent.py heartbeat 检测缺口")


def create_event_pattern():
    """创建事件模式（触发事件覆盖缺口）"""
    from paths import EVENTS_LOG
    events_file = EVENTS_LOG
    
    print("\n" + "=" * 60)
    print("[REPORT] 创建事件模式（触发事件覆盖缺口）")
    print("=" * 60)
    
    # 创建未处理的事件
    events = []
    
    # 场景 1：资源告警事件（未处理率 >50%）
    for i in range(10):
        event = {
            "type": "resource.alert",
            "source": "monitor",
            "payload": {
                "alert_type": "high_cpu",
                "value": 85 + i,
                "threshold": 80
            },
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat()
        }
        events.append(event)
    
    # 场景 2：错误事件（未处理）
    for i in range(5):
        event = {
            "type": "error.critical",
            "source": "application",
            "payload": {
                "error_type": "database_connection_failed",
                "message": f"Database connection timeout #{i+1}"
            },
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat()
        }
        events.append(event)
    
    # 追加到 events.jsonl
    with open(events_file, 'a', encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"[OK] 创建了 {len(events)} 个事件")
    print(f"   - 资源告警: 10 个")
    print(f"   - 错误事件: 5 个")
    print(f"\n下一步：运行 meta_agent.py heartbeat 检测缺口")


if __name__ == "__main__":
    create_failure_pattern()
    create_event_pattern()
