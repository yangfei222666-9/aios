#!/usr/bin/env python3
"""
Context Manager Agent
管理 Agent 间的上下文传递和共享
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class ContextManager:
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.context_file = self.data_dir / "agent_contexts.json"
        self.load_contexts()
    
    def load_contexts(self):
        """加载上下文数据"""
        if self.context_file.exists():
            with open(self.context_file, 'r', encoding='utf-8') as f:
                self.contexts = json.load(f)
        else:
            self.contexts = {
                "contexts": {},
                "last_updated": None
            }
    
    def save_contexts(self):
        """保存上下文数据"""
        self.contexts["last_updated"] = datetime.now().isoformat()
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(self.contexts, f, indent=2, ensure_ascii=False)
    
    def set_context(self, agent_id: str, key: str, value: Any, ttl: int = 3600) -> Dict[str, Any]:
        """设置上下文"""
        if agent_id not in self.contexts["contexts"]:
            self.contexts["contexts"][agent_id] = {}
        
        self.contexts["contexts"][agent_id][key] = {
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
            "ttl": ttl
        }
        
        self.save_contexts()
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "key": key,
            "ttl": ttl
        }
    
    def get_context(self, agent_id: str, key: str) -> Dict[str, Any]:
        """获取上下文"""
        if agent_id not in self.contexts["contexts"]:
            return {
                "status": "not_found",
                "message": f"No context for agent: {agent_id}"
            }
        
        if key not in self.contexts["contexts"][agent_id]:
            return {
                "status": "not_found",
                "message": f"Key not found: {key}"
            }
        
        context = self.contexts["contexts"][agent_id][key]
        
        # 检查是否过期
        expires_at = datetime.fromisoformat(context["expires_at"])
        if datetime.now() > expires_at:
            # 删除过期上下文
            del self.contexts["contexts"][agent_id][key]
            self.save_contexts()
            return {
                "status": "expired",
                "message": f"Context expired at {context['expires_at']}"
            }
        
        return {
            "status": "success",
            "value": context["value"],
            "created_at": context["created_at"],
            "expires_at": context["expires_at"]
        }
    
    def share_context(self, from_agent: str, to_agent: str, key: str) -> Dict[str, Any]:
        """在 Agent 间共享上下文"""
        # 获取源 Agent 的上下文
        source_context = self.get_context(from_agent, key)
        
        if source_context["status"] != "success":
            return source_context
        
        # 复制到目标 Agent
        if to_agent not in self.contexts["contexts"]:
            self.contexts["contexts"][to_agent] = {}
        
        self.contexts["contexts"][to_agent][key] = self.contexts["contexts"][from_agent][key].copy()
        self.save_contexts()
        
        return {
            "status": "success",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "key": key
        }
    
    def list_contexts(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """列出上下文"""
        if agent_id:
            if agent_id not in self.contexts["contexts"]:
                return {
                    "status": "not_found",
                    "message": f"No context for agent: {agent_id}"
                }
            
            contexts = {agent_id: self.contexts["contexts"][agent_id]}
        else:
            contexts = self.contexts["contexts"]
        
        # 清理过期上下文
        now = datetime.now()
        cleaned_contexts = {}
        
        for aid, agent_contexts in contexts.items():
            cleaned_contexts[aid] = {}
            for key, context in agent_contexts.items():
                expires_at = datetime.fromisoformat(context["expires_at"])
                if now <= expires_at:
                    cleaned_contexts[aid][key] = {
                        "created_at": context["created_at"],
                        "expires_at": context["expires_at"],
                        "ttl": context["ttl"]
                    }
        
        return {
            "status": "success",
            "contexts": cleaned_contexts,
            "agent_count": len(cleaned_contexts)
        }
    
    def cleanup_expired(self) -> Dict[str, Any]:
        """清理过期上下文"""
        now = datetime.now()
        removed_count = 0
        
        for agent_id in list(self.contexts["contexts"].keys()):
            for key in list(self.contexts["contexts"][agent_id].keys()):
                context = self.contexts["contexts"][agent_id][key]
                expires_at = datetime.fromisoformat(context["expires_at"])
                
                if now > expires_at:
                    del self.contexts["contexts"][agent_id][key]
                    removed_count += 1
            
            # 删除空的 Agent 上下文
            if not self.contexts["contexts"][agent_id]:
                del self.contexts["contexts"][agent_id]
        
        self.save_contexts()
        
        return {
            "status": "success",
            "removed_count": removed_count
        }
    
    def get_shared_context(self, task_id: str) -> Dict[str, Any]:
        """获取任务相关的共享上下文"""
        # 查找与任务相关的上下文
        related_contexts = {}
        
        for agent_id, agent_contexts in self.contexts["contexts"].items():
            for key, context in agent_contexts.items():
                if task_id in str(context.get("value", "")):
                    if agent_id not in related_contexts:
                        related_contexts[agent_id] = {}
                    related_contexts[agent_id][key] = context
        
        return {
            "status": "success",
            "task_id": task_id,
            "contexts": related_contexts
        }

def main():
    import sys
    
    manager = ContextManager()
    
    if len(sys.argv) < 2:
        print("Usage: python context_manager.py [set|get|share|list|cleanup]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "set":
        if len(sys.argv) < 5:
            print("Usage: python context_manager.py set <agent_id> <key> <value> [ttl]")
            sys.exit(1)
        
        agent_id = sys.argv[2]
        key = sys.argv[3]
        value = sys.argv[4]
        ttl = int(sys.argv[5]) if len(sys.argv) > 5 else 3600
        
        result = manager.set_context(agent_id, key, value, ttl)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "get":
        if len(sys.argv) < 4:
            print("Usage: python context_manager.py get <agent_id> <key>")
            sys.exit(1)
        
        agent_id = sys.argv[2]
        key = sys.argv[3]
        
        result = manager.get_context(agent_id, key)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "share":
        if len(sys.argv) < 5:
            print("Usage: python context_manager.py share <from_agent> <to_agent> <key>")
            sys.exit(1)
        
        from_agent = sys.argv[2]
        to_agent = sys.argv[3]
        key = sys.argv[4]
        
        result = manager.share_context(from_agent, to_agent, key)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "list":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else None
        result = manager.list_contexts(agent_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "cleanup":
        result = manager.cleanup_expired()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
