# task_executions.jsonl 标准格式规范

## 字段定义（11个字段）

### 核心字段（8个，每条必有）

1. **task_id** (string) - 任务唯一标识
2. **agent_id** (string) - 执行 Agent 标识
3. **status** (string) - 执行状态：`"completed"` | `"failed"` | `"timeout"`
4. **start_time** (string) - 开始时间（ISO 8601 格式，UTC）
5. **end_time** (string) - 结束时间（ISO 8601 格式，UTC）
6. **duration_ms** (int) - 执行耗时（毫秒）
7. **retry_count** (int) - 重试次数（0 = 首次执行）
8. **side_effects** (object) - 副作用记录
   - `files_written` (array) - 写入的文件路径列表
   - `tasks_created` (array) - 创建的子任务 ID 列表
   - `api_calls` (int) - API 调用次数

### 条件字段（3个，按需出现）

9. **error** (string) - 错误信息（仅 `status="failed"` 时出现）
10. **result** (object) - 执行结果（仅 `status="completed"` 时出现）
    - `output` (string) - 输出摘要（最多 500 字符）
    - `task_type` (string) - 任务类型
11. **metadata** (object) - 可选元数据（扩展字段）

## 示例

### 成功执行

```json
{
  "task_id": "task-20260307-112955",
  "agent_id": "coder",
  "status": "completed",
  "start_time": "2026-03-07T03:30:19.028869+00:00",
  "end_time": "2026-03-07T03:30:19.028869+00:00",
  "duration_ms": 4319,
  "retry_count": 0,
  "side_effects": {
    "files_written": ["test_runs/output.py"],
    "tasks_created": ["task-xxx"],
    "api_calls": 2
  },
  "result": {
    "output": "Code generated successfully",
    "task_type": "code"
  }
}
```

### 失败执行

```json
{
  "task_id": "task-20260307-113000",
  "agent_id": "analyst",
  "status": "failed",
  "start_time": "2026-03-07T03:30:00.000000+00:00",
  "end_time": "2026-03-07T03:30:05.000000+00:00",
  "duration_ms": 5000,
  "retry_count": 1,
  "side_effects": {
    "files_written": [],
    "tasks_created": [],
    "api_calls": 1
  },
  "error": "API timeout after 5000ms"
}
```

## 设计原则

1. **条件字段** - `error` 只在 `failed` 时出现，`result` 只在 `completed` 时出现，保持 JSONL 行尽量短
2. **自动采集** - `side_effects` 应该自动收集，不依赖手动填写（当前标记 `TODO: auto-collect`）
3. **时间格式** - 统一使用 ISO 8601 格式（UTC），便于跨时区分析
4. **字段稳定** - 核心 8 字段不可删减，扩展字段放在 `metadata` 里

## 迁移工具

旧格式迁移到新格式：

```bash
python migrate_task_executions.py                # 迁移并备份
python migrate_task_executions.py --dry-run      # 预览不写入
python migrate_task_executions.py --no-backup    # 不备份旧文件
```

## TODO

- [ ] 自动采集 `side_effects`（hook 文件写入和任务创建）
- [ ] 记录真实 `start_time`（当前简化为 `end_time`）
- [ ] 支持 `timeout` 状态（当前只有 `completed` 和 `failed`）
- [ ] 扩展 `metadata` 字段（模型名称、token 消耗等）

---

**版本：** v1.0  
**最后更新：** 2026-03-07  
**维护者：** 小九 + 珊瑚海
