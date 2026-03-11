#!/usr/bin/env python3
"""
Self-Improving Loop - 生产级自动改进

集成到 heartbeat 中，定期检查所有 Agent 的健康状况并自动改进。

使用方式：
    python run_self_improving.py [--agent-id AGENT_ID] [--dry-run]

参数：
    --agent-id: 指定 Agent ID（可选，默认检查所有 Agent）
    --dry-run: 只分析不应用改进
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from src.self_improving_loop import SelfImprovingLoop, TraceAnalyzer

AIOS_ROOT = Path(__file__).resolve().parent


def check_agent_health(agent_id: str, trace_analyzer: TraceAnalyzer) -> dict:
    """检查单个 Agent 的健康状况"""
    agent_traces = [t for t in trace_analyzer.traces if t["agent_id"] == agent_id]
    
    if not agent_traces:
        return {
            "agent_id": agent_id,
            "status": "no_data",
            "total_tasks": 0,
            "success_rate": 0.0,
            "needs_improvement": False
        }
    
    total = len(agent_traces)
    successes = sum(1 for t in agent_traces if t.get("success"))
    success_rate = successes / total if total > 0 else 0.0
    
    # 判断是否需要改进（成功率 < 70%）
    needs_improvement = success_rate < 0.7 and total >= 3
    
    return {
        "agent_id": agent_id,
        "status": "healthy" if success_rate >= 0.7 else "unhealthy",
        "total_tasks": total,
        "success_rate": success_rate,
        "needs_improvement": needs_improvement
    }


def run_self_improving(agent_id: str = None, dry_run: bool = False):
    """运行自动改进"""
    print("=" * 60)
    print("Self-Improving Loop - 自动改进")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模式: {'Dry-Run（只分析）' if dry_run else '生产模式（会应用改进）'}")
    print()
    
    # 初始化
    loop = SelfImprovingLoop()
    trace_analyzer = TraceAnalyzer()
    
    # 获取所有 Agent
    if agent_id:
        agent_ids = [agent_id]
    else:
        # 从 traces 中提取所有 Agent ID
        agent_ids = list(set(t["agent_id"] for t in trace_analyzer.traces))
    
    if not agent_ids:
        print("❌ 没有找到任何 Agent 数据")
        return
    
    print(f"📊 检查 {len(agent_ids)} 个 Agent...\n")
    
    # 检查每个 Agent
    results = []
    for aid in agent_ids:
        health = check_agent_health(aid, trace_analyzer)
        results.append(health)
        
        status_icon = "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "unhealthy" else "❓"
        print(f"{status_icon} {aid}")
        print(f"   任务数: {health['total_tasks']} | 成功率: {health['success_rate']:.1%}")
        
        if health["needs_improvement"]:
            print(f"   🔧 需要改进")
            
            if not dry_run:
                # 触发改进（通过模拟一次失败任务）
                def mock_failure():
                    raise Exception("触发改进检查")
                
                try:
                    result = loop.execute_with_improvement(
                        agent_id=aid,
                        task="健康检查触发改进",
                        execute_fn=mock_failure
                    )
                    
                    if result["improvement_applied"] > 0:
                        print(f"   ✅ 应用了 {result['improvement_applied']} 项改进")
                    else:
                        print(f"   ℹ️ 未触发改进（可能在冷却期）")
                except Exception as e:
                    print(f"   ❌ 改进失败: {e}")
        print()
    
    # 汇总统计
    print("=" * 60)
    print("汇总统计")
    print("=" * 60)
    
    healthy = sum(1 for r in results if r["status"] == "healthy")
    unhealthy = sum(1 for r in results if r["status"] == "unhealthy")
    no_data = sum(1 for r in results if r["status"] == "no_data")
    needs_improvement = sum(1 for r in results if r["needs_improvement"])
    
    print(f"✅ 健康: {healthy}")
    print(f"⚠️ 不健康: {unhealthy}")
    print(f"❓ 无数据: {no_data}")
    print(f"🔧 需要改进: {needs_improvement}")
    
    # 查看全局改进统计
    global_stats = loop.get_improvement_stats()
    print(f"\n📈 总改进次数: {global_stats['total_improvements']}")
    print(f"📋 已改进 Agent: {len(global_stats['agents_improved'])}")
    
    if not dry_run and needs_improvement > 0:
        print(f"\n✅ 自动改进完成")
    elif dry_run and needs_improvement > 0:
        print(f"\n⚠️ Dry-Run 模式，未应用改进")
    else:
        print(f"\n✅ 所有 Agent 健康，无需改进")


def main():
    parser = argparse.ArgumentParser(description="Self-Improving Loop - 自动改进")
    parser.add_argument("--agent-id", help="指定 Agent ID")
    parser.add_argument("--dry-run", action="store_true", help="只分析不应用改进")
    
    args = parser.parse_args()
    
    try:
        run_self_improving(agent_id=args.agent_id, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
