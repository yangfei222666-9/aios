#!/bin/bash
#
# 太极OS - macOS 自动运行配置脚本
# 让太极OS像在Windows上一样自动工作
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "============================================================"
echo "  太极OS - macOS 自动运行配置"
echo "  让太极OS自己动手工作"
echo "============================================================"
echo ""

# 获取当前目录
TAIJIOS_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_SYSTEM_DIR="$TAIJIOS_DIR/agent_system"

log_info "太极OS 目录: $TAIJIOS_DIR"

# 1. 创建定时任务配置
log_info "配置定时任务（Heartbeat 每6小时执行一次）..."

PLIST_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$PLIST_DIR"

# Memory Server 自启动
cat > "$PLIST_DIR/com.taijios.memoryserver.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taijios.memoryserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3.12)</string>
        <string>$AGENT_SYSTEM_DIR/memory_server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$AGENT_SYSTEM_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$TAIJIOS_DIR/logs/memoryserver.log</string>
    <key>StandardErrorPath</key>
    <string>$TAIJIOS_DIR/logs/memoryserver.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONIOENCODING</key>
        <string>utf-8</string>
        <key>PYTHONUTF8</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF

log_success "创建 Memory Server 自启动配置"

# Dashboard 自启动
cat > "$PLIST_DIR/com.taijios.dashboard.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taijios.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3.12)</string>
        <string>$TAIJIOS_DIR/dashboard/AIOS-Dashboard-v3.4/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$TAIJIOS_DIR/dashboard/AIOS-Dashboard-v3.4</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$TAIJIOS_DIR/logs/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>$TAIJIOS_DIR/logs/dashboard.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONIOENCODING</key>
        <string>utf-8</string>
        <key>PYTHONUTF8</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF

log_success "创建 Dashboard 自启动配置"

# Heartbeat 定时任务（每6小时）
cat > "$PLIST_DIR/com.taijios.heartbeat.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taijios.heartbeat</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3.12)</string>
        <string>$AGENT_SYSTEM_DIR/heartbeat_v5.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$AGENT_SYSTEM_DIR</string>
    <key>StartInterval</key>
    <integer>21600</integer>
    <key>StandardOutPath</key>
    <string>$TAIJIOS_DIR/logs/heartbeat.log</string>
    <key>StandardErrorPath</key>
    <string>$TAIJIOS_DIR/logs/heartbeat.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONIOENCODING</key>
        <string>utf-8</string>
        <key>PYTHONUTF8</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF

log_success "创建 Heartbeat 定时任务配置（每6小时）"

# 创建日志目录
mkdir -p "$TAIJIOS_DIR/logs"
log_success "创建日志目录"

# 2. 加载服务
log_info "加载服务..."

launchctl unload "$PLIST_DIR/com.taijios.memoryserver.plist" 2>/dev/null || true
launchctl load "$PLIST_DIR/com.taijios.memoryserver.plist"
log_success "Memory Server 已加载"

launchctl unload "$PLIST_DIR/com.taijios.dashboard.plist" 2>/dev/null || true
launchctl load "$PLIST_DIR/com.taijios.dashboard.plist"
log_success "Dashboard 已加载"

launchctl unload "$PLIST_DIR/com.taijios.heartbeat.plist" 2>/dev/null || true
launchctl load "$PLIST_DIR/com.taijios.heartbeat.plist"
log_success "Heartbeat 定时任务已加载"

# 3. 验证服务状态
log_info "验证服务状态..."
sleep 3

if curl -s http://127.0.0.1:7788/status > /dev/null 2>&1; then
    log_success "Memory Server 运行正常"
else
    log_warning "Memory Server 可能需要几秒钟启动"
fi

if curl -s http://127.0.0.1:8888 > /dev/null 2>&1; then
    log_success "Dashboard 运行正常"
else
    log_warning "Dashboard 可能需要几秒钟启动"
fi

# 4. 创建管理脚本
log_info "创建管理脚本..."

cat > "$TAIJIOS_DIR/taijios_control.sh" << 'CONTROL_EOF'
#!/bin/bash
# 太极OS 服务控制脚本

case "$1" in
    start)
        echo "启动太极OS服务..."
        launchctl load ~/Library/LaunchAgents/com.taijios.memoryserver.plist
        launchctl load ~/Library/LaunchAgents/com.taijios.dashboard.plist
        launchctl load ~/Library/LaunchAgents/com.taijios.heartbeat.plist
        echo "✓ 服务已启动"
        ;;
    stop)
        echo "停止太极OS服务..."
        launchctl unload ~/Library/LaunchAgents/com.taijios.memoryserver.plist
        launchctl unload ~/Library/LaunchAgents/com.taijios.dashboard.plist
        launchctl unload ~/Library/LaunchAgents/com.taijios.heartbeat.plist
        echo "✓ 服务已停止"
        ;;
    restart)
        echo "重启太极OS服务..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "太极OS 服务状态:"
        echo ""
        echo "Memory Server:"
        if curl -s http://127.0.0.1:7788/status > /dev/null 2>&1; then
            echo "  ✓ 运行中 (http://127.0.0.1:7788)"
        else
            echo "  ✗ 未运行"
        fi
        echo ""
        echo "Dashboard:"
        if curl -s http://127.0.0.1:8888 > /dev/null 2>&1; then
            echo "  ✓ 运行中 (http://127.0.0.1:8888)"
        else
            echo "  ✗ 未运行"
        fi
        echo ""
        echo "Heartbeat:"
        if launchctl list | grep -q com.taijios.heartbeat; then
            echo "  ✓ 定时任务已加载（每6小时执行）"
        else
            echo "  ✗ 定时任务未加载"
        fi
        ;;
    logs)
        echo "查看日志（按 Ctrl+C 退出）:"
        tail -f logs/*.log
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
CONTROL_EOF

chmod +x "$TAIJIOS_DIR/taijios_control.sh"
log_success "创建服务控制脚本: taijios_control.sh"

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 太极OS 自动运行配置完成！${NC}"
echo "============================================================"
echo ""
echo "现在太极OS会："
echo "  1. 开机自动启动 Memory Server 和 Dashboard"
echo "  2. 每6小时自动执行一次 Heartbeat"
echo "  3. 服务崩溃后自动重启"
echo ""
echo "服务管理命令："
echo "  ./taijios_control.sh start    # 启动服务"
echo "  ./taijios_control.sh stop     # 停止服务"
echo "  ./taijios_control.sh restart  # 重启服务"
echo "  ./taijios_control.sh status   # 查看状态"
echo "  ./taijios_control.sh logs     # 查看日志"
echo ""
echo "访问地址："
echo "  Memory Server: http://127.0.0.1:7788"
echo "  Dashboard: http://127.0.0.1:8888"
echo ""
echo "日志位置："
echo "  $TAIJIOS_DIR/logs/"
echo ""
echo "============================================================"
echo ""
