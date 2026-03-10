#!/bin/bash
# macOS 系统测试脚本 - 太极OS
# 版本: v1.0
# 用途: 快速验证 macOS 部署是否成功

set -e

echo "🧪 太极OS macOS 系统测试"
echo "========================"
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE="$HOME/.openclaw/workspace"
PASSED=0
FAILED=0

# 测试函数
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ============================================
# 1. 系统环境测试
# ============================================

echo "📋 1. 系统环境"
echo "-------------"

# macOS 版本
if [[ "$OSTYPE" == "darwin"* ]]; then
    test_pass "操作系统: macOS"
    sw_vers | sed 's/^/  /'
else
    test_fail "操作系统: 不是 macOS"
fi

# Python 版本
if command -v python3.12 &> /dev/null; then
    test_pass "Python 3.12: $(python3.12 --version)"
else
    test_fail "Python 3.12: 未安装"
fi

# Node.js 版本
if command -v node &> /dev/null; then
    test_pass "Node.js: $(node --version)"
else
    test_fail "Node.js: 未安装"
fi

# OpenClaw
if command -v openclaw &> /dev/null; then
    test_pass "OpenClaw: $(openclaw --version 2>&1 | head -1)"
else
    test_fail "OpenClaw: 未安装"
fi

echo ""

# ============================================
# 2. 工作目录测试
# ============================================

echo "📁 2. 工作目录"
echo "-------------"

if [ -d "$WORKSPACE" ]; then
    test_pass "工作目录存在: $WORKSPACE"
else
    test_fail "工作目录不存在: $WORKSPACE"
fi

# 核心文件
for file in AGENTS.md SOUL.md USER.md TOOLS.md IDENTITY.md HEARTBEAT.md MEMORY.md; do
    if [ -f "$WORKSPACE/$file" ]; then
        test_pass "$file"
    else
        test_warn "$file (缺失)"
    fi
done

# AIOS 目录
if [ -d "$WORKSPACE/aios" ]; then
    test_pass "AIOS 目录存在"
else
    test_fail "AIOS 目录不存在"
fi

# memory 目录
if [ -d "$WORKSPACE/memory" ]; then
    test_pass "memory 目录存在"
else
    test_warn "memory 目录不存在"
fi

echo ""

# ============================================
# 3. Python 依赖测试
# ============================================

echo "🐍 3. Python 依赖"
echo "----------------"

# 激活虚拟环境（如果存在）
if [ -f "$WORKSPACE/aios/venv/bin/activate" ]; then
    source "$WORKSPACE/aios/venv/bin/activate"
    test_pass "虚拟环境已激活"
fi

# 测试核心包
for package in anthropic openai requests yaml jsonlines sentence_transformers lancedb; do
    if python3.12 -c "import $package" 2>/dev/null; then
        test_pass "Python 包: $package"
    else
        test_fail "Python 包: $package (缺失)"
    fi
done

echo ""

# ============================================
# 4. Memory Server 测试
# ============================================

echo "🧠 4. Memory Server"
echo "------------------"

# 检查 Memory Server 是否运行
if curl -s http://localhost:7788/status > /dev/null 2>&1; then
    test_pass "Memory Server 运行中"
    
    # 获取状态
    STATUS=$(curl -s http://localhost:7788/status)
    echo "  状态: $STATUS"
else
    test_warn "Memory Server 未运行"
    echo "  提示: 运行 'python3.12 $WORKSPACE/aios/agent_system/memory_server.py &'"
fi

echo ""

# ============================================
# 5. AIOS 系统测试
# ============================================

echo "🤖 5. AIOS 系统"
echo "--------------"

if [ -f "$WORKSPACE/aios/agent_system/aios.py" ]; then
    test_pass "aios.py 存在"
    
    # 测试 AIOS 状态
    cd "$WORKSPACE/aios/agent_system"
    if python3.12 aios.py status > /dev/null 2>&1; then
        test_pass "AIOS 状态检查通过"
    else
        test_warn "AIOS 状态检查失败"
    fi
else
    test_fail "aios.py 不存在"
fi

echo ""

# ============================================
# 6. Heartbeat 测试
# ============================================

echo "💓 6. Heartbeat"
echo "--------------"

if [ -f "$WORKSPACE/aios/agent_system/heartbeat_v5.py" ]; then
    test_pass "heartbeat_v5.py 存在"
    
    # 测试 Heartbeat（不实际运行，只检查语法）
    cd "$WORKSPACE/aios/agent_system"
    if python3.12 -m py_compile heartbeat_v5.py 2>/dev/null; then
        test_pass "Heartbeat 语法检查通过"
    else
        test_fail "Heartbeat 语法检查失败"
    fi
else
    test_fail "heartbeat_v5.py 不存在"
fi

echo ""

# ============================================
# 7. OpenClaw Gateway 测试
# ============================================

echo "🌐 7. OpenClaw Gateway"
echo "---------------------"

if openclaw gateway status > /dev/null 2>&1; then
    test_pass "Gateway 运行中"
    openclaw gateway status | sed 's/^/  /'
else
    test_warn "Gateway 未运行"
    echo "  提示: 运行 'openclaw gateway start'"
fi

echo ""

# ============================================
# 8. 自启动服务测试
# ============================================

echo "🔄 8. 自启动服务"
echo "---------------"

# Memory Server LaunchAgent
PLIST="$HOME/Library/LaunchAgents/com.taijios.memory-server.plist"
if [ -f "$PLIST" ]; then
    test_pass "Memory Server LaunchAgent 已配置"
    
    if launchctl list | grep -q "com.taijios.memory-server"; then
        test_pass "Memory Server LaunchAgent 已加载"
    else
        test_warn "Memory Server LaunchAgent 未加载"
    fi
else
    test_warn "Memory Server LaunchAgent 未配置"
fi

echo ""

# ============================================
# 9. 文件权限测试
# ============================================

echo "🔐 9. 文件权限"
echo "-------------"

# 检查敏感文件权限
if [ -f "$WORKSPACE/MEMORY.md" ]; then
    PERMS=$(stat -f "%OLp" "$WORKSPACE/MEMORY.md")
    if [ "$PERMS" = "600" ]; then
        test_pass "MEMORY.md 权限正确 (600)"
    else
        test_warn "MEMORY.md 权限: $PERMS (建议 600)"
    fi
fi

echo ""

# ============================================
# 10. 网络测试
# ============================================

echo "🌍 10. 网络连接"
echo "--------------"

# 测试 Anthropic API
if curl -s --max-time 5 https://api.anthropic.com > /dev/null 2>&1; then
    test_pass "Anthropic API 可访问"
else
    test_warn "Anthropic API 无法访问"
fi

# 测试 OpenAI API
if curl -s --max-time 5 https://api.openai.com > /dev/null 2>&1; then
    test_pass "OpenAI API 可访问"
else
    test_warn "OpenAI API 无法访问"
fi

echo ""

# ============================================
# 测试总结
# ============================================

echo "========================"
echo "📊 测试总结"
echo "========================"
echo ""
echo "通过: $PASSED"
echo "失败: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！系统部署成功！${NC}"
    exit 0
elif [ $FAILED -le 3 ]; then
    echo -e "${YELLOW}⚠ 部分测试失败，但系统基本可用${NC}"
    echo "请检查失败项并修复"
    exit 1
else
    echo -e "${RED}❌ 多个测试失败，系统可能无法正常工作${NC}"
    echo "请参考部署文档重新配置"
    exit 2
fi
