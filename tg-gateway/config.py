# tg-gateway/config.py - 配置
"""所有可配置项集中在这里，方便后续改成 .env 或 YAML"""

# Telegram Bot Token (新 Bot)
TG_BOT_TOKEN = "8297495903:AAFwnRpSiBCo946x_NzK7kA10ToniDOium8"

# 允许的 Telegram 用户 ID（只响应珊瑚海）
ALLOWED_USER_IDS = {7986452220}

# OpenClaw Gateway
OPENCLAW_GATEWAY_URL = "http://127.0.0.1:18789"
OPENCLAW_GATEWAY_TOKEN = "10d1f57377d222dc29e71c1efcd81eeb58b1ab0c84086013"

# 快车道：简单命令的动作前缀
FAST_TRACK_PREFIXES = [
    "打开", "打開", "启动", "关闭", "關閉", "退出", "停止",
]

# 用户标识（用于 chatCompletions 的 user 字段，绑定稳定 session）
OPENCLAW_USER_ID = "shanhuhai-tg-gateway"
