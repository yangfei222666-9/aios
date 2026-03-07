#!/usr/bin/env python3
"""
Phase 3 Observer - LowSuccess_Agent 自动观察脚本
每次重生自动记录统计，生成 Mermaid 图表报告

核心功能：
1. 记录每次重生（task_id/success/recovery_time）
2. 生成统计报告（成功率/平均恢复时间/观察样本数）
3. 生成 Mermaid 图表（饼图 + 流程图）
4. 无外部依赖（纯 Python + JSON）
"""

import json
from pathlib import Path
from datetime import datetime

# 路径配置
WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")
AIOS_DIR = WORKSPACE / "aios" / "agent_system"
PHASE3_LOG = AIOS_DIR / "phase3_observations.jsonl"
PHASE3_REPORT = AIOS_DIR / "reports" / "lowsuccess_phase3_report.md"

# 确保 reports 目录存在
(AIOS_DIR / "reports").mkdir(parents=True, exist_ok=True)

def observe_phase3(task_id: str, task_description: str, success: bool, recovery_time: float, agent_id: str = "LowSuccess_Agent"):
    """
    记录一次重生观察
    
    Args:
        task_id: 任务ID
        task_description: 任务描述
        success: 是否成功
        recovery_time: 恢复时间（秒）
        agent_id: 执行Agent ID
    """
    observation = {
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'agent_id': agent_id,
        'reborn_at': datetime.now().isoformat(),
        'outcome': 'success' if success else 'failed',
        'task_description': task_description,
        'success': success,
        'recovery_time': recovery_time
    }
    
    # 追加到观察日志
    with open(PHASE3_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(observation, ensure_ascii=False) + '\n')
    
    print(f"[PHASE3] Observed: {task_id} | Success: {success} | Time: {recovery_time:.2f}s")

def load_observations():
    """加载所有观察记录"""
    if not PHASE3_LOG.exists():
        return []
    
    observations = []
    with open(PHASE3_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                observations.append(json.loads(line))
            except:
                continue
    
    return observations

def calculate_stats(observations):
    """计算统计数据"""
    if not observations:
        return {
            'total': 0,
            'success': 0,
            'failed': 0,
            'success_rate': 0.0,
            'avg_recovery_time': 0.0
        }
    
    total = len(observations)
    success = sum(1 for o in observations if o.get('success', False))
    failed = total - success
    success_rate = (success / total) * 100 if total > 0 else 0.0
    
    recovery_times = [o.get('recovery_time', 0) for o in observations]
    avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else 0.0
    
    return {
        'total': total,
        'success': success,
        'failed': failed,
        'success_rate': success_rate,
        'avg_recovery_time': avg_recovery_time
    }

def generate_mermaid_pie_chart(stats):
    """生成 Mermaid 饼图"""
    return f"""```mermaid
pie title Phase 3 重生成功率
    "成功" : {stats['success']}
    "失败" : {stats['failed']}
```"""

def generate_mermaid_flowchart():
    """生成 Mermaid 流程图"""
    return """```mermaid
flowchart TD
    A[失败任务] --> B[LowSuccess_Agent 触发]
    B --> C[从 LanceDB 推荐历史成功策略]
    C --> D[生成 feedback + strategy]
    D --> E[创建 spawn 请求]
    E --> F[Heartbeat 执行真实 Agent]
    F --> G{成功?}
    G -->|是| H[保存到 LanceDB]
    G -->|否| I[需要人工介入]
    H --> J[Phase 3 观察：记录统计]
    I --> J
    J --> K[生成图表报告]
    K --> L[下次同类错误自动应用历史经验]
```"""

def generate_phase3_report():
    """生成 Phase 3 报告"""
    observations = load_observations()
    stats = calculate_stats(observations)
    
    # 生成报告
    report = f"""# LowSuccess_Agent Phase 3 观察报告

**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计数据

- **观察样本数：** {stats['total']}
- **重生成功：** {stats['success']}
- **重生失败：** {stats['failed']}
- **成功率：** {stats['success_rate']:.1f}%（目标 85%+）
- **平均恢复时间：** {stats['avg_recovery_time']:.2f}s

## 成功率分布

{generate_mermaid_pie_chart(stats)}

## 完整工作流

{generate_mermaid_flowchart()}

## 最近观察记录

| 时间 | 任务ID | 任务描述 | 成功 | 恢复时间 |
|------|--------|----------|------|----------|
"""
    
    # 添加最近10条记录
    recent = observations[-10:] if len(observations) > 10 else observations
    for obs in reversed(recent):
        timestamp = obs.get('timestamp', 'N/A')[:19]  # 只取日期时间部分
        task_id = obs.get('task_id', 'N/A')
        task_desc = obs.get('task_description', 'N/A')[:30]  # 截断长描述
        success = '✅' if obs.get('success', False) else '❌'
        recovery_time = obs.get('recovery_time', 0)
        
        report += f"| {timestamp} | {task_id} | {task_desc} | {success} | {recovery_time:.2f}s |\n"
    
    # 写入报告
    with open(PHASE3_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[OK] Phase 3 report generated: {PHASE3_REPORT}")
    print(f"  重生成功率: {stats['success_rate']:.1f}%（目标 85%+）")
    print(f"  平均恢复时间: {stats['avg_recovery_time']:.2f}s")
    print(f"  观察样本数: {stats['total']}")

def main():
    """主函数（用于测试）"""
    print("Phase 3 Observer - 生成报告")
    print("=" * 60)
    
    generate_phase3_report()

if __name__ == '__main__':
    main()
