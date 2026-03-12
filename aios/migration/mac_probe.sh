#!/bin/bash
# macOS 环境探针 - 只检查，不修改

echo "=========================================="
echo "macOS 环境探针"
echo "=========================================="
echo ""

# 1. 确认用户
echo "1. 当前用户："
whoami
echo ""

# 2. 确认 Python
echo "2. Python 环境："
if command -v python3 &> /dev/null; then
    echo "  ✓ python3 路径: $(command -v python3)"
    echo "  ✓ python3 版本: $(python3 --version)"
else
    echo "  ✗ python3 未找到"
fi
echo ""

# 3. 确认目录
echo "3. 工作目录："
if [ -d "$HOME/.openclaw/workspace" ]; then
    echo "  ✓ ~/.openclaw/workspace 存在"
else
    echo "  ✗ ~/.openclaw/workspace 不存在"
    echo "  → 创建目录..."
    mkdir -p "$HOME/.openclaw/workspace"
    echo "  ✓ 已创建"
fi
echo ""

# 4. 确认项目文件
echo "4. 项目文件："
if [ -d "$HOME/.openclaw/workspace/aios/agent_system" ]; then
    echo "  ✓ aios/agent_system 存在"
    echo "  → 关键文件检查："
    
    files=(
        "memory_server.py"
        "heartbeat_v5.py"
        "learning_agents.py"
        "data/agents.json"
        "lessons.json"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$HOME/.openclaw/workspace/aios/agent_system/$file" ]; then
            echo "    ✓ $file"
        else
            echo "    ✗ $file 缺失"
        fi
    done
else
    echo "  ✗ aios/agent_system 不存在"
    echo "  → 需要先传输项目文件"
fi
echo ""

# 5. 端口检查
echo "5. 端口占用："
ports=(7788 8888 8889)
for port in "${ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  ✗ 端口 $port 已被占用"
    else
        echo "  ✓ 端口 $port 可用"
    fi
done
echo ""

echo "=========================================="
echo "探针完成"
echo "=========================================="
