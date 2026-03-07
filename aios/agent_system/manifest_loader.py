"""Manifest 加载器 - 兼容新旧格式。

load_manifest_compat(path) 读取 JSON/JSONL manifest 文件，
经过 normalize_manifest 归一化后返回统一结构。
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Union

from manifest_schema import normalize_manifest


def load_manifest_compat(path: Union[str, Path]) -> dict:
    """加载并归一化 manifest 文件。

    支持 .json 格式。

    Args:
        path: manifest 文件路径。

    Returns:
        normalize_manifest 返回的统一结构。

    Raises:
        FileNotFoundError: 文件不存在。
        json.JSONDecodeError: JSON 解析失败。
        ValueError: manifest 校验失败（缺少必需键等）。
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"manifest not found: {p}")

    raw = json.loads(p.read_text(encoding="utf-8"))
    return normalize_manifest(raw)
