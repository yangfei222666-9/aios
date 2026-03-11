#!/usr/bin/env python3
"""Update draft registry index"""
import json
from pathlib import Path
from datetime import datetime

def update_registry(skill_id: str, status: str = "validated"):
    """更新 draft registry index"""
    
    index_file = Path("draft_registry/index.json")
    
    # 读取现有 index
    if index_file.exists():
        index = json.loads(index_file.read_text(encoding='utf-8'))
    else:
        index = {"skills": [], "last_updated": None}
    
    # 读取 meta
    meta_file = Path(f"draft_registry/{skill_id}/meta.json")
    if not meta_file.exists():
        return {"success": False, "error": "meta.json not found"}
    
    meta = json.loads(meta_file.read_text(encoding='utf-8'))
    
    # 更新 meta 状态
    meta["status"] = status
    meta["validated_at"] = datetime.now().isoformat()
    meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # 检查是否已存在
    existing = None
    for i, skill in enumerate(index["skills"]):
        if skill["skill_id"] == skill_id:
            existing = i
            break
    
    # 构建 index entry
    entry = {
        "skill_id": skill_id,
        "name": meta["name"],
        "version": meta["version"],
        "status": status,
        "risk_level": meta.get("risk_level", "unknown"),
        "confidence": meta.get("confidence", 0.0),
        "created_at": meta["created_at"],
        "validated_at": meta.get("validated_at")
    }
    
    if existing is not None:
        index["skills"][existing] = entry
    else:
        index["skills"].append(entry)
    
    index["last_updated"] = datetime.now().isoformat()
    
    # 写回
    index_file.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    
    return {"success": True, "skill_id": skill_id, "status": status}

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python update_registry.py <skill_id> [status]")
        sys.exit(1)
    
    skill_id = sys.argv[1]
    status = sys.argv[2] if len(sys.argv) > 2 else "validated"
    
    result = update_registry(skill_id, status)
    
    if result["success"]:
        print(f"✅ Registry updated: {skill_id} -> {status}")
    else:
        print(f"❌ Failed: {result['error']}")
        sys.exit(1)
