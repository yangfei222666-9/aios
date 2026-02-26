#!/usr/bin/env python3
"""
影子验证器 - 进化引擎的安全门

在自动应用改进前，先跑：
1. smoke_test - 基础功能测试
2. replay_recent_events - 回放最近事件，确保不会变差

任何一项失败 → 不应用，只发 Telegram 提醒
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# 确保能导入 AIOS 模块
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer


class ShadowValidator:
    """影子验证器 - 在应用改进前验证安全性"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = AIOS_ROOT / "agent_system" / "data"
        self.data_dir = Path(data_dir)
        self.analyzer = TraceAnalyzer()

    def validate_before_apply(
        self,
        agent_id: str,
        improvement: Dict,
        replay_count: int = 100
    ) -> Tuple[bool, str]:
        """
        在应用改进前验证

        Args:
            agent_id: Agent ID
            improvement: 改进内容
            replay_count: 回放事件数量

        Returns:
            (是否通过, 失败原因)
        """
        print(f"[ShadowValidator] 验证 {agent_id} 的改进...")

        # 1. Smoke Test
        smoke_ok, smoke_msg = self._smoke_test(agent_id, improvement)
        if not smoke_ok:
            return False, f"Smoke Test 失败: {smoke_msg}"

        # 2. Replay Recent Events
        replay_ok, replay_msg = self._replay_recent_events(
            agent_id, improvement, replay_count
        )
        if not replay_ok:
            return False, f"Replay 失败: {replay_msg}"

        return True, "验证通过"

    def _smoke_test(self, agent_id: str, improvement: Dict) -> Tuple[bool, str]:
        """基础功能测试"""
        print("  [1/2] Smoke Test...")

        # 检查改进类型
        imp_type = improvement.get("type", "unknown")

        if imp_type == "timeout_adjustment":
            # 超时调整：确保新值合理（10s ~ 300s）
            new_timeout = improvement.get("new_value", 0)
            if not (10 <= new_timeout <= 300):
                return False, f"超时值不合理: {new_timeout}s"

        elif imp_type == "priority_adjustment":
            # 优先级调整：确保在 0~1 范围
            new_priority = improvement.get("new_value", -1)
            if not (0 <= new_priority <= 1):
                return False, f"优先级不合理: {new_priority}"

        elif imp_type == "prompt_patch":
            # Prompt 补丁：确保不为空
            patch = improvement.get("patch", "")
            if not patch or len(patch) < 10:
                return False, "Prompt 补丁为空或过短"

        elif imp_type == "config_change":
            # 配置变更：确保有 key 和 value
            if "key" not in improvement or "value" not in improvement:
                return False, "配置变更缺少 key 或 value"

        else:
            # 未知类型：保守拒绝
            return False, f"未知改进类型: {imp_type}"

        print("    ✅ Smoke Test 通过")
        return True, "OK"

    def _replay_recent_events(
        self, agent_id: str, improvement: Dict, count: int
    ) -> Tuple[bool, str]:
        """回放最近事件，确保改进不会让情况变差"""
        print(f"  [2/2] Replay Recent Events (n={count})...")

        # 获取该 Agent 最近的 trace
        agent_traces = [
            t for t in self.analyzer.traces
            if t.get("agent_id") == agent_id and t.get("env", "prod") == "prod"
        ]

        if not agent_traces:
            print("    ⚠️  无历史数据，跳过 Replay")
            return True, "无历史数据"

        # 取最近 N 条
        recent = agent_traces[-count:]

        # 计算当前成功率和平均耗时
        current_success_rate = sum(1 for t in recent if t.get("success")) / len(recent)
        current_avg_duration = sum(t.get("duration_sec", 0) for t in recent) / len(recent)

        print(f"    当前基线: 成功率={current_success_rate:.2%}, 平均耗时={current_avg_duration:.1f}s")

        # 模拟应用改进后的效果
        # （这里是简化版，实际应该真的跑一遍）
        predicted_success_rate, predicted_avg_duration = self._predict_impact(
            improvement, current_success_rate, current_avg_duration
        )

        print(f"    预测效果: 成功率={predicted_success_rate:.2%}, 平均耗时={predicted_avg_duration:.1f}s")

        # 判断是否变差
        # 成功率下降 >10% 或 耗时增加 >20% → 拒绝
        if predicted_success_rate < current_success_rate - 0.10:
            return False, f"成功率预计下降 {(current_success_rate - predicted_success_rate)*100:.1f}%"

        if predicted_avg_duration > current_avg_duration * 1.2:
            return False, f"耗时预计增加 {(predicted_avg_duration / current_avg_duration - 1)*100:.1f}%" if current_avg_duration > 0 else (False, "当前平均耗时为0，无法比较")

        print("    ✅ Replay 通过")
        return True, "OK"

    def _predict_impact(
        self, improvement: Dict, current_sr: float, current_dur: float
    ) -> Tuple[float, float]:
        """
        预测改进的影响（简化版）

        实际生产中应该：
        1. 创建临时 Agent 副本
        2. 应用改进
        3. 真实回放最近 N 个任务
        4. 对比指标

        这里用启发式规则快速估算
        """
        imp_type = improvement.get("type", "unknown")

        if imp_type == "timeout_adjustment":
            # 超时增加 → 成功率可能提升，耗时增加
            old_timeout = improvement.get("old_value", 100)
            new_timeout = improvement.get("new_value", 100)
            ratio = new_timeout / old_timeout if old_timeout > 0 else 1.0

            if ratio > 1:  # 增加超时
                predicted_sr = min(1.0, current_sr + 0.05)  # 成功率提升 5%
                predicted_dur = current_dur * 1.1  # 耗时增加 10%
            else:  # 减少超时
                predicted_sr = current_sr - 0.05  # 成功率下降 5%
                predicted_dur = current_dur * 0.9  # 耗时减少 10%

        elif imp_type == "priority_adjustment":
            # 优先级调整 → 对成功率和耗时影响不大
            predicted_sr = current_sr
            predicted_dur = current_dur

        elif imp_type == "prompt_patch":
            # Prompt 补丁 → 假设成功率提升 3%，耗时不变
            predicted_sr = min(1.0, current_sr + 0.03)
            predicted_dur = current_dur

        else:
            # 未知类型 → 保守估计无变化
            predicted_sr = current_sr
            predicted_dur = current_dur

        return predicted_sr, predicted_dur


def test_validator():
    """测试验证器"""
    validator = ShadowValidator()

    # 测试用例 1: 合理的超时调整
    improvement1 = {
        "type": "timeout_adjustment",
        "old_value": 100,
        "new_value": 120,
        "reason": "减少超时失败"
    }
    ok, msg = validator.validate_before_apply("agent_coder_001", improvement1)
    print(f"\n测试 1: {ok} - {msg}")

    # 测试用例 2: 不合理的超时（太大）
    improvement2 = {
        "type": "timeout_adjustment",
        "old_value": 100,
        "new_value": 500,
        "reason": "减少超时失败"
    }
    ok, msg = validator.validate_before_apply("agent_coder_001", improvement2)
    print(f"\n测试 2: {ok} - {msg}")

    # 测试用例 3: Prompt 补丁
    improvement3 = {
        "type": "prompt_patch",
        "patch": "在执行前先检查输入参数是否合法",
        "reason": "减少参数错误"
    }
    ok, msg = validator.validate_before_apply("agent_coder_001", improvement3)
    print(f"\n测试 3: {ok} - {msg}")


if __name__ == "__main__":
    test_validator()
