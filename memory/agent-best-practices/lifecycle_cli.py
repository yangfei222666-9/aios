#!/usr/bin/env python3
"""
Agent 生命周期手动干预 CLI - 实现示例
基于 2026-03-13 最佳实践研究

功能：
1. 强制激活/降级 Agent
2. 查看转换历史
3. 重置 Cooldown
4. 批量操作
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 路径配置
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

try:
    from paths import AGENTS_STATE
    from state_transition_logger import StateTransitionLogger
except ImportError:
    print("⚠️  无法导入依赖模块，请确保在正确的目录运行")
    sys.exit(1)


class LifecycleController:
    """生命周期控制器"""

    def __init__(self):
        self.agents_file = AGENTS_STATE
        self.logger = StateTransitionLogger()

    def load_agents(self):
        """加载 agents.json"""
        if not self.agents_file.exists():
            print(f"❌ 找不到 {self.agents_file}")
            sys.exit(1)

        with open(self.agents_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_agents(self, data):
        """保存 agents.json"""
        with open(self.agents_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def find_agent(self, data, agent_id: str):
        """查找 Agent"""
        for agent in data.get("agents", []):
            if agent.get("id") == agent_id or agent.get("name") == agent_id:
                return agent
        return None

    def force_state(self, agent_id: str, target_state: str, reason: str):
        """
        强制设置 Agent 状态

        Args:
            agent_id: Agent ID
            target_state: 目标状态 (active/shadow/disabled)
            reason: 原因
        """
        if target_state not in ["active", "shadow", "disabled"]:
            print(f"❌ 无效状态: {target_state}")
            sys.exit(1)

        data = self.load_agents()
        agent = self.find_agent(data, agent_id)

        if not agent:
            print(f"❌ 找不到 Agent: {agent_id}")
            sys.exit(1)

        old_state = agent.get("lifecycle_state", "active")

        if old_state == target_state:
            print(f"ℹ️  Agent {agent_id} 已经是 {target_state} 状态")
            return

        # 更新状态
        agent["lifecycle_state"] = target_state
        agent["cooldown_until"] = None  # 清除 cooldown
        agent["routable"] = target_state == "active"

        # 更新 timeout 和 priority
        timeout_map = {"active": 60, "shadow": 120, "disabled": 0}
        priority_map = {"active": "normal", "shadow": "low", "disabled": "none"}
        agent["timeout"] = timeout_map[target_state]
        agent["priority"] = priority_map[target_state]

        # 保存
        self.save_agents(data)

        # 记录日志
        self.logger.log_transition(
            agent_id=agent_id,
            from_state=old_state,
            to_state=target_state,
            reason=reason,
            trigger="manual",
        )

        print(f"✅ 已将 {agent_id} 从 {old_state} 强制切换到 {target_state}")
        print(f"   原因: {reason}")

    def reset_cooldown(self, agent_id: str):
        """重置 Cooldown"""
        data = self.load_agents()
        agent = self.find_agent(data, agent_id)

        if not agent:
            print(f"❌ 找不到 Agent: {agent_id}")
            sys.exit(1)

        old_cooldown = agent.get("cooldown_until")
        agent["cooldown_until"] = None

        self.save_agents(data)

        print(f"✅ 已重置 {agent_id} 的 Cooldown")
        if old_cooldown:
            print(f"   原 Cooldown: {old_cooldown}")

    def show_status(self, agent_id: Optional[str] = None):
        """显示状态"""
        data = self.load_agents()

        if agent_id:
            agent = self.find_agent(data, agent_id)
            if not agent:
                print(f"❌ 找不到 Agent: {agent_id}")
                sys.exit(1)
            agents = [agent]
        else:
            agents = data.get("agents", [])

        print(f"\n📊 Agent 状态")
        print("=" * 80)

        for agent in agents:
            aid = agent.get("id") or agent.get("name")
            state = agent.get("lifecycle_state", "active")
            cooldown = agent.get("cooldown_until")
            routable = agent.get("routable", False)

            print(f"\n{aid}")
            print(f"  状态: {state}")
            print(f"  可路由: {'✅' if routable else '❌'}")
            if cooldown:
                print(f"  Cooldown 至: {cooldown}")

    def batch_force_active(self, agent_ids: list, reason: str):
        """批量激活"""
        for agent_id in agent_ids:
            try:
                self.force_state(agent_id, "active", reason)
            except Exception as e:
                print(f"⚠️  {agent_id} 激活失败: {e}")


# ── CLI ──

def main():
    if len(sys.argv) < 2:
        print("Agent 生命周期手动干预 CLI")
        print("=" * 60)
        print("用法:")
        print("  python lifecycle_cli.py force-active <agent_id> <reason>")
        print("  python lifecycle_cli.py force-shadow <agent_id> <reason>")
        print("  python lifecycle_cli.py force-disabled <agent_id> <reason>")
        print("  python lifecycle_cli.py reset-cooldown <agent_id>")
        print("  python lifecycle_cli.py status [agent_id]")
        print("  python lifecycle_cli.py history <agent_id>")
        print("  python lifecycle_cli.py batch-active <id1,id2,...> <reason>")
        print()
        print("示例:")
        print("  python lifecycle_cli.py force-active data-collector 'bug fixed'")
        print("  python lifecycle_cli.py status")
        print("  python lifecycle_cli.py history data-collector")
        sys.exit(1)

    controller = LifecycleController()
    command = sys.argv[1]

    if command == "force-active":
        if len(sys.argv) < 4:
            print("❌ 用法: force-active <agent_id> <reason>")
            sys.exit(1)
        agent_id = sys.argv[2]
        reason = sys.argv[3]
        controller.force_state(agent_id, "active", reason)

    elif command == "force-shadow":
        if len(sys.argv) < 4:
            print("❌ 用法: force-shadow <agent_id> <reason>")
            sys.exit(1)
        agent_id = sys.argv[2]
        reason = sys.argv[3]
        controller.force_state(agent_id, "shadow", reason)

    elif command == "force-disabled":
        if len(sys.argv) < 4:
            print("❌ 用法: force-disabled <agent_id> <reason>")
            sys.exit(1)
        agent_id = sys.argv[2]
        reason = sys.argv[3]
        controller.force_state(agent_id, "disabled", reason)

    elif command == "reset-cooldown":
        if len(sys.argv) < 3:
            print("❌ 用法: reset-cooldown <agent_id>")
            sys.exit(1)
        agent_id = sys.argv[2]
        controller.reset_cooldown(agent_id)

    elif command == "status":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else None
        controller.show_status(agent_id)

    elif command == "history":
        if len(sys.argv) < 3:
            print("❌ 用法: history <agent_id>")
            sys.exit(1)
        agent_id = sys.argv[2]
        logger = StateTransitionLogger()
        history = logger.get_history(agent_id, limit=10)

        print(f"\n📜 {agent_id} 状态转换历史")
        print("=" * 80)
        for r in history:
            print(f"{r['ts']}")
            print(f"  {r['from_state']} → {r['to_state']}")
            print(f"  原因: {r['reason']}")
            print(f"  触发: {r['trigger']}")
            print()

    elif command == "batch-active":
        if len(sys.argv) < 4:
            print("❌ 用法: batch-active <id1,id2,...> <reason>")
            sys.exit(1)
        agent_ids = sys.argv[2].split(",")
        reason = sys.argv[3]
        controller.batch_force_active(agent_ids, reason)

    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
