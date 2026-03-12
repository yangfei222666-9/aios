#!/bin/bash
# Memory Server 最小启动脚本

set -e  # 遇到错误立即退出

AIOS_ROOT="$HOME/.openclaw/workspace/aios/agent_system"

echo "=========================================="
echo "Memory Server 启动"
echo "=========================================="
echo ""

# 1. 检查目录
if [ ! -d "$AIOS_ROOT" ]; then
    echo "✗ 错误: $AIOS_ROOT 不存在"
    exit 1
fi

cd "$AIOS_ROOT"
echo "✓ 工作目录: $AIOS_ROOT"
echo ""

# 2. 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "✗ 虚拟环境不存在，正在创建..."
    python3 -m venv .venv
    echo "✓ 虚拟环境已创建"
    echo ""
    
    echo "→ 安装依赖..."
    source .venv/bin/activate
    python -m pip install -U pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "⚠ requirements.txt 不存在，跳过依赖安装"
    fi
    echo ""
else
    echo "✓ 虚拟环境已存在"
    source .venv/bin/activate
    echo ""
fi

# 3. 设置环境变量
export PYTHONIOENCODING="utf-8"
export PYTHONUTF8=1
echo "✓ 环境变量已设置"
echo ""

# 4. 检查 memory_server.py
if [ ! -f "memory_server.py" ]; then
    echo "✗ 错误: memory_server.py 不存在"
    exit 1
fi
echo "✓ memory_server.py 存在"
echo ""

# 5. 启动 Memory Server
echo "→ 启动 Memory Server (端口 7788)..."
echo "  按 Ctrl+C 停止"
echo ""
python memory_server.py
