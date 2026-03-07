# embedding_generator.py - Phase 3 最终版（OpenAI + 本地fallback）
import os
from sentence_transformers import SentenceTransformer

# 本地模型（离线可用）
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384维，速度快，推荐生产

def generate_embedding(text: str) -> list:
    """生产级Embedding生成（OpenAI优先 → 本地fallback）"""
    if not text:
        text = "default task"
    
    # 优先尝试OpenAI（如果有key）
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if client.api_key:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
    except:
        pass  # OpenAI失败时自动回退本地模型
    
    # 本地模型（零依赖）
    embedding = model.encode(text).tolist()
    print(f"[EMBED] Using local sentence-transformers (384-dim)")
    return embedding
