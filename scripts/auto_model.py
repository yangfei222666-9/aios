# scripts/auto_model.py - 自动模型切换策略 v2
"""
v2 三护栏：
1. min_dwell_turns: 至少待满N轮才允许切
2. hysteresis: 上下阈值不同，防抖动
3. switch_reason: 每次决策记录日志

基于关键词 + 长度 + 结构特征打分。
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
import time
import json
import re
from pathlib import Path

# 关键词配置
OPUS_KEYWORDS = (
    "重构", "架构", "设计", "调优", "性能瓶颈", "并发",
    "排查", "调试", "写代码", "写个", "写一个", "做一个",
    "Python脚本", "测试失败", "补丁", "review", "算法",
    "分析", "优化", "提升", "改进", "升级", "迁移",
    "系统", "模块", "组件", "引擎", "框架",
    "autolearn", "aios", "aram", "baseline", "dispatcher",
    "实现", "开发", "部署", "发布",
)

SONNET_KEYWORDS = (
    "闲聊", "天气", "翻译一句", "润色", "确认一下", "简答", "一句话",
    "你好", "hi", "hello", "早", "晚安", "谢谢", "好的", "ok", "收到",
    "查一下", "搜一下", "看看", "几点", "时间", "提醒",
)

# 强制关键词（绕过打分直接决策）
FORCE_OPUS = ("切工作模式", "切opus", "用opus")
FORCE_SONNET = ("切日常模式", "切sonnet", "用sonnet")

STATE_FILE = Path(__file__).parent.parent / "memory" / "auto_model_state.json"
LOG_FILE = Path(__file__).parent.parent / "memory" / "auto_model_log.jsonl"


@dataclass
class AutoModelConfig:
    min_dwell_turns: int = 3
    up_threshold: float = 0.72
    down_threshold: float = 0.45


@dataclass
class AutoModelState:
    current_model: str = "sonnet"
    turns_since_switch: int = 0


def _load_state() -> AutoModelState:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return AutoModelState(**{k: v for k, v in data.items()
                                     if k in AutoModelState.__dataclass_fields__})
        except Exception:
            pass
    return AutoModelState()


def _save_state(state: AutoModelState):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2),
                          encoding="utf-8")


def _append_log(entry: Dict):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def classify_complexity(msg: str) -> Dict[str, Any]:
    """对消息打分：score 越高越偏复杂任务"""
    t = msg.strip().lower()
    signals: List[str] = []
    score = 0.0
    complex_hits = 0

    # 1) 关键词特征
    opus_hits = [k for k in OPUS_KEYWORDS if k.lower() in t]
    sonnet_hits = [k for k in SONNET_KEYWORDS if k.lower() in t]

    if opus_hits:
        score += min(0.55, 0.18 * len(opus_hits))
        complex_hits = len(opus_hits)
        signals.append(f"opus_kw:{len(opus_hits)}")
    if sonnet_hits:
        score -= min(0.40, 0.15 * len(sonnet_hits))
        signals.append(f"sonnet_kw:{len(sonnet_hits)}")

    # 2) 长度/结构特征
    if len(t) > 180:
        score += 0.18
        signals.append("len>180")

    if "```" in msg:
        score += 0.22
        signals.append("code_block")

    if any(x in t for x in ["traceback", "日志", "stack"]):
        score += 0.15
        signals.append("error_context")

    # "报错"在 opus 模式下可能是任务中遇到问题，不应降级
    if "报错" in t and not any(x in t for x in ["分析", "修复", "排查", "调试"]):
        score += 0.08  # 轻微加分，避免被降级
        signals.append("error_mention_neutral")

    # 3) 归一化
    score = max(0.0, min(1.0, 0.5 + score))

    # 4) 短消息惩罚
    if len(t) < 30 and complex_hits == 0:
        score = max(0.0, score - 0.15)
        signals.append("short_msg_penalty")

    label = "complex" if score >= 0.5 else "simple"

    # 5) 置信度
    confidence = abs(score - 0.5) * 2.0
    confidence = max(0.0, min(1.0, confidence))

    return {
        "score": score,
        "label": label,
        "confidence": confidence,
        "signals": signals,
    }


def should_switch(msg: str) -> Dict[str, Any]:
    """主入口：判断是否需要切换模型"""
    cfg = AutoModelConfig()
    state = _load_state()
    state.turns_since_switch += 1

    result = classify_complexity(msg)
    score = result["score"]
    confidence = result["confidence"]

    reason_parts: List[str] = []
    target = state.current_model
    cur = state.current_model

    t = msg.strip().lower()

    # A) 强制关键词
    if any(k in t for k in FORCE_OPUS):
        target = "opus"
        reason_parts.append("force_opus_keyword")
    elif any(k in t for k in FORCE_SONNET):
        target = "sonnet"
        reason_parts.append("force_sonnet_keyword")
    else:
        # B) 普通阈值决策（hysteresis）
        if cur == "sonnet":
            if score >= cfg.up_threshold and confidence >= 0.35:
                target = "opus"
                reason_parts.append(f"score>={cfg.up_threshold}")
            else:
                reason_parts.append("stay_sonnet_by_threshold")
        else:  # cur == opus
            # opus → sonnet: 降低 confidence 要求
            if score <= cfg.down_threshold and confidence >= 0.25:
                target = "sonnet"
                reason_parts.append(f"score<={cfg.down_threshold}")
            else:
                reason_parts.append("stay_opus_by_threshold")

    # C) 护栏1: min_dwell_turns 防抖
    blocked_by_dwell = False
    if target != cur and state.turns_since_switch < cfg.min_dwell_turns:
        blocked_by_dwell = True
        reason_parts.append(
            f"blocked:min_dwell({state.turns_since_switch}<{cfg.min_dwell_turns})"
        )

    # D) 执行切换
    did_switch = (target != cur) and not blocked_by_dwell
    if did_switch:
        state.current_model = target
        state.turns_since_switch = 0

    _save_state(state)

    # E) 护栏3: 日志
    import uuid
    trace_id = uuid.uuid4().hex[:8]
    _append_log({
        "ts": int(time.time()),
        "trace_id": trace_id,
        "current_model": cur,
        "target_model": target,
        "will_switch": did_switch,
        "switch_reason": "|".join(reason_parts),
        "score": round(score, 2),
        "confidence": round(confidence, 2),
    })

    return {
        "should_switch": did_switch,
        "from": cur,
        "to": state.current_model,
        "reason": "|".join(reason_parts),
        "trace_id": trace_id,
        "score": score,
        "confidence": confidence,
    }


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = input("输入消息: ")

    result = should_switch(msg)

    if result["should_switch"]:
        print(f"🔄 切换: {result['from']} → {result['to']}")
    else:
        print(f"✓ 保持: {result['from']}")
    print(f"原因: {result['reason']}")
    print(f"评分: {result['score']:.2f} (置信度 {result['confidence']:.2f})")
    print(f"trace_id: {result['trace_id']}")
