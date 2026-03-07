"""
embedder.py - 单例加载 sentence-transformers + 简单缓存
Day 1 目标：稳定、本地、轻量。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


@lru_cache(maxsize=4096)
def embed_text(text: str) -> tuple[float, ...]:
    """对单条文本做 embedding，并缓存结果。"""
    if not text:
        text = ""
    vec = get_model().encode(text, normalize_embeddings=True)
    return tuple(float(x) for x in vec.tolist())


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量 embedding。对重复文本会复用单条缓存。"""
    return [list(embed_text(t)) for t in texts]


def embedding_dim() -> int:
    return len(embed_text("test"))
