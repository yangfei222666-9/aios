# API Testing Skill - Changelog

## v2.0.0 (2026-03-08)

### 本次新增能力

- **真实 HTTP 请求** - 基于 `urllib.request`，零外部依赖
- **超时保护** - 默认 30s，可通过 `--timeout` 自定义
- **错误分类** - 自动识别 timeout / 5xx / network_error
- **性能统计** - 批量请求的 min/max/avg 耗时

### 已验证场景

**正常场景：**
- GET 请求（200 响应）✓
- POST 请求（JSON body）✓
- 自定义 headers ✓
- 性能测试（10 次请求统计）✓

**边界场景：**
- 超时（30s 限制触发）✓
- 5xx 错误（502 Bad Gateway）✓
- 网络错误（DNS 解析失败）✓

**实际输出表现：**
```json
{
  "ok": true,
  "status": 200,
  "elapsed_ms": 52.3,
  "body": "{\"status\":\"healthy\"}"
}

{
  "ok": false,
  "error": "HTTP 502: Bad Gateway",
  "error_type": "http_5xx"
}

{
  "ok": false,
  "error": "timeout after 30s",
  "error_type": "timeout"
}
```

### 已发现并修复的问题

**问题：初版使用 mock 数据，未真实发送 HTTP 请求**
- **现象：** `send_request()` 返回硬编码的 `{"ok": true, "status": 200}`
- **影响：** 无法验证真实 API 行为
- **修复方式：**
  1. 替换为 `urllib.request.urlopen()` 真实请求
  2. 添加超时保护（默认 30s）
  3. 错误分类（timeout / http_5xx / network_error）
- **验证：** 真实 HTTP 请求回归通过（200 / 502 / timeout 均已验证）

### 仍待补完的边界

- **WebSocket 支持** - 当前仅支持 HTTP/HTTPS
- **文件上传** - multipart/form-data 未实现
- **HTTP/2** - 当前仅支持 HTTP/1.1
- **性能基准** - 不同并发数的压测数据

---

## v1.0.0 (2026-02-27)

### 初始版本

- 发送 HTTP 请求（GET/POST/PUT/DELETE）
- 响应验证（状态码、耗时）
- 性能测试（批量请求统计）
- 批量测试（JSON 测试套件）

**已知限制：**
- 使用 mock 数据，未真实发送请求
- 无超时保护
- 错误处理不完整
