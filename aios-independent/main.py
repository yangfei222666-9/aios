from fastapi import FastAPI
from aiogram import Bot, Dispatcher
import asyncio
from contextlib import asynccontextmanager
from config import TELEGRAM_TOKEN
from core.router import dp
from core.scheduler import start_background_tasks

bot = Bot(token=TELEGRAM_TOKEN)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] AIOS Independent service started! Telegram polling enabled")
    asyncio.create_task(dp.start_polling(bot))
    asyncio.create_task(start_background_tasks(bot))
    yield
    print("[SHUTDOWN] AIOS Independent service stopped")

app = FastAPI(title="AIOS Independent", version="0.1.0", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "AIOS Independent v0.1", "agents_loaded": 37}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
