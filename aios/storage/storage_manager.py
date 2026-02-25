"""AIOS Storage Manager - 使用 aiosqlite + aiosql"""
import aiosql
import aiosqlite
import json
import time
from pathlib import Path

# 加载 SQL 查询
QUERIES_PATH = Path(__file__).parent / "queries.sql"
queries = aiosql.from_path(str(QUERIES_PATH), "aiosqlite", encoding="utf-8")

DB_PATH = Path(__file__).parent.parent / "data" / "aios.db"


class StorageManager:
    """AIOS 存储管理器"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def init_db(self):
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await queries.create_agent_states_table(db)
            await queries.create_contexts_table(db)
            await queries.create_events_table(db)
            await db.commit()
    
    # ==================== Agent States ====================
    
    async def save_agent_state(self, agent_id: str, state: dict):
        """保存 Agent 状态"""
        async with aiosqlite.connect(self.db_path) as db:
            await queries.save_agent_state(
                db,
                agent_id=agent_id,
                state=json.dumps(state),
                timestamp=time.time()
            )
            await db.commit()
    
    async def get_agent_state(self, agent_id: str) -> dict:
        """获取 Agent 状态"""
        async with aiosqlite.connect(self.db_path) as db:
            result = await queries.get_agent_state(db, agent_id=agent_id)
            if result:
                return json.loads(result)
            return None
    
    async def get_all_active_agents(self) -> list:
        """获取所有活跃 Agent"""
        async with aiosqlite.connect(self.db_path) as db:
            rows = await queries.get_all_active_agents(db)
            return [
                {
                    'agent_id': row[0],
                    'state': json.loads(row[1]),
                    'timestamp': row[2]
                }
                for row in rows
            ]
    
    async def deactivate_agent(self, agent_id: str):
        """停用 Agent"""
        async with aiosqlite.connect(self.db_path) as db:
            await queries.deactivate_agent(db, agent_id=agent_id)
            await db.commit()
    
    # ==================== Contexts ====================
    
    async def save_context(self, agent_id: str, context: dict):
        """保存上下文"""
        async with aiosqlite.connect(self.db_path) as db:
            await queries.save_context(
                db,
                agent_id=agent_id,
                context=json.dumps(context),
                timestamp=time.time()
            )
            await db.commit()
    
    async def get_latest_context(self, agent_id: str) -> dict:
        """获取最新上下文"""
        async with aiosqlite.connect(self.db_path) as db:
            result = await queries.get_latest_context(db, agent_id=agent_id)
            if result:
                return json.loads(result)
            return None
    
    async def get_context_history(self, agent_id: str, limit: int = 10) -> list:
        """获取上下文历史"""
        async with aiosqlite.connect(self.db_path) as db:
            rows = await queries.get_context_history(db, agent_id=agent_id, limit=limit)
            return [
                {
                    'context': json.loads(row[0]),
                    'timestamp': row[1]
                }
                for row in rows
            ]
    
    # ==================== Events ====================
    
    async def save_event(self, event: dict):
        """保存事件"""
        async with aiosqlite.connect(self.db_path) as db:
            await queries.save_event(
                db,
                type=event.get('type', 'unknown'),
                level=event.get('level', 'info'),
                message=event.get('message', ''),
                data=json.dumps(event.get('data', {})),
                timestamp=event.get('timestamp', time.time())
            )
            await db.commit()
    
    async def get_recent_events(self, limit: int = 100) -> list:
        """获取最近事件"""
        async with aiosqlite.connect(self.db_path) as db:
            rows = await queries.get_recent_events(db, limit=limit)
            return [
                {
                    'type': row[0],
                    'level': row[1],
                    'message': row[2],
                    'data': json.loads(row[3]) if row[3] else {},
                    'timestamp': row[4]
                }
                for row in rows
            ]
    
    async def get_error_events(self, limit: int = 100) -> list:
        """获取错误事件"""
        async with aiosqlite.connect(self.db_path) as db:
            rows = await queries.get_error_events(db, limit=limit)
            return [
                {
                    'type': row[0],
                    'level': row[1],
                    'message': row[2],
                    'data': json.loads(row[3]) if row[3] else {},
                    'timestamp': row[4]
                }
                for row in rows
            ]
    
    # ==================== Cleanup ====================
    
    async def cleanup_old_data(self, days: int = 7):
        """清理旧数据"""
        before_timestamp = time.time() - (days * 86400)
        async with aiosqlite.connect(self.db_path) as db:
            await queries.delete_old_events(db, before_timestamp=before_timestamp)
            await queries.delete_old_contexts(db, before_timestamp=before_timestamp)
            await db.commit()


# ==================== 使用示例 ====================

async def example():
    """使用示例"""
    storage = StorageManager()
    
    # 初始化数据库
    await storage.init_db()
    
    # 保存 Agent 状态
    await storage.save_agent_state('agent_001', {
        'status': 'running',
        'task': 'learning',
        'progress': 0.5
    })
    
    # 获取 Agent 状态
    state = await storage.get_agent_state('agent_001')
    print(f"Agent state: {state}")
    
    # 保存上下文
    await storage.save_context('agent_001', {
        'conversation': ['Hello', 'Hi there!'],
        'memory': {'key': 'value'}
    })
    
    # 保存事件
    await storage.save_event({
        'type': 'agent_created',
        'level': 'info',
        'message': 'Agent 001 created',
        'data': {'agent_id': 'agent_001'}
    })
    
    # 获取最近事件
    events = await storage.get_recent_events(limit=10)
    print(f"Recent events: {len(events)}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(example())
