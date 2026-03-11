#!/usr/bin/env python3
"""
AIOS 备份脚本 v2.0
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

# 最小可恢复集合（MRS）定义
MRS_DEFINITION = {
    "runtime_data": {
        "required": True,
        "files": [
            "agents.json",
            "lessons.json",
            "data/task_queue.jsonl",
            "data/task_executions.jsonl",
            "data/spawn_pending.jsonl",
            "data/spawn_results.jsonl",
            "data/spawn_executions.jsonl",
            "data/tasks.jsonl",
            "data/alerts.jsonl",
            "memory/selflearn-state.json",
        ]
    },
    "config_and_code": {
        "required": True,
        "files": [
            "heartbeat_v5.py",
            "learning_agents.py",
            "aios.py",
            "task_executor.py",
            "learning_scheduler.py",
            "memory_server.py",
        ]
    },
    "memory_and_state": {
        "required": True,
        "files": [
            "../../MEMORY.md",  # workspace 根目录
        ],
        "patterns": [
            "../../memory/2026-*.md",  # workspace/memory 目录
        ]
    },
    "recovery_scripts": {
        "required": True,
        "files": [
            "backup.py",
            "restore.py",
            "MINIMUM_RECOVERABLE_SET.md",
        ]
    },
    "optional_enhancements": {
        "required": False,
        "dirs": [
            "../docs",
            "../dashboard",
        ]
    }
}


def get_recent_memory_files(days: int = 7) -> List[Path]:
    """获取最近 N 天的记忆文件"""
    memory_files = []
    if MEMORY_DIR.exists():
        for file in MEMORY_DIR.glob("2026-*.md"):
            memory_files.append(file)
    
    # 按日期排序，取最近的
    memory_files.sort(reverse=True)
    return memory_files[:days]


def check_mrs_completeness() -> Tuple[bool, List[str], List[str]]:
    """检查 MRS 完整性"""
    missing_files = []
    found_files = []
    
    for category, config in MRS_DEFINITION.items():
        if not config.get("required", True):
            continue
        
        # 检查文件
        for file_path in config.get("files", []):
            full_path = AGENT_SYSTEM_DIR / file_path
            if full_path.exists():
                found_files.append(str(file_path))
            else:
                missing_files.append(str(file_path))
        
        # 检查模式匹配的文件
        for pattern in config.get("patterns", []):
            matched = list(AGENT_SYSTEM_DIR.glob(pattern))
            if matched:
                found_files.extend([str(f.relative_to(AGENT_SYSTEM_DIR)) for f in matched])
            else:
                missing_files.append(f"pattern:{pattern}")
    
    is_complete = len(missing_files) == 0
    return is_complete, found_files, missing_files


def create_backup(check_only: bool = False) -> Dict:
    """创建备份"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_date = datetime.now().strftime("%Y-%m-%d")
    backup_dir = BACKUP_ROOT / backup_date
    
    print(f"🔍 检查 MRS 完整性...")
    is_complete, found_files, missing_files = check_mrs_completeness()
    
    if not is_complete:
        print(f"\n⚠️  MRS 不完整！缺少以下文件：")
        for file in missing_files:
            print(f"  ❌ {file}")
        print(f"\n✅ 已找到的文件：")
        for file in found_files[:5]:  # 只显示前 5 个
            print(f"  ✓ {file}")
        if len(found_files) > 5:
            print(f"  ... 还有 {len(found_files) - 5} 个文件")
        
        if check_only:
            return {
                "status": "incomplete",
                "missing": missing_files,
                "found": found_files
            }
        
        print(f"\n⚠️  继续备份，但恢复时可能不完整")
    else:
        print(f"✅ MRS 完整！所有必需文件都存在")
    
    if check_only:
        return {
            "status": "complete",
            "found": found_files
        }
    
    # 创建备份目录
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 开始备份到: {backup_dir}")
    
    backed_up_files = []
    
    # 备份运行时数据
    print(f"\n[1/4] 备份运行时数据...")
    for file_path in MRS_DEFINITION["runtime_data"]["files"]:
        src = AGENT_SYSTEM_DIR / file_path
        if src.exists():
            dst = backup_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up_files.append(file_path)
            print(f"  ✓ {file_path}")
    
    # 备份配置与代码
    print(f"\n[2/4] 备份配置与代码...")
    for file_path in MRS_DEFINITION["config_and_code"]["files"]:
        src = AGENT_SYSTEM_DIR / file_path
        if src.exists():
            dst = backup_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up_files.append(file_path)
            print(f"  ✓ {file_path}")
    
    # 备份记忆与状态
    print(f"\n[3/4] 备份记忆与状态...")
    for file_path in MRS_DEFINITION["memory_and_state"]["files"]:
        src = AGENT_SYSTEM_DIR / file_path
        if src.exists():
            dst = backup_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up_files.append(file_path)
            print(f"  ✓ {file_path}")
    
    # 备份最近的记忆文件
    recent_memories = get_recent_memory_files(7)
    for memory_file in recent_memories:
        rel_path = memory_file.relative_to(AGENT_SYSTEM_DIR)
        dst = backup_dir / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(memory_file, dst)
        backed_up_files.append(str(rel_path))
        print(f"  ✓ {rel_path}")
    
    # 备份恢复脚本
    print(f"\n[4/4] 备份恢复脚本...")
    for file_path in MRS_DEFINITION["recovery_scripts"]["files"]:
        src = AGENT_SYSTEM_DIR / file_path
        if src.exists():
            dst = backup_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up_files.append(file_path)
            print(f"  ✓ {file_path}")
    
    # 创建备份元数据
    metadata = {
        "timestamp": timestamp,
        "date": backup_date,
        "mrs_complete": is_complete,
        "backed_up_files": backed_up_files,
        "missing_files": missing_files,
        "backup_dir": str(backup_dir)
    }
    
    metadata_file = backup_dir / "backup_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 备份完成！")
    print(f"  备份目录: {backup_dir}")
    print(f"  备份文件数: {len(backed_up_files)}")
    print(f"  MRS 完整性: {'✅ 完整' if is_complete else '⚠️  不完整'}")
    
    return metadata


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AIOS 备份脚本 v2.0")
    parser.add_argument("--check-mrs", action="store_true", help="只检查 MRS 完整性，不执行备份")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AIOS 备份脚本 v2.0")
    print("基于最小可恢复集合（MRS）标准")
    print("=" * 60)
    
    result = create_backup(check_only=args.check_mrs)
    
    if args.check_mrs:
        if result["status"] == "complete":
            print(f"\n✅ MRS 检查通过！所有必需文件都存在")
            sys.exit(0)
        else:
            print(f"\n❌ MRS 检查失败！缺少 {len(result['missing'])} 个文件")
            sys.exit(1)


if __name__ == "__main__":
    main()
