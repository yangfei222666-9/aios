#!/usr/bin/env python3
"""
AIOS 文档打包工具
打包核心文档、架构设计、使用指南等关键文件
"""
import os
import zipfile
from pathlib import Path
from datetime import datetime

def create_docs_package():
    """创建文档包"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"AIOS_Docs_{timestamp}.zip"
    
    # 定义要打包的文件和目录
    include_patterns = [
        # 核心文档
        "README.md",
        "ARCHITECTURE.md",
        "QUICKSTART.md",
        "TUTORIAL.md",
        "ROADMAP.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        
        # 设计文档
        "docs/*.md",
        "docs/blog/**/*.md",
        
        # 核心代码结构说明
        "core/README.md",
        "agent_system/README.md",
        "dashboard/README.md",
        
        # 配置示例
        "*.json.example",
        "config/*.json.example",
        
        # 使用指南
        "INTEGRATION_GUIDE.md",
        "PLATFORM_GUIDE.md",
        "WORKFLOW_GUIDE.md",
        "SKILL_INTEGRATION.md",
        
        # 开发指南
        "DEV_SETUP.md",
        "QUICK_REFERENCE.md",
        "TEST_COVERAGE.md",
        
        # 发布说明
        "RELEASE_NOTES*.md",
        "BLOG_POST*.md",
    ]
    
    # 排除的目录
    exclude_dirs = {
        "__pycache__",
        ".git",
        "node_modules",
        "venv",
        "dist",
        "build",
        "htmlcov",
        ".pytest_cache",
        "backups",
        "archive",
        "dist_exe",
        "dist_full",
    }
    
    base_dir = Path(__file__).parent
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加根目录的核心文档
        for pattern in ["README.md", "ARCHITECTURE.md", "QUICKSTART.md", "TUTORIAL.md", 
                       "ROADMAP.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md",
                       "INTEGRATION_GUIDE.md", "PLATFORM_GUIDE.md", "WORKFLOW_GUIDE.md",
                       "SKILL_INTEGRATION.md", "DEV_SETUP.md", "QUICK_REFERENCE.md"]:
            file_path = base_dir / pattern
            if file_path.exists():
                zipf.write(file_path, file_path.name)
                print(f"[OK] {file_path.name}")
        
        # 添加 docs 目录
        docs_dir = base_dir / "docs"
        if docs_dir.exists():
            for file_path in docs_dir.rglob("*.md"):
                if not any(excl in file_path.parts for excl in exclude_dirs):
                    arcname = file_path.relative_to(base_dir)
                    zipf.write(file_path, arcname)
                    print(f"[OK] {arcname}")
        
        # 添加发布说明
        for file_path in base_dir.glob("RELEASE_NOTES*.md"):
            zipf.write(file_path, file_path.name)
            print(f"[OK] {file_path.name}")
        
        for file_path in base_dir.glob("BLOG_POST*.md"):
            zipf.write(file_path, file_path.name)
            print(f"[OK] {file_path.name}")
        
        # 添加核心模块的 README
        for module in ["core", "agent_system", "dashboard", "observability"]:
            readme = base_dir / module / "README.md"
            if readme.exists():
                arcname = f"{module}/README.md"
                zipf.write(readme, arcname)
                print(f"[OK] {arcname}")
        
        # 添加配置示例
        for file_path in base_dir.rglob("*.json.example"):
            if not any(excl in file_path.parts for excl in exclude_dirs):
                arcname = file_path.relative_to(base_dir)
                zipf.write(file_path, arcname)
                print(f"[OK] {arcname}")
    
    file_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n[SUCCESS] 文档包创建完成: {output_file}")
    print(f"[INFO] 文件大小: {file_size:.2f} MB")
    print(f"[INFO] 位置: {os.path.abspath(output_file)}")
    
    return output_file

if __name__ == "__main__":
    create_docs_package()
