# tg-gateway/bot.py - Telegram Bot 主入口
"""
单 Bot 反向代理：快车道本地执行，慢车道透传 OpenClaw。
用法: python bot.py
"""
import asyncio
import logging
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    ContextTypes, filters
)

from config import TG_BOT_TOKEN, ALLOWED_USER_IDS
from router import classify
from fast_track import execute_fast
from slow_track import ask_openclaw

# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("tg-gateway")


def is_allowed(update: Update) -> bool:
    """检查用户是否在白名单"""
    user = update.effective_user
    if not user:
        return False
    return user.id in ALLOWED_USER_IDS


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理所有文本消息"""
    if not is_allowed(update):
        return

    text = update.message.text
    if not text:
        return

    chat_id = update.effective_chat.id
    logger.info(f"收到消息: {text[:50]}...")

    try:
        # 路由判断
        result = classify(text)

        if result["track"] == "fast":
            # 快车道：本地执行
            logger.info(f"快车道: {result['resolve_result']['action']} {result['resolve_result']['canonical']}")
            reply = execute_fast(result["resolve_result"])
        else:
            # 慢车道：透传 OpenClaw
            logger.info("慢车道: 转发到 OpenClaw")
            reply = await ask_openclaw(text, chat_id)
    except Exception as e:
        logger.exception(f"处理消息时出错: {e}")
        reply = f"⚠️ 内部错误: {e}"

    # 发送回复
    if reply:
        try:
            if len(reply) > 4000:
                chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(reply)
        except Exception as e:
            logger.exception(f"发送回复失败: {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理语音消息：下载 → 本地 whisper 转写 → 路由"""
    if not is_allowed(update):
        return

    # TODO: Phase 2 - 本地 faster-whisper 转写
    # 目前先发到慢车道让 OpenClaw 处理
    await update.message.reply_text("🎙️ 语音处理暂未接入，请发文字消息")


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """健康检查"""
    if not is_allowed(update):
        return
    await update.message.reply_text("🏓 pong — tg-gateway 运行中")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """状态查询"""
    if not is_allowed(update):
        return

    import httpx
    from config import OPENCLAW_GATEWAY_URL, OPENCLAW_GATEWAY_TOKEN

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{OPENCLAW_GATEWAY_URL}/tools/invoke",
                headers={
                    "Authorization": f"Bearer {OPENCLAW_GATEWAY_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={"tool": "sessions_list", "args": {}},
            )
            if resp.status_code == 200:
                openclaw_status = "✅ 在线"
            else:
                openclaw_status = f"⚠️ HTTP {resp.status_code}"
    except Exception as e:
        openclaw_status = f"❌ 离线 ({e})"

    await update.message.reply_text(
        f"tg-gateway 状态\n"
        f"• Bot: ✅ 运行中\n"
        f"• OpenClaw Gateway: {openclaw_status}"
    )


def main():
    logger.info("启动 tg-gateway...")

    app = Application.builder().token(TG_BOT_TOKEN).build()

    # 命令
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("status", cmd_status))

    # 语音消息
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    # 文本消息（最后注册，兜底）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot 已启动，等待消息...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
