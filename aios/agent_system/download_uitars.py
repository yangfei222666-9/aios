"""
下载 UI-TARS-1.5-7B 模型
"""

from huggingface_hub import snapshot_download
import os

# 设置缓存目录
cache_dir = r"C:\Users\A\.cache\huggingface\hub"
os.makedirs(cache_dir, exist_ok=True)

print("开始下载 UI-TARS-1.5-7B 模型...")
print(f"缓存目录: {cache_dir}")
print("预计大小: ~15GB")
print("这可能需要 10-30 分钟，取决于网速...\n")

try:
    model_path = snapshot_download(
        repo_id="ByteDance-Seed/UI-TARS-1.5-7B",
        cache_dir=cache_dir,
        resume_download=True,  # 支持断点续传
        local_files_only=False
    )
    
    print(f"\n✅ 模型下载完成！")
    print(f"路径: {model_path}")
    
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
    print("\n可能的原因：")
    print("1. 网络连接问题")
    print("2. HuggingFace 访问受限（需要代理）")
    print("3. 磁盘空间不足")
