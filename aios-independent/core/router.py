from aiogram import Router, Dispatcher
from aiogram.types import Message
from core.executor import agent_executor

router = Router()
dp = Dispatcher()
dp.include_router(router)

@router.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text or "[Non-text message]"
    
    print(f"[MSG] Received Telegram message | {user_id}: {text[:60]}...")
    
    reply_text = await agent_executor.execute(user_id, text, message)
    if reply_text:
        await message.reply(reply_text)
