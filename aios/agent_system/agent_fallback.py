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

    # 用于从错误字符串中提取 HTTP 状态码
    import re
    _STATUS_CODE_RE = re.compile(r'\b([1-5]\d{2})\b')

    def detect_error_type(self, error: str) -> str:
        """
        检测错误类型（细分版）

        优先级：精确匹配 > 模糊匹配 > 兜底
        返回值：gateway_error | transient_network_failure | rate_limit |
                auth_error | client_error | timeout | memory_error |
                network_error | unknown_error
        """
        error_lower = error.lower()

        # --- Gateway 错误（502/503/504）---
        if any(code in error for code in ("502", "503", "504")) or "bad gateway" in error_lower or "service unavailable" in error_lower:
            return "gateway_error"

        # --- 瞬态网络故障（连接级别）---
        if any(kw in error_lower for kw in ("connectionreset", "connection reset", "econnrefused", "econnreset", "enetunreach", "temporary failure")):
            return "transient_network_failure"

        # --- 429 限流 ---
        if "429" in error or "rate limit" in error_lower:
            return "rate_limit"

        # --- 401/403 认证错误（独立保留，不合并进 client_error）---
        if any(code in error for code in ("401", "403")) or "unauthorized" in error_lower or "forbidden" in error_lower:
            return "auth_error"

        # --- 4xx 客户端错误（非 429、非 401/403）---
        # 用正则提取状态码，覆盖所有 4xx 而不是枚举
        codes = self._STATUS_CODE_RE.findall(error)
        for code in codes:
            c = int(code)
            if 400 <= c < 500 and c not in (401, 403, 429):
                return "client_error"

        # --- 超时 ---
        if "timeout" in error_lower or "超时" in error:
            return "timeout"

        # --- 内存 ---
        if "out of memory" in error_lower or "memory" in error_lower:
            return "memory_error"

        # --- 兜底：仍保留 network_error 作为未分类网络问题 ---
        if any(kw in error_lower for kw in ("network", "socket", "dns", "resolve")):
            return "network_error"

        return "unknown_error"

    def get_fallback_strategy(
        self, error_type: str, retry_count: int
    ) -> Optional[Dict]:
        """
        根据错误类型和重试次数返回降级策略

        action 可能值:
          retry / retry_with_backoff / downgrade_model / reduce_thinking /
          reduce_resources / mark_pending / manual_intervention / give_up
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

        # ── gateway_error (502/503/504) ──
        # 首次：15s 延时重试；再失败：mark_pending
        if error_type == "gateway_error":
            if retry_count == 0:
                strategy["wait_seconds"] = 15
                strategy["action"] = "retry_with_backoff"
            else:
                strategy["action"] = "mark_pending"
            return strategy

        # ── transient_network_failure (连接重置等) ──
        # 同 gateway_error 策略
        if error_type == "transient_network_failure":
            if retry_count == 0:
                strategy["wait_seconds"] = 15
                strategy["action"] = "retry_with_backoff"
            else:
                strategy["action"] = "mark_pending"
            return strategy

        # ── client_error (4xx 非 429/401/403) ──
        # 客户端错误无法自动修复，直接失败
        if error_type == "client_error":
            return None

        # ── auth_error (401/403) ──
        # 认证错误：需要人工介入，不重试
        # 保持独立分类以便未来接入 token 刷新逻辑
        if error_type == "auth_error":
            return None

        # ── 全局重试上限 guardrail ──
        # 通用错误（network/rate_limit/timeout/memory）的统一退出上限。
        # gateway_error / transient_network_failure 是特例，走 pending 路径，
        # 已在上面 early return，不受此 guardrail 覆盖。
        if retry_count >= 3:
            strategy["action"] = "give_up"
            return None

        # ── network_error (兜底网络问题) ──
        if error_type == "network_error":
            strategy["timeout"] = min(current_timeout * 1.5, 180)
            strategy["wait_seconds"] = min(retry_count * 5, 30)
            strategy["action"] = "retry_with_backoff"

        # ── rate_limit (429) ──
        elif error_type == "rate_limit":
            strategy["wait_seconds"] = min(retry_count * 15, 60)
            if retry_count >= 2:
                next_model = self.MODEL_FALLBACK_CHAIN.get(current_model)
                if next_model:
                    strategy["model"] = next_model
                    strategy["action"] = "downgrade_model"

        # ── timeout ──
        elif error_type == "timeout":
            next_thinking = self.THINKING_FALLBACK_CHAIN.get(current_thinking)
            if next_thinking:
                strategy["thinking"] = next_thinking
                strategy["action"] = "reduce_thinking"
            strategy["timeout"] = min(current_timeout * 2, 300)

        # ── memory_error ──
        elif error_type == "memory_error":
            next_model = self.MODEL_FALLBACK_CHAIN.get(current_model)
            next_thinking = self.THINKING_FALLBACK_CHAIN.get(current_thinking)
            if next_model:
                strategy["model"] = next_model
            if next_thinking:
                strategy["thinking"] = next_thinking
            strategy["action"] = "reduce_resources"

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
        ("Network error: 502 Bad Gateway", "Gateway 错误"),
        ("503 Service Unavailable", "Gateway 错误 (503)"),
        ("ConnectionResetError: peer closed", "瞬态网络故障"),
        ("API rate limit exceeded: 429", "限流错误"),
        ("Request timeout after 60s", "超时错误"),
        ("Out of memory", "内存错误"),
        ("400 Bad Request: invalid param", "客户端错误"),
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
