"""
schemas.py - 统一 MemoryRecord 定义
Memory Agent v2 的数据契约，所有写入/查询都走这个结构。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class MemoryRecord:
    """一条经验记忆的完整结构。"""

    # 唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 内容
    text: str = ""                          # 原始描述（用于 embedding）
    summary: str = ""                       # 精炼摘要（可选，用于注入 prompt）

    # 分类
    memory_type: str = "general"            # success_case | failure_pattern | fix_solution | general
    task_type: str = ""                     # code | analysis | monitor | research | ...
    error_type: str = ""                    # timeout | dependency_error | logic_error | ...

    # 来源
    source: str = ""                        # task_executions | lessons | experience_library | manual
    source_task_id: str = ""                # 关联的原始 task id

    # 结果
    outcome: str = "success"                # success | failed
    confidence: float = 0.5                 # 0.0 ~ 1.0，可通过 feedback 调整

    # 元数据
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)  # unix timestamp
    updated_at: float = field(default_factory=time.time)

    # embedding（写入 store 时由 embedder 填充，不需要手动设置）
    vector: Optional[list[float]] = None

    def to_dict(self) -> dict:
        """转为 dict，适合写入 LanceDB。"""
        d = asdict(self)
        # tags 序列化为 JSON string（LanceDB 不支持 list column）
        import json
        d["tags"] = json.dumps(d["tags"])
        # vector 为 None 时不写入（由 store 层填充）
        if d["vector"] is None:
            del d["vector"]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> MemoryRecord:
        """从 dict 还原。"""
        import json
        d = dict(d)  # copy
        if isinstance(d.get("tags"), str):
            try:
                d["tags"] = json.loads(d["tags"])
            except Exception:
                d["tags"] = []
        # 过滤掉 LanceDB 内部字段
        d.pop("_distance", None)
        d.pop("_score", None)
        # 只保留 dataclass 字段
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        d = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**d)
