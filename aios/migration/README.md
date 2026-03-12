# macOS 最小可运行迁移指南

**目标：** 先跑通 Memory Server，不做自动化。

---

## 第一步：传输文件到 Mac

将整个 `aios` 目录传输到 Mac：

```bash
# 在 Mac 上创建目录
mkdir -p ~/.openclaw/workspace

# 传输方式（选一种）：
# 1. 通过网络共享
# 2. 通过 USB 驱动器
# 3. 通过云同步（OneDrive/iCloud）
# 4. 通过 scp/rsync（如果两台机器在同一网络）
```

---

## 第二步：运行环境探针

```bash
cd ~/.openclaw/workspace/aios/migration
chmod +x mac_probe.sh
./mac_probe.sh
```

**检查输出：**
- ✓ python3 路径和版本
- ✓ 工作目录存在
- ✓ 关键文件完整
- ✓ 端口可用（7788, 8888, 8889）

如果有 ✗ 标记，先解决问题再继续。

---

## 第三步：启动 Memory Server

```bash
cd ~/.openclaw/workspace/aios/migration
chmod +x start_memory.sh
./start_memory.sh
```

**预期输出：**
```
==========================================
Memory Server 启动
==========================================

✓ 工作目录: /Users/你的用户名/.openclaw/workspace/aios/agent_system
✓ 虚拟环境已存在
✓ 环境变量已设置
✓ memory_server.py 存在

→ 启动 Memory Server (端口 7788)...
  按 Ctrl+C 停止

Memory Server started on http://127.0.0.1:7788
```

---

## 第四步：验证 Memory Server

**在另一个终端：**

```bash
# 检查端口
lsof -i :7788

# 测试接口
curl http://127.0.0.1:7788/status
```

**预期响应：**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime": "..."
}
```

---

## 第五步：配置环境变量（可选）

如果需要在所有终端中使用环境变量：

```bash
# 将环境变量添加到 .zshrc
echo 'source ~/.openclaw/workspace/aios/migration/env.sh' >> ~/.zshrc

# 重新加载配置
source ~/.zshrc

# 验证
echo $AIOS_ROOT
```

---

## 常见问题

### 1. python3 未找到

```bash
# 安装 Python 3（通过 Homebrew）
brew install python@3.12
```

### 2. 端口被占用

```bash
# 查看占用端口的进程
lsof -i :7788

# 杀死进程（替换 PID）
kill -9 <PID>
```

### 3. 依赖安装失败

```bash
# 手动安装核心依赖
cd ~/.openclaw/workspace/aios/agent_system
source .venv/bin/activate
pip install torch sentence-transformers lancedb fastapi uvicorn
```

### 4. 虚拟环境激活失败

```bash
# 删除旧虚拟环境
rm -rf ~/.openclaw/workspace/aios/agent_system/.venv

# 重新运行启动脚本
./start_memory.sh
```

---

## 下一步（Memory Server 跑通后）

1. **启动 Dashboard**
   - 先手动运行 `python server.py`
   - 验证 http://127.0.0.1:8888

2. **启动 Heartbeat**
   - 先手动运行 `python heartbeat_v5.py`
   - 验证任务队列处理

3. **平台适配**
   - 修改硬编码路径（`pathlib.Path`）
   - 修改 Python 解释器路径（`sys.executable`）

4. **自动启动（最后）**
   - 配置 launchd
   - 添加日志路径
   - 测试开机自启

---

**核心原则：** 先手动跑通，再自动化。

**最后更新：** 2026-03-12  
**维护者：** 小九 + 珊瑚海
