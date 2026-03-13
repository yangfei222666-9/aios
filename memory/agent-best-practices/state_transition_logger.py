#!/usr/bin/env python3
"""
状态转换日志记录器 - 实现示例
基于 2026-03-13 最佳实践研究

功能：
1. 记录所有状态转换到 state_transitions.jsonl
2. 提供查询接口
3. 生成统计报告
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 路径配置
BASE = Path(__file__).parent
STATE_TRANSITIONS_LOG = BASE / "data" / "state_transitions.jsonl"


class StateTransitionLogger:
    """状态转换日志记录器"""

    def __init__(self, log_path: Path = STATE_TRANSITIONS_LOG):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_transition(
        self,
        agent_id: str,
        from_state: str,
        to_state: str,
        reason: str,
        trigger: str = "auto",
        cooldown_until: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        记录状态转换

        Args:
            agent_id: Agent ID
            from_state: 原状态
            to_state: 新状态
            reason: 转换原因
            trigger: 触发方式 (auto/manual)
            cooldown_until: Cooldown 结束时间
            metadata: 额外元数据（如 failure_rate, streak）
        """
        entry = {
            "ts": datetime.now().isoformat(),
            "agent_id": agent_id,
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
            "trigger": trigger,
            "cooldown_until": cooldown_until,
            "metadata": metadata or {},
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"✅ 状态转换已记录: {agent_id} {from_state} → {to_state}")

    def get_history(
        self, agent_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """
        获取转换历史

        Args:
            agent_id: 可选，只返回特定 Agent 的历史
            limit: 最多返回多少条

        Returns:
            转换记录列表（最新的在前）
        """
        if not self.log_path.exists():
            return []

        records = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if agent_id is None or record.get("agent_id") == agent_id:
                        records.append(record)
                except json.JSONDecodeError:
                    continue

        # 最新的在前
        records.reverse()
        return records[:limit]

    def get_stats(self, days: int = 7) -> Dict:
        """
        生成统计报告

        Args:
            days: 统计最近多少天

        Returns:
            统计数据
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        records = self.get_history(limit=10000)

        # 过滤时间范围
        recent = [
            r
            for r in records
            if datetime.fromisoformat(r["ts"]) > cutoff
        ]

        # 统计
        stats = {
            "total_transitions": len(recent),
            "by_agent": {},
            "by_transition": {},
            "by_trigger": {"auto": 0, "manual": 0},
            "degradations": 0,  # active → shadow/disabled
            "recoveries": 0,  # shadow → active
        }

        for r in recent:
            agent_id = r["agent_id"]
            from_state = r["from_state"]
            to_state = r["to_state"]
            trigger = r["trigger"]
            transition = f"{from_state} → {to_state}"

            # 按 Agent 统计
            if agent_id not in stats["by_agent"]:
                stats["by_agent"][agent_id] = 0
            stats["by_agent"][agent_id] += 1

            # 按转换类型统计
            if transition not in stats["by_transition"]:
                stats["by_transition"][transition] = 0
            stats["by_transition"][transition] += 1

            # 按触发方式统计
            stats["by_trigger"][trigger] = stats["by_trigger"].get(trigger, 0) + 1

            # 降级/恢复统计
            if from_state == "active" and to_state in ["shadow", "disabled"]:
                stats["degradations"] += 1
            elif from_state == "shadow" and to_state == "active":
                stats["recoveries"] += 1

        return stats


# ── CLI ──

if __name__ == "__main__":
    import sys

    logger = StateTransitionLogger()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python state_transition_logger.py log <agent_id> <from> <to> <reason>")
        print("  python state_transition_logger.py history [agent_id]")
        print("  python state_transition_logger.py stats [days]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "log":
        if len(sys.argv) < 6:
            print("错误: log 需要 4 个参数")
            sys.exit(1)

        agent_id = sys.argv[2]
        from_state = sys.argv[3]
        to_state = sys.argv[4]
        reason = sys.argv[5]

        logger.log_transition(agent_id, from_state, to_state, reason)

    elif command == "history":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else None
        history = logger.get_history(agent_id, limit=20)

        print(f"\n📜 状态转换历史 (最近 20 条)")
        if agent_id:
            print(f"   Agent: {agent_id}")
        print("=" * 80)

        for r in history:
            print(f"{r['ts']}")
            print(f"  {r['agent_id']}: {r['from_state']} → {r['to_state']}")
            print(f"  原因: {r['reason']}")
            print(f"  触发: {r['trigger']}")
            if r.get("cooldown_until"):
                print(f"  Cooldown 至: {r['cooldown_until']}")
            print()

    elif command == "stats":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        stats = logger.get_stats(days)

        print(f"\n📊 状态转换统计 (最近 {days} 天)")
        print("=" * 80)
        print(f"总转换次数: {stats['total_transitions']}")
        print(f"降级次数: {stats['degradations']}")
        print(f"恢复次数: {stats['recoveries']}")
        print()

        print("按 Agent 统计:")
        for agent_id, count in sorted(
            stats["by_agent"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {agent_id}: {count} 次")
        print()

        print("按转换类型统计:")
        for transition, count in sorted(
            stats["by_transition"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {transition}: {count} 次")
        print()

        print("按触发方式统计:")
        for trigger, count in stats["by_trigger"].items():
            print(f"  {trigger}: {count} 次")

    else:
        print(f"未知命令: {command}")
        sys.exit(1)
