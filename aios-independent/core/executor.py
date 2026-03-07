import json
from config import AGENTS_FILE

class AgentExecutor:
    def __init__(self):
        self.agents = self._load_agents()
    
    def _load_agents(self):
        if not AGENTS_FILE.exists():
            print("⚠️ agents.json not found, please copy backup file")
            return {}
        
        with open(AGENTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"[OK] Successfully loaded {len(data)} Agents (from backup)")
        return data
    
    async def execute(self, user_id: int, message: str, tg_msg=None):
        # MVP 版：直接回复确认，后续这里会接完整 LLM + tools + LanceDB
        return f"🦀 AIOS Independent received!\nMessage: {message[:40]}...\nLoaded {len(self.agents)} Agents\n(Heartbeat & Self-learning running in background)"

agent_executor = AgentExecutor()
