import asyncio
from aiogram import Bot

async def start_background_tasks(bot: Bot):
    print("[SCHEDULER] Background tasks started (Heartbeat v5 + Cron + Self-learning placeholder)")
    
    while True:
        await asyncio.sleep(60)
        print("[HEARTBEAT] Heartbeat tick - AIOS running independently...")
        # 这里后续直接 import heartbeat_v5 运行
