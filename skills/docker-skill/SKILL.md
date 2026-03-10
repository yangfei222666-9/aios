---
name: docker-skill
description: Docker 操作 - 构建、运行、管理容器
version: 2.0.0
author: 小九
tags: [docker, container, devops]
category: infrastructure
---

# Docker Skill

轻量级 Docker 管理工具，零依赖（纯 Python 标准库 + docker CLI）。

> 本轮 v2.0.0 优化已推进到真实环境回归验证。daemon 不可用时的错误可见性已验证；daemon 可用环境下的资源场景待补测。

## 功能

- 列出容器/镜像
- 构建镜像
- 运行容器（支持端口映射、环境变量）
- 停止/删除容器
- 查看日志（支持实时跟踪）
- 资源监控（CPU/内存）

## 前置条件

需要安装 Docker：
- Windows: Docker Desktop
- Linux: `sudo apt install docker.io`
- macOS: Docker Desktop

## 使用方法

### 1. 列出容器

```bash
# 运行中的容器
python docker_tool.py ps

# 所有容器（包含已停止）
python docker_tool.py ps -a
```

### 2. 列出镜像

```bash
python docker_tool.py images
```

### 3. 构建镜像

```bash
# 从当前目录构建
python docker_tool.py build . -t myapp:latest

# 自定义超时（默认 300s）
python docker_tool.py build . -t myapp:latest --timeout 600
```

### 4. 运行容器

```bash
# 简单运行
python docker_tool.py run nginx:latest

# 后台运行 + 端口映射 + 环境变量
python docker_tool.py run nginx:latest \
  --name my-nginx \
  -d \
  -p 8080:80 \
  -e ENV=production

# 传递启动参数
python docker_tool.py run ubuntu:latest bash -c "echo hello"
```

### 5. 停止容器

```bash
python docker_tool.py stop my-nginx
```

### 6. 删除容器

```bash
# 普通删除（需先停止）
python docker_tool.py rm my-nginx

# 强制删除（运行中也删）
python docker_tool.py rm my-nginx -f
```

### 7. 查看日志

```bash
# 最后 100 行
python docker_tool.py logs my-nginx

# 最后 50 行
python docker_tool.py logs my-nginx --tail 50

# 实时跟踪（Ctrl+C 退出）
python docker_tool.py logs my-nginx -f
```

### 8. 资源监控

```bash
# 所有容器
python docker_tool.py stats

# 指定容器
python docker_tool.py stats my-nginx
```

## Python API

```python
from docker_tool import run_cmd

# 列出容器
result = run_cmd(["docker", "ps", "-a"])
if result["ok"]:
    print(result["stdout"])

# 构建镜像
result = run_cmd(["docker", "build", "-t", "myapp", "."], timeout=300)
if result["ok"]:
    print("✅ 构建成功")
else:
    print(f"❌ {result['stderr']}")
```

## 常见场景

### 场景1：快速启动 Web 服务
```bash
python docker_tool.py run nginx:latest --name web -d -p 8080:80
```

### 场景2：调试容器日志
```bash
python docker_tool.py logs web --tail 50
```

### 场景3：清理停止的容器
```bash
python docker_tool.py ps -a  # 查看所有容器
python docker_tool.py rm old-container -f
```

### 场景4：监控资源使用
```bash
python docker_tool.py stats
```

## 错误处理

- **Docker 未安装** — 自动检测并提示 `docker: command not found`
- **Docker daemon 不可用** — 明确提示 `Docker daemon not available. Is the docker daemon running?`
- **超时** — 构建默认 300s，可通过 `--timeout` 调整
- **权限不足** — Linux 需要 `sudo` 或加入 `docker` 组

## 限制

- 不支持 Docker Compose
- 不支持 Swarm/Kubernetes
- 不支持镜像推送到 Registry
- **daemon 可用环境下的资源场景**（build/run/stats/logs）待 Docker 环境可用后补测

## 变更日志

详见 [CHANGELOG.md](./CHANGELOG.md)

- v2.0.0 (2026-03-08) - daemon 不可用时错误可见性验证通过；资源场景待 Docker 环境可用后补测
- v1.0.0 (2026-02-27) - 初始版本
