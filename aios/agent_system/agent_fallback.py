"""
Agent Fallback: 失败时自动降级
根据错误类型自动切换模型、调整参数、重试策略
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

AIOS_ROOT = Path(__file__).resolve().parent.parent
FALLBACK_LOG = AIOS_ROOT / "agent_system" / "data" / "fallback_log.jsonl"


class AgentFallback:
    """Agent 降级策略"""

    # 模型降级链
    MODEL_FALLBACK_CHAIN = {
        "claude-opus-4-6": "claude-sonnet-4-5",
        "claude-sonnet-4-5": "claude-haiku-4-5",
        "claude-haiku-4-5": None,  # 最后一级，无法再降级
    }

    # Thinking 降级链
    THINKING_FALLBACK_CHAIN = {
        "high": "medium",
        "medium": "low",
        "low": "off",
        "off": None,
    }

    def __init__(self, agent_id: str, current_config: Dict):
        self.agent_id = agent_id
        self.current_config = current_config
        self.fallback_history = []

    def detect_error_type(self, error: str) -> str:
        """检测错误类型"""
        error_lower = error.lower()

        if "502" in error or "bad gateway" in error_lower:
            return "network_error"
        elif "429" in error or "rate limit" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower or "超时" in error:
            return "timeout"
        elif "401" in error or "403" in error or "unauthorized" in error_lower:
            return "auth_error"
        elif "out of memory" in error_lower or "memory" in error_lower:
            return "memory_error"
        else:
            return "unknown_error"

    def get_fallback_strategy(
        self, error_type: str, retry_count: int
    ) -> Optional[Dict]:
        """
        根据错误类型和重试次数返回降级策略
        """
        current_model = self.current_config.get("model", "claude-sonnet-4-5")
        current_thinking = self.current_config.get("thinking", "medium")
        current_timeout = self.current_config.get("timeout", 60)

        strategy = {
            "model": current_model,
            "thinking": current_thinking,
            "timeout": current_timeout,
            "wait_seconds": 0,
            "action": "retry",
        }

        # 根据错误类型调整策略
        if error_type == "network_error":
            # 网络错误：增加超时，等待后重试
            strategy["timeout"] = min(current_timeout * 1.5, 180)
            strategy["wait_seconds"] = min(retry_count * 5, 30)
            strategy["action"] = "retry_with_backoff"

        elif error_type == "rate_limit":
            # 限流：等待更长时间，降级模型减少负载
            strategy["wait_seconds"] = min(retry_count * 15, 60)
            if retry_count >= 2:
                next_model = self.MODEL_FALLBACK_CHAIN.get(current_model)
                if next_model:
                    strategy["model"] = next_model
                    strategy["action"] = "downgrade_model"

        elif error_type == "timeout":
            # 超时：降低 thinking 级别，增加超时时间
            next_thinking = self.THINKING_FALLBACK_CHAIN.get(current_thinking)
            if next_thinking:
                strategy["thinking"] = next_thinking
                strategy["action"] = "reduce_thinking"
            strategy["timeout"] = min(current_timeout * 2, 300)

        elif error_type == "memory_error":
            # 内存错误：降级模型和 thinking
            next_model = self.MODEL_FALLBACK_CHAIN.get(current_model)
            next_thinking = self.THINKING_FALLBACK_CHAIN.get(current_thinking)
            if next_model:
                strategy["model"] = next_model
            if next_thinking:
                strategy["thinking"] = next_thinking
            strategy["action"] = "reduce_resources"

        elif error_type == "auth_error":
            # 认证错误：无法自动修复，需要人工介入
            strategy["action"] = "manual_intervention"
            return None

        # 如果重试次数过多，放弃
        if retry_count >= 3:
            strategy["action"] = "give_up"
            return None

        return strategy

    def apply_fallback(self, error: str, retry_count: int) -> Optional[Dict]:
        """
        应用降级策略
        返回新的配置，如果无法降级则返回 None
        """
        error_type = self.detect_error_type(error)
        strategy = self.get_fallback_strategy(error_type, retry_count)

        if not strategy or strategy["action"] in ["give_up", "manual_intervention"]:
            self._log_fallback(error_type, retry_count, None, "failed")
            return None

        # 记录降级
        self._log_fallback(error_type, retry_count, strategy, "applied")

        return strategy

    def _log_fallback(
        self, error_type: str, retry_count: int, strategy: Optional[Dict], status: str
    ):
        """记录降级日志"""
        log_entry = {
            "ts": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "error_type": error_type,
            "retry_count": retry_count,
            "strategy": strategy,
            "status": status,
        }

        FALLBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(FALLBACK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ── CLI ──

if __name__ == "__main__":
    import sys

    # 演示
    print("=" * 50)
    print("Agent Fallback 演示")
    print("=" * 50)

    config = {"model": "claude-opus-4-6", "thinking": "high", "timeout": 60}

    fallback = AgentFallback("test-agent", config)

    # 测试不同错误类型
    test_errors = [
        ("Network error: 502 Bad Gateway", "网络错误"),
        ("API rate limit exceeded: 429", "限流错误"),
        ("Request timeout after 60s", "超时错误"),
        ("Out of memory", "内存错误"),
    ]

    for error, desc in test_errors:
        print(f"\n[TEST] 测试：{desc}")
        print(f"   错误：{error}")

        for retry in range(3):
            strategy = fallback.apply_fallback(error, retry)
            if strategy:
                print(f"   重试 {retry + 1}: {strategy['action']}")
                print(f"     - 模型: {strategy['model']}")
                print(f"     - Thinking: {strategy['thinking']}")
                print(f"     - 超时: {strategy['timeout']}s")
                print(f"     - 等待: {strategy['wait_seconds']}s")
            else:
                print(f"   重试 {retry + 1}: 无法降级，放弃")
                break
