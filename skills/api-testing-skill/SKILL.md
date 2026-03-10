---
name: api-testing-skill
description: API 测试 - 发送请求、验证响应、性能测试
version: 2.0.0
author: 小九
tags: [api, testing, http]
category: testing
---

# API Testing Skill

轻量级 HTTP 测试工具，零依赖（纯 Python 标准库）。

> 本轮 v2.0.0 优化已从单元测试通过，推进到真实环境回归验证。真实 HTTP 请求、timeout、5xx 错误处理均已完成关键行为验证。

## 功能

- 发送 HTTP 请求（GET/POST/PUT/DELETE）
- 响应验证（状态码、耗时）
- 性能测试（批量请求统计）
- 批量测试（JSON 测试套件）

## 使用方法

### 1. 发送单个请求

```bash
# GET 请求
python api_test.py send https://api.example.com/users

# POST 请求（JSON body）
python api_test.py send https://api.example.com/users \
  -X POST \
  -H "Authorization: Bearer token123" \
  -d '{"name": "张三", "age": 25}'

# 自定义超时（默认 30s）
python api_test.py send https://slow-api.com --timeout 60
```

### 2. 性能测试

```bash
# 发送 10 次请求，统计耗时
python api_test.py perf https://api.example.com/health --n 10

# 输出示例：
# {
#   "total": 10,
#   "success": 10,
#   "errors": 0,
#   "min_ms": 45.2,
#   "max_ms": 89.1,
#   "avg_ms": 62.3
# }
```

### 3. 批量测试（测试套件）

创建 `tests.json`：
```json
[
  {
    "name": "健康检查",
    "url": "https://api.example.com/health",
    "method": "GET",
    "expect_status": 200
  },
  {
    "name": "创建用户",
    "url": "https://api.example.com/users",
    "method": "POST",
    "headers": {"Authorization": "Bearer token123"},
    "body": {"name": "张三"},
    "expect_status": 201
  }
]
```

运行：
```bash
python api_test.py suite tests.json

# 输出：
# ✅ 健康检查 — 200 (52.3ms)
# ✅ 创建用户 — 201 (89.1ms)
# 结果: 2 通过 / 0 失败
```

## Python API

```python
from api_test import send_request, perf_test

# 发送请求
result = send_request(
    "https://api.example.com/users",
    method="POST",
    headers={"Authorization": "Bearer token"},
    body='{"name": "张三"}',
    timeout=30
)

if result["ok"]:
    print(f"成功: {result['status']} ({result['elapsed_ms']}ms)")
    print(result["body"])
else:
    print(f"失败: {result['error']}")

# 性能测试
stats = perf_test(
    "https://api.example.com/health",
    method="GET",
    n=100,
    headers={},
    body=None,
    timeout=30
)
print(f"平均耗时: {stats['avg_ms']}ms")
```

## 常见场景

### 场景1：API 健康检查
```bash
python api_test.py send https://api.example.com/health
```

### 场景2：压力测试
```bash
python api_test.py perf https://api.example.com/endpoint --n 100
```

### 场景3：回归测试
```bash
python api_test.py suite regression_tests.json
```

## 错误处理

- **网络错误** — 自动捕获并返回 `error` 字段，`error_type: network_error`
- **超时** — 默认 30s，可通过 `--timeout` 调整，`error_type: timeout`
- **5xx 错误** — 自动识别，`error_type: http_5xx`
- **非 JSON 响应** — 自动降级为纯文本

## 限制

- 不支持 WebSocket
- 不支持文件上传（multipart/form-data）
- 不支持 HTTP/2

## 变更日志

详见 [CHANGELOG.md](./CHANGELOG.md)

- v2.0.0 (2026-03-08) - 真实 HTTP 请求；超时保护；错误分类（timeout/5xx/network_error）；真实回归验证通过
- v1.0.0 (2026-02-27) - 初始版本
