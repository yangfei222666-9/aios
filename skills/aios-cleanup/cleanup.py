"""
AIOS Cleanup Skill
清理 AIOS 旧数据
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_old_data(days=7):
    """清理超过 N 天的数据"""
    workspace = Path(r"C:\Users\A\.openclaw\workspace\aios")
    memory_dir = Path(r"C:\Users\A\.openclaw\workspace\memory")
    cutoff_date = datetime.now() - timedelta(days=days)
    
    cleaned = []
    errors = []
    
    # 1. 清理旧事件
    events_file = workspace / "data" / "events.jsonl"
    if events_file.exists():
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original_count = len(lines)
            
            # 只保留最近 N 天的
            new_lines = []
            for line in lines:
                try:
                    event = json.loads(line)
                    event_time_str = event.get("timestamp", "")
                    
                    # 尝试解析时间戳
                    if event_time_str:
                        # 支持多种格式
                        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                            try:
                                event_time = datetime.strptime(event_time_str.split('.')[0], fmt)
                                break
                            except:
                                continue
                        else:
                            # 无法解析，保留
                            new_lines.append(line)
                            continue
                        
                        if event_time > cutoff_date:
                            new_lines.append(line)
                    else:
                        # 没有时间戳，保留
                        new_lines.append(line)
                
                except Exception as e:
                    # 无法解析的行，保留
                    new_lines.append(line)
            
            # 写回
            with open(events_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            removed = original_count - len(new_lines)
            if removed > 0:
                cleaned.append({
                    "file": "events.jsonl",
                    "before": original_count,
                    "after": len(new_lines),
                    "removed": removed
                })
        
        except Exception as e:
            errors.append({
                "file": "events.jsonl",
                "error": str(e)
            })
    
    # 2. 归档旧日志
    if memory_dir.exists():
        archive_dir = memory_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        for log_file in memory_dir.glob("*.md"):
            # 只处理标准日期格式的文件 (YYYY-MM-DD.md)
            if log_file.stem.count('-') == 2:
                try:
                    date_str = log_file.stem  # 2026-02-24
                    log_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if log_date < cutoff_date:
                        # 归档
                        log_file.rename(archive_dir / log_file.name)
                        cleaned.append({
                            "file": log_file.name,
                            "action": "archived"
                        })
                
                except Exception as e:
                    # 跳过无法解析的文件
                    pass
    
    # 3. 清理临时文件
    temp_patterns = ["*.bak", "*.tmp", "*~"]
    for pattern in temp_patterns:
        for temp_file in workspace.rglob(pattern):
            try:
                temp_file.unlink()
                cleaned.append({
                    "file": str(temp_file.relative_to(workspace)),
                    "action": "deleted"
                })
            except Exception as e:
                errors.append({
                    "file": str(temp_file),
                    "error": str(e)
                })
    
    # 4. 清理 __pycache__
    for pycache_dir in workspace.rglob("__pycache__"):
        try:
            import shutil
            shutil.rmtree(pycache_dir)
            cleaned.append({
                "file": str(pycache_dir.relative_to(workspace)),
                "action": "deleted"
            })
        except Exception as e:
            errors.append({
                "file": str(pycache_dir),
                "error": str(e)
            })
    
    return {
        "ok": len(errors) == 0,
        "result": {
            "cleaned_count": len(cleaned),
            "cleaned_items": cleaned,
            "error_count": len(errors),
            "errors": errors
        },
        "evidence": [str(events_file), str(memory_dir)],
        "next": []
    }

if __name__ == "__main__":
    # 支持命令行参数
    days = 7
    if len(sys.argv) > 1 and sys.argv[1] == "--days":
        days = int(sys.argv[2])
    
    result = cleanup_old_data(days=days)
    print(json.dumps(result, indent=2, ensure_ascii=False))
