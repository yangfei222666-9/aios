# 快速验证 - 太极OS 最小运行链

> 验证系统核心链路是否正常工作。不是产品 demo，是真链验真。

## 前置条件

- Python 3.12+
- Windows 11（当前唯一验证过的环境）

## 步骤 1：安装核心依赖

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
pip install requests flask flask-cors
```

## 步骤 2：验证 Task Queue

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" -c "
from task_queue import TaskQueue
q = TaskQueue()
tid = q.enqueue_task({'type': 'test', 'description': 'hello aios', 'priority': 1})
print(f'入队成功: {tid}')
pending = q.list_tasks_by_status('pending')
print(f'待处理: {len(pending)} 个')
"
```

预期输出：入队成功 + 1 个待处理任务。

## 步骤 3：验证 Health Monitor

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 agents/health_monitor.py
```

预期输出：Agent 健康状态报告，告警写入 `data/alerts.jsonl`。

## 步骤 4：验证 Memory Server（可选）

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" memory_server.py
```

另开终端验证：

```powershell
Invoke-RestMethod http://127.0.0.1:7788/status
```

预期输出：`{"status": "ok", "model": "all-MiniLM-L6-v2", "port": 7788}`

## 步骤 5：验证告警推送链

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 agents/notification_manager.py
```

预期：读取 `data/alerts.jsonl` 中未发送的告警，通过 Telegram 推送。

## 验证清单

| 链路 | 命令 | 预期 | 状态 |
|------|------|------|------|
| Task Queue 入队 | 步骤 2 | 任务 ID 返回 | ✅ 已验证 |
| Health Monitor | 步骤 3 | 告警写入 alerts.jsonl | ✅ 已验证 |
| Memory Server | 步骤 4 | /status 返回 200 | ✅ 已验证 |
| 告警推送 | 步骤 5 | Telegram 收到消息 | ✅ 已验证 |
| Task → Agent 执行 | — | 任务被消费并回写结果 | ❌ 未验证 |
| Learning Loop | — | 失败转成规则 | ❌ 未验证 |
| Scheduler 自动调度 | — | 定时触发任务分配 | ❌ 未验证 |

## 常见问题

**Q: 编码报错？**  
A: 所有 Python 命令加 `$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'` 和 `-X utf8`。

**Q: Memory Server 启动卡住？**  
A: 首次加载 embedding 模型需要 ~9 秒，之后热加载 <100ms。如果超过 30 秒，检查磁盘空间。

**Q: alerts.jsonl 在哪？**  
A: `data/alerts.jsonl`（通过 `paths.py` 定义）。根目录的 `alerts.jsonl` 是旧文件，已迁移。

---

**最后更新：** 2026-03-13
