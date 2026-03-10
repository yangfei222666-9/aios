#!/bin/bash
# Windows → macOS 数据同步脚本
# 版本: v1.0
# 用途: 将 Windows 上的太极OS 数据同步到 macOS

set -e

echo "🔄 太极OS 数据同步脚本 (Windows → macOS)"
echo "========================================"
echo ""

# 配置
MACOS_WORKSPACE="$HOME/.openclaw/workspace"
SYNC_METHOD=""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 选择同步方式
echo "请选择同步方式:"
echo "1) Git 同步（推荐）"
echo "2) rsync 通过 SSH"
echo "3) 手动复制（从共享文件夹/U盘）"
read -p "请选择 (1-3): " SYNC_METHOD

case $SYNC_METHOD in
    1)
        echo ""
        echo "📦 Git 同步模式"
        echo "----------------"
        
        read -p "请输入 Git 仓库 URL: " REPO_URL
        
        if [ -d "$MACOS_WORKSPACE/aios/.git" ]; then
            echo "更新现有仓库..."
            cd "$MACOS_WORKSPACE/aios"
            git pull
        else
            echo "克隆仓库..."
            cd "$MACOS_WORKSPACE"
            git clone "$REPO_URL" aios
        fi
        
        echo -e "${GREEN}✓ Git 同步完成${NC}"
        ;;
        
    2)
        echo ""
        echo "🔗 rsync SSH 同步模式"
        echo "---------------------"
        
        read -p "Windows SSH 地址 (user@ip): " WINDOWS_HOST
        read -p "Windows workspace 路径: " WINDOWS_PATH
        
        echo "同步 AIOS..."
        rsync -avz --progress "$WINDOWS_HOST:$WINDOWS_PATH/aios/" "$MACOS_WORKSPACE/aios/"
        
        echo "同步核心文件..."
        rsync -avz --progress "$WINDOWS_HOST:$WINDOWS_PATH/*.md" "$MACOS_WORKSPACE/"
        
        echo "同步 memory 目录..."
        rsync -avz --progress "$WINDOWS_HOST:$WINDOWS_PATH/memory/" "$MACOS_WORKSPACE/memory/"
        
        echo -e "${GREEN}✓ rsync 同步完成${NC}"
        ;;
        
    3)
        echo ""
        echo "📁 手动复制模式"
        echo "----------------"
        
        read -p "请输入源目录路径（Windows 数据所在位置）: " SOURCE_DIR
        
        if [ ! -d "$SOURCE_DIR" ]; then
            echo -e "${RED}错误: 源目录不存在${NC}"
            exit 1
        fi
        
        echo "复制 AIOS..."
        cp -r "$SOURCE_DIR/aios" "$MACOS_WORKSPACE/"
        
        echo "复制核心文件..."
        cp "$SOURCE_DIR"/*.md "$MACOS_WORKSPACE/" 2>/dev/null || true
        
        echo "复制 memory 目录..."
        cp -r "$SOURCE_DIR/memory" "$MACOS_WORKSPACE/" 2>/dev/null || true
        
        echo -e "${GREEN}✓ 手动复制完成${NC}"
        ;;
        
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "🔍 验证同步结果"
echo "----------------"

# 检查关键文件
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${YELLOW}⚠${NC} $1 (缺失)"
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${YELLOW}⚠${NC} $1 (缺失)"
    fi
}

echo ""
echo "核心文件:"
check_file "$MACOS_WORKSPACE/AGENTS.md"
check_file "$MACOS_WORKSPACE/SOUL.md"
check_file "$MACOS_WORKSPACE/USER.md"
check_file "$MACOS_WORKSPACE/TOOLS.md"
check_file "$MACOS_WORKSPACE/IDENTITY.md"
check_file "$MACOS_WORKSPACE/HEARTBEAT.md"
check_file "$MACOS_WORKSPACE/MEMORY.md"

echo ""
echo "目录:"
check_dir "$MACOS_WORKSPACE/aios"
check_dir "$MACOS_WORKSPACE/memory"
check_dir "$MACOS_WORKSPACE/aios/agent_system"

echo ""
echo "🔧 修复路径差异"
echo "----------------"

# 修复 Python 路径（Windows → macOS）
if [ -d "$MACOS_WORKSPACE/aios" ]; then
    echo "扫描并修复 Python 路径..."
    
    # 查找所有包含 Windows Python 路径的文件
    find "$MACOS_WORKSPACE/aios" -type f -name "*.py" -o -name "*.sh" | while read file; do
        if grep -q "C:\\\\Program Files\\\\Python312\\\\python.exe" "$file" 2>/dev/null; then
            echo "  修复: $file"
            sed -i '' 's|C:\\Program Files\\Python312\\python.exe|python3.12|g' "$file"
        fi
    done
    
    echo -e "${GREEN}✓ 路径修复完成${NC}"
fi

echo ""
echo "🔐 设置文件权限"
echo "----------------"

# 设置敏感文件权限
chmod 600 "$MACOS_WORKSPACE/MEMORY.md" 2>/dev/null || true
chmod 600 "$MACOS_WORKSPACE/memory"/*.md 2>/dev/null || true
chmod 700 "$MACOS_WORKSPACE/aios/agent_system" 2>/dev/null || true

echo -e "${GREEN}✓ 权限设置完成${NC}"

echo ""
echo "📝 更新 TOOLS.md"
echo "----------------"

# 提示更新 TOOLS.md
if [ -f "$MACOS_WORKSPACE/TOOLS.md" ]; then
    echo -e "${YELLOW}⚠ 请手动更新 TOOLS.md 中的 macOS 特定配置:${NC}"
    echo "  - 应用路径"
    echo "  - SSH 主机"
    echo "  - 设备名称"
    echo ""
    read -p "按回车继续..."
fi

echo ""
echo "================================"
echo "🎉 同步完成！"
echo "================================"
echo ""
echo "下一步:"
echo "1. 检查并更新 TOOLS.md"
echo "2. 安装 Python 依赖:"
echo "   cd $MACOS_WORKSPACE/aios"
echo "   python3.12 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "3. 启动 Memory Server:"
echo "   cd $MACOS_WORKSPACE/aios/agent_system"
echo "   python3.12 memory_server.py"
echo ""
echo "4. 测试系统:"
echo "   python3.12 heartbeat_v5.py"
echo ""
