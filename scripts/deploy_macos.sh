#!/bin/bash
# MacBook 快速部署脚本 - 太极OS (TaijiOS)
# 版本: v1.0
# 日期: 2026-03-10

set -e  # 遇到错误立即退出

echo "🚀 太极OS MacBook 部署脚本 v1.0"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

# 步骤 1: 检查系统要求
echo "📋 步骤 1/8: 检查系统要求"
echo "------------------------"

if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}错误: 此脚本仅支持 macOS${NC}"
    exit 1
fi

echo "✓ 操作系统: macOS"
echo "✓ 用户: $(whoami)"
echo "✓ 主目录: $HOME"
echo ""

# 步骤 2: 检查必需工具
echo "🔧 步骤 2/8: 检查必需工具"
echo "------------------------"

MISSING_TOOLS=0

if ! check_command brew; then
    echo -e "${YELLOW}正在安装 Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

if ! check_command python3.12; then
    echo -e "${YELLOW}正在安装 Python 3.12...${NC}"
    brew install python@3.12
fi

if ! check_command node; then
    echo -e "${YELLOW}正在安装 Node.js...${NC}"
    brew install node
fi

if ! check_command git; then
    echo -e "${YELLOW}正在安装 Git...${NC}"
    brew install git
fi

echo ""

# 步骤 3: 安装 OpenClaw
echo "📦 步骤 3/8: 安装 OpenClaw"
echo "------------------------"

if ! command -v openclaw &> /dev/null; then
    echo "正在安装 OpenClaw..."
    npm install -g openclaw-cn
else
    echo "✓ OpenClaw 已安装"
    openclaw --version
fi

echo ""

# 步骤 4: 创建工作目录
echo "📁 步骤 4/8: 创建工作目录"
echo "------------------------"

WORKSPACE="$HOME/.openclaw/workspace"

if [ ! -d "$WORKSPACE" ]; then
    echo "创建工作目录: $WORKSPACE"
    mkdir -p "$WORKSPACE"
else
    echo "✓ 工作目录已存在: $WORKSPACE"
fi

cd "$WORKSPACE"
echo "✓ 当前目录: $(pwd)"
echo ""

# 步骤 5: 克隆或同步 AIOS
echo "🔄 步骤 5/8: 设置 AIOS"
echo "------------------------"

if [ ! -d "$WORKSPACE/aios" ]; then
    echo "请选择 AIOS 来源:"
    echo "1) 从 Git 仓库克隆"
    echo "2) 从 Windows 同步（需要手动复制）"
    echo "3) 跳过（稍后手动设置）"
    read -p "请选择 (1-3): " choice
    
    case $choice in
        1)
            read -p "请输入 Git 仓库 URL: " repo_url
            git clone "$repo_url" aios
            ;;
        2)
            echo -e "${YELLOW}请手动将 Windows 上的 aios 目录复制到:${NC}"
            echo "$WORKSPACE/aios"
            echo "完成后按回车继续..."
            read
            ;;
        3)
            echo "跳过 AIOS 设置"
            ;;
        *)
            echo "无效选择，跳过"
            ;;
    esac
else
    echo "✓ AIOS 目录已存在"
fi

echo ""

# 步骤 6: 安装 Python 依赖
echo "🐍 步骤 6/8: 安装 Python 依赖"
echo "------------------------"

if [ -d "$WORKSPACE/aios" ]; then
    cd "$WORKSPACE/aios"
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        echo "创建 Python 虚拟环境..."
        python3.12 -m venv venv
    fi
    
    echo "激活虚拟环境..."
    source venv/bin/activate
    
    echo "升级 pip..."
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        echo "从 requirements.txt 安装依赖..."
        pip install -r requirements.txt
    else
        echo "安装核心依赖..."
        pip install anthropic openai requests pyyaml jsonlines sentence-transformers chromadb
    fi
    
    echo "✓ Python 依赖安装完成"
else
    echo -e "${YELLOW}⚠ AIOS 目录不存在，跳过 Python 依赖安装${NC}"
fi

echo ""

# 步骤 7: 配置 OpenClaw
echo "⚙️  步骤 7/8: 配置 OpenClaw"
echo "------------------------"

if ! openclaw gateway status &> /dev/null; then
    echo "启动 OpenClaw Gateway..."
    openclaw gateway start
    
    echo ""
    echo "请按照提示配置 OpenClaw:"
    echo "- Anthropic API Key"
    echo "- 默认模型"
    echo "- Telegram Bot Token（可选）"
    echo ""
else
    echo "✓ OpenClaw Gateway 已运行"
fi

echo ""

# 步骤 8: 设置自启动服务
echo "🔄 步骤 8/8: 设置自启动服务"
echo "------------------------"

read -p "是否设置 Memory Server 开机自启动? (y/n): " setup_autostart

if [[ "$setup_autostart" == "y" ]]; then
    PLIST_FILE="$HOME/Library/LaunchAgents/com.taijios.memory-server.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taijios.memory-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3.12)</string>
        <string>$WORKSPACE/aios/agent_system/memory_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$WORKSPACE/aios/agent_system/memory_server.log</string>
    <key>StandardErrorPath</key>
    <string>$WORKSPACE/aios/agent_system/memory_server_error.log</string>
</dict>
</plist>
EOF
    
    launchctl load "$PLIST_FILE"
    echo "✓ Memory Server 自启动已设置"
else
    echo "跳过自启动设置"
fi

echo ""

# 完成
echo "================================"
echo "🎉 部署完成！"
echo "================================"
echo ""
echo "下一步:"
echo "1. 配置核心文件 (AGENTS.md, SOUL.md, USER.md, etc.)"
echo "2. 启动 Memory Server:"
echo "   cd $WORKSPACE/aios/agent_system"
echo "   python3.12 memory_server.py"
echo ""
echo "3. 测试系统:"
echo "   python3.12 heartbeat_v5.py"
echo "   python3.12 aios.py status"
echo ""
echo "4. 查看文档:"
echo "   cat $WORKSPACE/docs/MACOS_DEPLOYMENT.md"
echo ""
echo "祝使用愉快！ 🐾"
