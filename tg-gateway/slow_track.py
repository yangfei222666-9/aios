# tg-gateway/slow_track.py - 慢车道：透传到 OpenClaw Gateway
"""
通过 /v1/chat/completions 将消息发给 OpenClaw，拿到回复。
带指数退避重试，应对 502/连接失败等瞬时故障。
"""
import asyncio
import httpx
import logging

from config import OPENCLAW_GATEWAY_URL, OPENCLAW_GATEWAY_TOKEN, OPENCLAW_USER_ID

logger = logging.getLogger("tg-gateway.slow")

COMPLETIONS_URL = f"{OPENCLAW_GATEWAY_URL}/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENCLAW_GATEWAY_TOKEN}",
    "Content-Type": "application/json",
}

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # 秒，指数退避基数
RETRYABLE_STATUS = {502, 503, 429}


async def ask_openclaw(text: str, chat_id: int = None) -> str:
    """
    发送消息到 OpenClaw，返回回复文本。
    瞬时故障（502/503/429/连接失败）自动重试，指数退避。
    """
    user_id = f"{OPENCLAW_USER_ID}:{chat_id}" if chat_id else OPENCLAW_USER_ID

    payload = {
        "model": "clawdbot:main",
        "user": user_id,
        "stream": False,
        "messages": [
            {"role": "user", "content": text}
        ],
    }

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(COMPLETIONS_URL, headers=HEADERS, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        return "⚠️ OpenClaw 没有返回内容"
                    content = choices[0].get("message", {}).get("content", "")
                    return content.strip() if content else "⚠️ OpenClaw 返回了空内容"

                # 可重试的状态码
                if resp.status_code in RETRYABLE_STATUS:
                    last_error = f"HTTP {resp.status_code}"
                    logger.warning(f"OpenClaw {last_error}, 重试 {attempt+1}/{MAX_RETRIES}")
                    await asyncio.sleep(RETRY_BASE_DELAY * (2 ** attempt))
                    continue

                # 不可重试的错误，直接返回
                logger.error(f"OpenClaw returned {resp.status_code}: {resp.text[:500]}")
                return f"⚠️ OpenClaw 返回错误 ({resp.status_code})"

        except httpx.TimeoutException:
            last_error = "响应超时"
            logger.warning(f"OpenClaw 超时, 重试 {attempt+1}/{MAX_RETRIES}")
            await asyncio.sleep(RETRY_BASE_DELAY * (2 ** attempt))
        except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
            last_error = str(e)
            logger.warning(f"OpenClaw 连接失败: {e}, 重试 {attempt+1}/{MAX_RETRIES}")
            await asyncio.sleep(RETRY_BASE_DELAY * (2 ** attempt))
        except Exception as e:
            # 未知异常不重试
            logger.error(f"OpenClaw request failed: {e}")
            return f"⚠️ 请求失败: {e}"

    logger.error(f"OpenClaw 重试 {MAX_RETRIES} 次后仍失败: {last_error}")
    return f"⚠️ OpenClaw 暂时不可用（{last_error}），已重试 {MAX_RETRIES} 次"
