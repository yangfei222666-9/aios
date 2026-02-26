#!/usr/bin/env python3
"""
智能超时管理器 - 按 Agent 类型和路由自适应调整超时

设计原则：
1. 不同类型 Agent 有不同的合理超时范围
2. 本地模型（Ollama）快响应，云端模型（Claude）慢响应
3. 从历史数据学习最优超时值
4. 自动调整，避免"一刀切"
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta


class TimeoutManager:
    """智能超时管理器"""

    # 默认超时策略（秒）
    DEFAULT_TIMEOUT_BY_TYPE = {
        "coder": 120,       # 写代码/跑测试，需要时间
        "analyst": 90,      # 分析数据，中等耗时
        "monitor": 30,      # 监控检查，快速响应
        "researcher": 150,  # 调研搜索，可能较慢
        "orchestrator": 60, # 协调调度，中等耗时
        "test": 20,         # 测试 Agent，快速失败
        "default": 100      # 未知类型，保守值
    }

    DEFAULT_TIMEOUT_BY_ROUTE = {
        "ollama": 45,       # 本地模型，快响应
        "claude": 120,      # 云端模型，慢响应
        "openai": 90,       # 云端模型，中等
        "default": 100      # 未知路由
    }

    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = Path.home() / ".openclaw" / "workspace" / "aios" / "agent_system" / "data" / "agent_configs.json"
        
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        # 历史数据文件
        self.trace_file = self.config_file.parent.parent / "data" / "traces" / "agent_traces.jsonl"

    def _load_config(self) -> Dict:
        """加载配置"""
        if not self.config_file.exists():
            return {
                "timeout": 100,
                "timeout_by_type": self.DEFAULT_TIMEOUT_BY_TYPE.copy(),
                "timeout_by_route": self.DEFAULT_TIMEOUT_BY_ROUTE.copy(),
                "agents": {}
            }
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 确保有默认策略
        if "timeout_by_type" not in config:
            config["timeout_by_type"] = self.DEFAULT_TIMEOUT_BY_TYPE.copy()
        if "timeout_by_route" not in config:
            config["timeout_by_route"] = self.DEFAULT_TIMEOUT_BY_ROUTE.copy()
        
        return config

    def _save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_timeout(self, agent_id: str, agent_type: str = None, route: str = None) -> int:
        """
        获取 Agent 的超时值（优先级：Agent 配置 > 类型策略 > 路由策略 > 全局默认）

        Args:
            agent_id: Agent ID
            agent_type: Agent 类型（coder/analyst/monitor 等）
            route: 路由类型（ollama/claude 等）

        Returns:
            超时值（秒）
        """
        # 1. Agent 特定配置
        agent_config = self.config.get("agents", {}).get(agent_id, {})
        if "timeout" in agent_config:
            return agent_config["timeout"]
        
        # 2. 类型策略
        if agent_type:
            type_timeout = self.config.get("timeout_by_type", {}).get(agent_type)
            if type_timeout:
                return type_timeout
        
        # 3. 路由策略
        if route:
            route_timeout = self.config.get("timeout_by_route", {}).get(route)
            if route_timeout:
                return route_timeout
        
        # 4. 全局默认
        return self.config.get("timeout", 100)

    def set_timeout(self, agent_id: str, timeout: int, reason: str = "manual"):
        """
        设置 Agent 的超时值

        Args:
            agent_id: Agent ID
            timeout: 超时值（秒）
            reason: 调整原因
        """
        if agent_id not in self.config["agents"]:
            self.config["agents"][agent_id] = {}
        
        old_timeout = self.config["agents"][agent_id].get("timeout", self.config.get("timeout", 100))
        self.config["agents"][agent_id]["timeout"] = timeout
        self.config["agents"][agent_id]["timeout_updated_at"] = datetime.now().isoformat()
        self.config["agents"][agent_id]["timeout_reason"] = reason
        
        self._save_config()
        
        print(f"✅ {agent_id} 超时调整: {old_timeout}s → {timeout}s (原因: {reason})")

    def learn_from_history(self, agent_id: str, lookback_days: int = 7) -> Optional[int]:
        """
        从历史数据学习最优超时值

        策略：
        1. 统计最近 N 天的**成功任务**耗时（排除失败/超时）
        2. 计算 P95 耗时（95% 的成功任务能在此时间内完成）
        3. 加 20% 缓冲作为推荐超时

        Args:
            agent_id: Agent ID
            lookback_days: 回溯天数

        Returns:
            推荐超时值（秒），如果数据不足返回 None
        """
        if not self.trace_file.exists():
            return None
        
        # 读取历史数据（只看成功任务）
        cutoff = datetime.now() - timedelta(days=lookback_days)
        durations = []
        
        with open(self.trace_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    trace = json.loads(line.strip())
                    if trace.get("agent_id") != agent_id:
                        continue
                    
                    # 只看成功任务
                    if not trace.get("success", False):
                        continue
                    
                    start_time = datetime.fromisoformat(trace.get("start_time", ""))
                    if start_time < cutoff:
                        continue
                    
                    duration = trace.get("duration_sec", 0)
                    if duration > 0:
                        durations.append(duration)
                except:
                    continue
        
        if len(durations) < 10:  # 数据不足
            return None
        
        # 计算 P95
        durations.sort()
        p95_index = int(len(durations) * 0.95)
        p95_duration = durations[p95_index]
        
        # 加 20% 缓冲
        recommended_timeout = int(p95_duration * 1.2)
        
        # 限制在合理范围（10s ~ 300s）
        recommended_timeout = max(10, min(300, recommended_timeout))
        
        return recommended_timeout

    def auto_adjust(self, agent_id: str, agent_type: str = None) -> bool:
        """
        自动调整 Agent 超时值

        Args:
            agent_id: Agent ID
            agent_type: Agent 类型

        Returns:
            是否调整了超时
        """
        recommended = self.learn_from_history(agent_id)
        
        if recommended is None:
            print(f"⚠️  {agent_id} 历史数据不足，无法自动调整")
            return False
        
        current = self.get_timeout(agent_id, agent_type)
        
        # 如果推荐值与当前值差异 >20%，才调整
        if abs(recommended - current) / current > 0.2:
            self.set_timeout(agent_id, recommended, reason="auto_learned_from_history")
            return True
        else:
            print(f"ℹ️  {agent_id} 当前超时 {current}s 已接近最优值 {recommended}s，无需调整")
            return False

    def batch_auto_adjust(self, env: str = "prod") -> Dict:
        """
        批量自动调整所有 Agent 的超时

        Args:
            env: 环境（prod/test/all）

        Returns:
            调整统计
        """
        adjusted = []
        skipped = []
        
        for agent_id, agent_config in self.config.get("agents", {}).items():
            # 过滤环境
            if env != "all" and agent_config.get("env", "prod") != env:
                continue
            
            agent_type = agent_config.get("type")
            if self.auto_adjust(agent_id, agent_type):
                adjusted.append(agent_id)
            else:
                skipped.append(agent_id)
        
        return {
            "adjusted": adjusted,
            "skipped": skipped,
            "total": len(adjusted) + len(skipped)
        }


def test_timeout_manager():
    """测试超时管理器"""
    manager = TimeoutManager()
    
    print("=== 测试超时管理器 ===\n")
    
    # 测试 1: 获取超时（按优先级）
    print("测试 1: 获取超时值")
    timeout1 = manager.get_timeout("agent_coder_001", agent_type="coder")
    print(f"  agent_coder_001 (coder): {timeout1}s")
    
    timeout2 = manager.get_timeout("unknown_agent", agent_type="monitor")
    print(f"  unknown_agent (monitor): {timeout2}s")
    
    timeout3 = manager.get_timeout("unknown_agent", route="ollama")
    print(f"  unknown_agent (ollama route): {timeout3}s\n")
    
    # 测试 2: 从历史学习
    print("测试 2: 从历史学习最优超时")
    recommended = manager.learn_from_history("agent_coder_001")
    if recommended:
        print(f"  agent_coder_001 推荐超时: {recommended}s")
    else:
        print(f"  agent_coder_001 历史数据不足\n")
    
    # 测试 3: 批量自动调整
    print("测试 3: 批量自动调整")
    result = manager.batch_auto_adjust(env="prod")
    print(f"  调整: {len(result['adjusted'])} 个")
    print(f"  跳过: {len(result['skipped'])} 个")
    print(f"  总计: {result['total']} 个")


if __name__ == "__main__":
    test_timeout_manager()
