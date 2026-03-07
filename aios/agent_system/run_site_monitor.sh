#!/usr/bin/env bash
set -euo pipefail

# === 配置（根据你的环境修改）===
ROOT="/path/to/your/repo"  # ← 改成你的仓库路径
PY="/usr/bin/python3"      # ← 改成你的 python3 路径（which python3）
CFG="$ROOT/monitors.yaml"
STATE="$ROOT/monitors_state.json"
HB="$ROOT/reports/heartbeat_monitor.md"
LOGDIR="$ROOT/logs"
LOCK="/tmp/site_monitor.lock"

# Telegram（可选）
# export TG_BOT_TOKEN="YOUR_TOKEN"
# export TG_CHAT_ID="7986452220"

# 时区
export MONITOR_TZ="Asia/Kuala_Lumpur"

# 创建日志目录
mkdir -p "$LOGDIR"
mkdir -p "$(dirname "$HB")"

# 切换到工作目录
cd "$ROOT"

# 防止 cron 触发重叠：flock 互斥锁
/usr/bin/flock -n "$LOCK" \
  "$PY" site_monitor.py \
    --config "$CFG" \
    --state "$STATE" \
    --heartbeat "$HB" \
    "$@" \
    >> "$LOGDIR/site_monitor.log" 2>&1

exit $?
