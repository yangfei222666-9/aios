"""
selflearn_state.py - selflearn-state.json 统一更新器

职责：
- 读取旧 state
- 合并更新字段
- 原子写回 selflearn-state.json

不要让每个 runner 各自乱写。

Version: 1.0
Created: 2026-03-11
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Literal

from schemas.selflearn_state_schema import (
    SelfLearnState,
    get_default_state,
    validate_state,
)


STATE_FILE = Path(__file__).parent / "memory" / "selflearn-state.json"


def load_state() -> SelfLearnState:
    """加载当前 state，如果不存在或损坏则返回默认值"""
    if not STATE_FILE.exists():
        return get_default_state()
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        if not validate_state(state):
            print(f"[WARN] selflearn-state.json 结构不合法，使用默认值")
            return get_default_state()
        
        return state
    except Exception as e:
        print(f"[ERROR] 加载 selflearn-state.json 失败: {e}")
        return get_default_state()


def save_state(state: SelfLearnState) -> bool:
    """原子写回 state"""
    try:
        # 确保目录存在
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 验证结构
        if not validate_state(state):
            print(f"[ERROR] state 结构不合法，拒绝写入")
            return False
        
        # 原子写入（先写临时文件，再重命名）
        temp_file = STATE_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        temp_file.replace(STATE_FILE)
        return True
    except Exception as e:
        print(f"[ERROR] 保存 selflearn-state.json 失败: {e}")
        return False


def update_state(
    agent_id: str | None = None,
    success: bool = True,
    learning_loop_status: Literal["healthy", "degraded", "blocked", "unknown"] | None = None,
    validated_count: int | None = None,
    active_count: int | None = None,
    pending_lessons: int | None = None,
    rules_derived: int | None = None,
) -> bool:
    """
    更新 state
    
    Args:
        agent_id: 执行的 Agent ID
        success: 是否成功
        learning_loop_status: 学习循环状态
        validated_count: 已验证的学习 Agent 数量
        active_count: 活跃的学习 Agent 数量
        pending_lessons: 待处理的 lesson 数量
        rules_derived: 已提炼的规则数量
    
    Returns:
        是否成功更新
    """
    state = load_state()
    
    # 更新时间戳
    now = datetime.now().isoformat()
    state["updated_at"] = now
    
    # 更新运行时间
    if agent_id:
        state["last_run_at"] = now
        state["last_agent"] = agent_id
        
        if success:
            state["last_success_at"] = now
    
    # 更新状态
    if learning_loop_status:
        state["learning_loop_status"] = learning_loop_status
    
    # 更新计数
    if validated_count is not None:
        state["validated_learning_agents_count"] = validated_count
    
    if active_count is not None:
        state["active_learning_agents_count"] = active_count
    
    if pending_lessons is not None:
        state["pending_lessons_count"] = pending_lessons
    
    if rules_derived is not None:
        state["rules_derived_count"] = rules_derived
    
    return save_state(state)


def get_state() -> SelfLearnState:
    """获取当前 state（只读）"""
    return load_state()


if __name__ == "__main__":
    # 测试：初始化 state
    print("初始化 selflearn-state.json...")
    state = get_default_state()
    if save_state(state):
        print("✅ 初始化成功")
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        print("❌ 初始化失败")
