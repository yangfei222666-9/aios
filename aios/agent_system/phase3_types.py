"""
Phase 3 类型定义 - Adversarial Validation System
统一的类型系统，支持 Bull vs Bear 辩论、64卦调解、LLM 调用
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TokenUsage:
    """Token 使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class GenerateRequest:
    """LLM 生成请求"""
    role: str  # bull / bear / judge / expert
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    temperature: float = 0.3
    max_tokens: int = 512
    timeout_ms: int = 15000
    trace_id: str = ""


@dataclass
class GenerateResponse:
    """LLM 生成响应"""
    ok: bool
    text: str
    model_id: str = "unknown"
    latency_ms: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    finish_reason: str = "stop"
    error_code: str = ""
    error_message: str = ""


@dataclass
class DecisionResult:
    """决策结果"""
    verdict: str  # approve / reject / defer
    reason: str
    rounds_used: int
    early_exit: bool
    confidence: float
    requires_human_gate: bool
    audit_id: str = ""
    # Debate vs Vote 动态模式字段（向后兼容，默认 None）
    selected_mode: str = ""          # "debate" | "vote"
    mode_reason: str = ""            # 模式选择原因
    uncertainty_score: float = 0.0   # 不确定性分数
    convergence_score: float = 0.0   # 收敛性分数
