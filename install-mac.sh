#!/bin/bash
# 太极OS Mac 一键安装脚本

set -e

echo "🚀 开始安装太极OS..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3.12+"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 创建工作目录
INSTALL_DIR="$HOME/taijios"
echo "📁 安装目录: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  目录已存在，跳过创建"
else
    mkdir -p "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 克隆记忆同步仓库
if [ -d "memory-sync" ]; then
    echo "📥 更新记忆同步..."
    cd memory-sync
    git pull
    cd ..
else
    echo "📥 克隆记忆同步仓库..."
    git clone https://github.com/shanhaiying/taijios-memory-sync.git memory-sync
fi

# 安装依赖
echo "📦 安装依赖..."
pip3 install torch sentence-transformers lancedb psutil fastapi uvicorn prometheus-client numpy pandas matplotlib --quiet

# 创建符号链接
if [ -d "aios" ]; then
    echo "✅ AIOS 目录已存在"
else
    if [ -d "memory-sync/aios" ]; then
        ln -s memory-sync/aios aios
        echo "✅ 创建 AIOS 符号链接"
    fi
fi

# 启动 Memory Server
echo "🚀 启动 Memory Server..."
cd "$INSTALL_DIR/aios/agent_system"
python3 memory_server.py &

sleep 3

# 验证
if curl -s http://localhost:7788/status > /dev/null; then
    echo "✅ Memory Server 启动成功！"
    echo "📍 访问: http://localhost:7788/status"
else
    echo "⚠️  Memory Server 启动中，请稍候..."
fi

echo ""
echo "🎉 太极OS 安装完成！"
echo ""
echo "📋 下一步："
echo "  1. 查看状态: curl http://localhost:7788/status"
echo "  2. 进入目录: cd $INSTALL_DIR/aios/agent_system"
echo "  3. 运行健康检查: python3 health_check_v2.py"
