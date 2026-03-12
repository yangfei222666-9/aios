#!/usr/bin/env python3
"""
AIOS 每日自动备份到 G 盘
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# 定义路径
AGENT_SYSTEM_DIR = Path(__file__).parent
AIOS_ROOT = AGENT_SYSTEM_DIR.parent
WORKSPACE_DIR = AIOS_ROOT.parent  # C:\Users\A\.openclaw\workspace

# G 盘备份目录
G_DRIVE_BACKUP = Path("G:/AIOS_Backups")

def backup_to_g_drive():
    """备份太极OS到 G 盘"""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup_dir = G_DRIVE_BACKUP / timestamp
    
    print(f"=" * 60)
    print(f"AIOS 每日自动备份到 G 盘")
    print(f"=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: {backup_dir}")
    print()
    
    # 检查 G 盘是否可用
    if not G_DRIVE_BACKUP.parent.exists():
        print(f"❌ G 盘不可用！")
        return False
    
    # 创建备份目录
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 备份整个 aios 目录
    print(f"📦 备份 aios 目录...")
    aios_backup = backup_dir / "aios"
    if aios_backup.exists():
        shutil.rmtree(aios_backup)
    
    # 复制 aios 目录，排除 backups 和 __pycache__
    shutil.copytree(
        AIOS_ROOT,
        aios_backup,
        ignore=shutil.ignore_patterns(
            "backups", "__pycache__", "*.pyc", ".DS_Store",
            "drill", "*.log", "node_modules"
        )
    )
    print(f"  ✓ aios 目录已备份")
    
    # 备份 workspace 关键文件
    print(f"\n📦 备份 workspace 关键文件...")
    workspace_backup = backup_dir / "workspace"
    workspace_backup.mkdir(exist_ok=True)
    
    # 备份 MEMORY.md
    if (WORKSPACE_DIR / "MEMORY.md").exists():
        shutil.copy2(WORKSPACE_DIR / "MEMORY.md", workspace_backup / "MEMORY.md")
        print(f"  ✓ MEMORY.md")
    
    # 备份 memory 目录（最近 14 天）
    memory_dir = WORKSPACE_DIR / "memory"
    if memory_dir.exists():
        memory_backup = workspace_backup / "memory"
        memory_backup.mkdir(exist_ok=True)
        
        # 复制最近 14 天的记忆文件
        memory_files = sorted(memory_dir.glob("2026-*.md"), reverse=True)[:14]
        for file in memory_files:
            shutil.copy2(file, memory_backup / file.name)
            print(f"  ✓ memory/{file.name}")
        
        # 复制 lessons.json
        if (memory_dir / "lessons.json").exists():
            shutil.copy2(memory_dir / "lessons.json", memory_backup / "lessons.json")
            print(f"  ✓ memory/lessons.json")
    
    # 备份 AGENTS.md, SOUL.md, USER.md 等配置文件
    for config_file in ["AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md", "IDENTITY.md"]:
        if (WORKSPACE_DIR / config_file).exists():
            shutil.copy2(WORKSPACE_DIR / config_file, workspace_backup / config_file)
            print(f"  ✓ {config_file}")
    
    # 创建备份元数据
    metadata_file = backup_dir / "backup_info.txt"
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(f"AIOS 自动备份\n")
        f.write(f"=" * 60 + "\n")
        f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"备份目录: {backup_dir}\n")
        f.write(f"\n备份内容:\n")
        f.write(f"  - aios/ (完整目录，排除 backups 和临时文件)\n")
        f.write(f"  - workspace/MEMORY.md\n")
        f.write(f"  - workspace/memory/ (最近 14 天)\n")
        f.write(f"  - workspace/*.md (配置文件)\n")
    
    print(f"\n✅ 备份完成！")
    print(f"  备份目录: {backup_dir}")
    print(f"  备份大小: {get_dir_size(backup_dir):.2f} MB")
    
    # 清理旧备份（保留最近 30 天）
    cleanup_old_backups(days=30)
    
    return True


def get_dir_size(path: Path) -> float:
    """获取目录大小（MB）"""
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total / (1024 * 1024)


def cleanup_old_backups(days: int = 30):
    """清理旧备份"""
    if not G_DRIVE_BACKUP.exists():
        return
    
    print(f"\n🧹 清理 {days} 天前的旧备份...")
    
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    for backup_dir in G_DRIVE_BACKUP.iterdir():
        if not backup_dir.is_dir():
            continue
        
        try:
            backup_date = datetime.strptime(backup_dir.name, "%Y-%m-%d")
            if backup_date < cutoff_date:
                shutil.rmtree(backup_dir)
                deleted_count += 1
                print(f"  🗑️  删除: {backup_dir.name}")
        except ValueError:
            continue
    
    if deleted_count == 0:
        print(f"  ✓ 无需清理")
    else:
        print(f"  ✓ 已删除 {deleted_count} 个旧备份")


if __name__ == "__main__":
    try:
        success = backup_to_g_drive()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 备份失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
