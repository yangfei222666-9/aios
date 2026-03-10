# Docker Skill - Changelog

## v2.0.0 (2026-03-08)

### 本次新增能力

- **Docker CLI 调用** - 统一 `run_cmd()` 封装，支持超时与错误返回
- **资源监控** - `docker stats` 支持（CPU/内存）
- **日志跟踪** - `docker logs -f` 支持
- **错误可见性** - daemon 不可用时的错误提示更清晰

### 已验证场景

**正常场景：**
- `docker ps` / `docker images` 在无 daemon 环境下触发错误 ✓
- `docker stats` 在无 daemon 环境下返回明确错误 ✓

**边界场景：**
- Docker 未安装（提示缺少 docker CLI）✓
- Docker daemon 不可用（错误可见性验证）✓

**实际输出表现（daemon 不可用）：**
```
[ERROR] Docker daemon not available. Is the docker daemon running?
```

### 已发现并修复的问题

**问题：daemon 不可用时错误信息不清晰**
- **现象：** 返回为空或抛异常
- **影响：** 用户无法判断是 docker 未安装还是 daemon 未启动
- **修复方式：**
  1. 捕获 stderr 并标准化错误提示
  2. 区分 docker CLI 不存在 vs daemon 不可用
- **验证：** 无 daemon 环境回归通过

### 仍待补完的边界

- **daemon 可用环境下的资源场景**（build/run/stats/logs）尚未验证
- **Windows Docker Desktop / WSL2** 兼容性未验证
- **性能基准**（大镜像构建 / 大容器日志）待补测

---

## v1.0.0 (2026-02-27)

### 初始版本

- 容器/镜像管理
- 构建镜像、运行容器
- 日志查看
- 资源监控

**已知限制：**
- 无 daemon 环境下错误不可见
- 未验证资源场景
