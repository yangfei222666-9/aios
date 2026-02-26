"""
AIOS Backup Skill
备份 AIOS 关键数据
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

def backup_aios():
    """备份关键数据"""
    workspace = Path(r"C:\Users\A\.openclaw\workspace\aios")
    memory_dir = Path(r"C:\Users\A\.openclaw\workspace\memory")
    
    backup_dir = workspace / "backups" / datetime.now().strftime("%Y-%m-%d")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backed_up = []
    errors = []
    
    # 备份关键文件
    files_to_backup = [
        ("data/events.jsonl", workspace),
        ("learning/metrics_history.jsonl", workspace),
        ("agent_system/agents.jsonl", workspace),
        ("agent_system/spawn_requests.jsonl", workspace),
        ("agent_system/spawn_results.jsonl", workspace),
        ("core/alerts.jsonl", workspace),
        ("selflearn-state.json", memory_dir),
        ("lessons.json", memory_dir)
    ]
    
    for file_path, base_dir in files_to_backup:
        src = base_dir / file_path
        
        if src.exists():
            try:
                dst = backup_dir / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                
                # 记录文件大小
                size_kb = src.stat().st_size / 1024
                
                backed_up.append({
                    "file": file_path,
                    "size_kb": round(size_kb, 2),
                    "backup_path": str(dst.relative_to(workspace))
                })
            
            except Exception as e:
                errors.append({
                    "file": file_path,
                    "error": str(e)
                })
    
    # 计算总大小
    total_size_kb = sum(item["size_kb"] for item in backed_up)
    
    return {
        "ok": len(errors) == 0,
        "result": {
            "backup_dir": str(backup_dir),
            "backed_up_count": len(backed_up),
            "backed_up_files": backed_up,
            "total_size_kb": round(total_size_kb, 2),
            "error_count": len(errors),
            "errors": errors
        },
        "evidence": [str(backup_dir)],
        "next": []
    }

if __name__ == "__main__":
    result = backup_aios()
    print(json.dumps(result, indent=2, ensure_ascii=False))
