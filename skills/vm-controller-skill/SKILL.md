---
name: vm-controller-skill
description: VM 控制器 - 创建/启动/停止/删除 VM、监控 VM 状态、执行命令（基于 Docker）
version: 1.0.0
author: 小九
tags: [vm, controller, virtualization, docker, container]
category: infrastructure
---

# VM Controller Skill v1.0

基于 Docker 的轻量 VM 控制器。用 Docker 容器模拟 VM，支持创建/启动/停止/删除/状态查询/命令执行。

## 功能

- ✅ **创建 VM** - 支持多种镜像（Ubuntu/Alpine/Python/Node）
- ✅ **启动/停止 VM** - 完整生命周期管理
- ✅ **删除 VM** - 支持强制删除
- ✅ **状态查询** - 实时查看 VM 状态和资源使用
- ✅ **命令执行** - 在 VM 中执行命令
- ✅ **交互式 Shell** - 进入 VM 终端
- ✅ **日志查看** - 查看 VM 输出日志
- ✅ **资源监控** - CPU/内存/网络使用统计

## 前置条件

**必须先安装 Docker Desktop：**

1. 下载：https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
2. 安装时勾选 "Use WSL 2 instead of Hyper-V"
3. 安装完重启一次
4. 启动 Docker Desktop

## 使用方法

### 1. 检查 Docker 状态

```bash
python vm_controller.py check
```

### 2. 创建 VM

```bash
# 创建默认 Ubuntu VM（1核 512MB）
python vm_controller.py create myvm

# 创建 Alpine VM（轻量级）
python vm_controller.py create alpine-vm --image alpine --memory 256m

# 创建 Python 开发环境
python vm_controller.py create pydev --image python --cpu 2 --memory 1g

# 创建带端口映射的 VM（本地8080 → 容器80）
python vm_controller.py create webvm --image ubuntu --ports 8080:80,443:443
```

**支持的镜像：**
- `ubuntu` / `ubuntu22` → Ubuntu 22.04
- `ubuntu20` → Ubuntu 20.04
- `debian` → Debian Bookworm
- `alpine` → Alpine Linux（最轻量）
- `python` → Python 3.12
- `node` → Node.js 20
- 或任何 Docker Hub 镜像名（如 `nginx:latest`）

### 3. 查看 VM 状态

```bash
# 查看所有 VM
python vm_controller.py status

# 查看单个 VM
python vm_controller.py status myvm
```

**输出示例：**
```
VM名称               状态            镜像                      CPU    内存     创建时间
------------------------------------------------------------------------------------------
🟢 myvm              Up 2 minutes    ubuntu:22.04              1      512m     2026-02-27 01:45
🔴 alpine-vm         Exited          alpine:latest             1      256m     2026-02-27 01:40
```

### 4. 启动/停止 VM

```bash
# 启动
python vm_controller.py start myvm

# 停止
python vm_controller.py stop myvm
```

### 5. 在 VM 中执行命令

```bash
# 执行单条命令
python vm_controller.py exec myvm "ls -la"
python vm_controller.py exec myvm "apt update && apt install -y curl"

# 进入交互式 Shell
python vm_controller.py shell myvm
```

### 6. 查看日志

```bash
# 查看最近 50 行日志
python vm_controller.py logs myvm

# 查看最近 100 行
python vm_controller.py logs myvm --lines 100
```

### 7. 资源监控

```bash
# 查看所有 VM 的 CPU/内存/网络使用
python vm_controller.py stats
```

### 8. 删除 VM

```bash
# 删除（需要确认）
python vm_controller.py delete myvm

# 强制删除（不确认）
python vm_controller.py delete myvm -f
```

## 集成到 AIOS

### 方式1：直接调用（推荐）

```python
import subprocess

def aios_create_vm(name: str, image: str = "ubuntu"):
    """AIOS 创建 VM"""
    result = subprocess.run(
        ["python", "vm_controller.py", "create", name, "--image", image],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def aios_vm_status():
    """AIOS 查看 VM 状态"""
    result = subprocess.run(
        ["python", "vm_controller.py", "status"],
        capture_output=True,
        text=True
    )
    return result.stdout
```

### 方式2：导入模块

```python
import sys
sys.path.append("C:/Users/A/.openclaw/workspace/skills/vm-controller-skill")
from vm_controller import vm_create, vm_start, vm_stop, vm_status

# 创建 VM
vm_create("test-vm", image="alpine", cpu="1", memory="256m")

# 查看状态
vm_status()

# 启动
vm_start("test-vm")
```

### 方式3：AIOS Agent 集成

在 `aios/agents/` 中创建 `vm_manager_agent.py`：

```python
from skills.vm_controller_skill.vm_controller import (
    vm_create, vm_start, vm_stop, vm_delete, vm_status, vm_exec
)

class VMManagerAgent:
    def __init__(self):
        self.name = "VM_Manager"
    
    def handle_task(self, task: dict):
        action = task.get("action")
        vm_name = task.get("vm_name")
        
        if action == "create":
            return vm_create(vm_name, task.get("image", "ubuntu"))
        elif action == "start":
            return vm_start(vm_name)
        elif action == "stop":
            return vm_stop(vm_name)
        elif action == "status":
            return vm_status(vm_name)
        elif action == "exec":
            return vm_exec(vm_name, task.get("command"))
```

## 数据存储

VM 注册表保存在：`vm_registry.json`

```json
{
  "myvm": {
    "id": "a1b2c3d4e5f6",
    "image": "ubuntu:22.04",
    "cpu": "1",
    "memory": "512m",
    "ports": null,
    "created_at": "2026-02-27T01:45:00",
    "status": "running"
  }
}
```

## 触发词

- "创建 VM"
- "启动 VM"
- "停止 VM"
- "VM 状态"
- "进入 VM"
- "删除 VM"

## 技术细节

### 为什么用 Docker 而不是真实 VM？

1. **轻量** - 容器启动秒级，VM 启动分钟级
2. **资源高效** - 容器共享内核，VM 需要完整 OS
3. **易管理** - Docker CLI 简单直观
4. **跨平台** - Windows/Mac/Linux 统一体验
5. **生态丰富** - Docker Hub 有海量镜像

### 容器 vs VM 对比

| 特性 | Docker 容器 | 传统 VM |
|------|------------|---------|
| 启动速度 | 秒级 | 分钟级 |
| 资源占用 | 低（共享内核） | 高（完整 OS） |
| 隔离性 | 进程级 | 硬件级 |
| 适用场景 | 开发/测试/微服务 | 生产/安全隔离 |

### 限制

- **不支持 GUI** - 纯命令行环境（可通过 VNC 扩展）
- **共享内核** - 不能运行不同 OS（如 Windows 容器在 Linux 上）
- **权限限制** - 默认非特权模式

## 下一步（v2.0 计划）

- [ ] VNC 支持（图形界面）
- [ ] 快照/恢复
- [ ] 网络隔离（自定义网络）
- [ ] 卷挂载（持久化数据）
- [ ] 批量操作（一次创建多个 VM）
- [ ] Web Dashboard（可视化管理）

## 故障排查

### Docker 未启动

```
❌ Docker 不可用: Cannot connect to the Docker daemon
```

**解决：** 启动 Docker Desktop

### 镜像拉取失败

```
❌ 拉取镜像失败: timeout
```

**解决：** 检查网络，或使用国内镜像源

### 端口冲突

```
❌ 创建失败: port is already allocated
```

**解决：** 更换端口或停止占用端口的程序

## 许可证

MIT License

---

**版本：** v1.0.0  
**作者：** 小九  
**最后更新：** 2026-02-27
