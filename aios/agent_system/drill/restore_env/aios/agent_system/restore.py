#!/usr/bin/env python3
"""
AIOS 恢复脚本 v2.0
基于最小可恢复集合（MRS）标准
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 定义路径
AGENT_SYSTEM_DIR = Path(__file__).parent
BACKUP_ROOT = AGENT_SYSTEM_DIR.parent / "backups"
DATA_DIR = AGENT_SYSTEM_DIR / "data"
MEMORY_DIR = AGENT_SYSTEM_DIR / "memory"


def list_available_backups() -> List[Dict]:
    """列出所有可用的备份"""
    backups = []
    
    if not BACKUP_ROOT.exists():
        return backups
    
    for backup_dir in sorted(BACKUP_ROOT.iterdir(), reverse=True):
        if not backup_dir.is_dir():
            continue
        
        metadata_file = backup_dir / "backup_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            backups.append({
                "date": backup_dir.name,
                "path": backup_dir,
                "metadata": metadata
            })
        else:
            # 没有元数据的旧备份
            backups.append({
                "date": backup_dir.name,
                "path": backup_dir,
                "metadata": None
            })
    
    return backups


def verify_backup_mrs(backup_dir: Path) -> Tuple[bool, List[str], List[str]]:
    """验证备份的 MRS 完整性"""
    metadata_file = backup_dir / "backup_metadata.json"
    
    if not metadata_file.exists():
        return False, [], ["backup_metadata.json"]
    
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    is_complete = metadata.get("mrs_complete", False)
    backed_up_files = metadata.get("backed_up_files", [])
    missing_files = metadata.get("missing_files", [])
    
    return is_complete, backed_up_files, missing_files


def restore_from_backup(backup_dir: Path, verify_only: bool = False) -> Dict:
    """从备份恢复"""
    print(f"🔍 验证备份: {backup_dir}")
    
    is_complete, backed_up_files, missing_files = verify_backup_mrs(backup_dir)
    
    if not is_complete:
        print(f"\n⚠️  备份不完整！缺少以下文件：")
        for file in missing_files:
            print(f"  ❌ {file}")
    else:
        print(f"✅ 备份完整！")
    
    print(f"\n📋 备份包含 {len(backed_up_files)} 个文件")
    
    if verify_only:
        return {
            "status": "verified",
            "complete": is_complete,
            "files": backed_up_files,
            "missing": missing_files
        }
    
    # 确认恢复
    print(f"\n⚠️  恢复操作会覆盖当前文件！")
    response = input("确认恢复？(yes/no): ")
    if response.lower() != "yes":
        print("❌ 恢复已取消")
        return {"status": "cancelled"}
    
    print(f"\n📦 开始恢复...")
    
    restored_files = []
    failed_files = []
    
    for file_path in backed_up_files:
        src = backup_dir / file_path
        dst = AGENT_SYSTEM_DIR / file_path
        
        if not src.exists():
            failed_files.append(file_path)
            print(f"  ❌ {file_path} (源文件不存在)")
            continue
        
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored_files.append(file_path)
            print(f"  ✓ {file_path}")
        except Exception as e:
            failed_files.append(file_path)
            print(f"  ❌ {file_path} (错误: {e})")
    
    print(f"\n✅ 恢复完成！")
    print(f"  成功: {len(restored_files)}")
    print(f"  失败: {len(failed_files)}")
    
    if failed_files:
        print(f"\n⚠️  以下文件恢复失败：")
        for file in failed_files:
            print(f"  ❌ {file}")
    
    return {
        "status": "completed",
        "complete": is_complete,
        "restored": restored_files,
        "failed": failed_files
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AIOS 恢复脚本 v2.0")
    parser.add_argument("--list", action="store_true", help="列出所有可用的备份")
    parser.add_argument("--verify-mrs", action="store_true", help="只验证 MRS 完整性，不执行恢复")
    parser.add_argument("--date", type=str, help="指定要恢复的备份日期 (YYYY-MM-DD)")
    parser.add_argument("--latest", action="store_true", help="恢复最新的备份")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AIOS 恢复脚本 v2.0")
    print("基于最小可恢复集合（MRS）标准")
    print("=" * 60)
    
    # 列出备份
    if args.list:
        backups = list_available_backups()
        if not backups:
            print("\n❌ 没有找到任何备份")
            sys.exit(1)
        
        print(f"\n📋 可用的备份：")
        for backup in backups:
            metadata = backup["metadata"]
            if metadata:
                mrs_status = "✅ 完整" if metadata.get("mrs_complete") else "⚠️  不完整"
                file_count = len(metadata.get("backed_up_files", []))
                print(f"  {backup['date']} - {file_count} 个文件 - {mrs_status}")
            else:
                print(f"  {backup['date']} - (无元数据)")
        sys.exit(0)
    
    # 选择备份
    backup_dir = None
    
    if args.latest:
        backups = list_available_backups()
        if not backups:
            print("\n❌ 没有找到任何备份")
            sys.exit(1)
        backup_dir = backups[0]["path"]
        print(f"\n📦 使用最新备份: {backup_dir.name}")
    
    elif args.date:
        backup_dir = BACKUP_ROOT / args.date
        if not backup_dir.exists():
            print(f"\n❌ 备份不存在: {args.date}")
            sys.exit(1)
    
    else:
        # 交互式选择
        backups = list_available_backups()
        if not backups:
            print("\n❌ 没有找到任何备份")
            sys.exit(1)
        
        print(f"\n📋 可用的备份：")
        for i, backup in enumerate(backups, 1):
            metadata = backup["metadata"]
            if metadata:
                mrs_status = "✅" if metadata.get("mrs_complete") else "⚠️"
                file_count = len(metadata.get("backed_up_files", []))
                print(f"  {i}. {backup['date']} - {file_count} 个文件 - {mrs_status}")
            else:
                print(f"  {i}. {backup['date']} - (无元数据)")
        
        choice = input(f"\n选择要恢复的备份 (1-{len(backups)}): ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                backup_dir = backups[idx]["path"]
            else:
                print("❌ 无效的选择")
                sys.exit(1)
        except ValueError:
            print("❌ 无效的输入")
            sys.exit(1)
    
    # 执行恢复
    result = restore_from_backup(backup_dir, verify_only=args.verify_mrs)
    
    if args.verify_mrs:
        if result["complete"]:
            print(f"\n✅ MRS 验证通过！")
            sys.exit(0)
        else:
            print(f"\n⚠️  MRS 验证失败！备份不完整")
            sys.exit(1)
    
    if result["status"] == "completed":
        if result["complete"]:
            print(f"\n✅ 恢复完成！系统已恢复到完整状态")
        else:
            print(f"\n⚠️  恢复完成，但备份不完整，系统可能无法完全恢复")


if __name__ == "__main__":
    main()
