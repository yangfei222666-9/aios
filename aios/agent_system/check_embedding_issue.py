#!/usr/bin/env python3
"""快速排查 embedding 加载问题"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("Embedding 加载问题排查")
print("=" * 60)

# 1. 检查 CUDA
print("\n1. CUDA 状态...")
try:
    import torch
    print(f"   PyTorch 版本: {torch.__version__}")
    print(f"   CUDA 可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   CUDA 版本: {torch.version.cuda}")
        print(f"   GPU 数量: {torch.cuda.device_count()}")
        print(f"   当前 GPU: {torch.cuda.current_device()}")
        print(f"   GPU 名称: {torch.cuda.get_device_name(0)}")
except Exception as e:
    print(f"   ❌ CUDA 检查失败: {e}")

# 2. 检查 sentence-transformers
print("\n2. sentence-transformers 状态...")
try:
    import sentence_transformers
    print(f"   版本: {sentence_transformers.__version__}")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")

# 3. 检查缓存
print("\n3. 模型缓存...")
home = Path.home()
hf_cache = home / ".cache" / "huggingface" / "hub"
st_cache = home / ".cache" / "torch" / "sentence_transformers"

print(f"   HuggingFace 缓存: {hf_cache}")
if hf_cache.exists():
    models = list(hf_cache.glob("models--*"))
    print(f"   ✅ 存在，包含 {len(models)} 个模型")
    for model in models[:3]:
        print(f"      - {model.name}")
else:
    print(f"   ❌ 不存在")

print(f"\n   Sentence-transformers 缓存: {st_cache}")
if st_cache.exists():
    models = list(st_cache.glob("*"))
    print(f"   ✅ 存在，包含 {len(models)} 个模型")
    for model in models[:3]:
        print(f"      - {model.name}")
else:
    print(f"   ❌ 不存在")

# 4. 检查 Memory Server
print("\n4. Memory Server 状态...")
try:
    import requests
    response = requests.get("http://localhost:7788/status", timeout=2)
    print(f"   ✅ Memory Server 运行中")
    print(f"   状态码: {response.status_code}")
except requests.exceptions.ConnectionError:
    print(f"   ❌ Memory Server 未运行")
except Exception as e:
    print(f"   ⚠️  检查失败: {e}")

# 5. 尝试加载模型（快速测试）
print("\n5. 模型加载测试...")
print("   ⚠️  跳过（避免卡住当前检查）")
print("   建议：单独测试 'python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')\"'")

print("\n" + "=" * 60)
print("排查完成")
print("=" * 60)
