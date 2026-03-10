# task-replay-skill 详细规格书

**版本：** v1.0  
**日期：** 2026-03-09  
**状态：** spec_draft  
**风险等级：** 低（纯读取 + 分析，不改主链路）

---

## 1. 定位

task-replay-skill 是太极OS 的**观察与复盘基础设施 Skill**。

它的核心能力是：从已有的执行记录中，还原一个任务从触发到结束的完整生命周期，输出结构化的复盘报告。

**一句话定义：**
> 把散落在多个文件里的任务痕迹，拼成一条完整的时间线，让你看清"到底发生了什么"。

---

## 2. 解决什么问题

当前太极OS 的任务执行数据分散在多个文件中：

| 文件 | 内容 |
|------|------|
| `task_queue.jsonl` | 任务提交记录 |
| `task_executions.jsonl` | 执行结果（成功/失败/输出） |
| `spawn_pending.jsonl` | spawn 请求 |
| `agents.json` | Agent 状态和统计 |
| `lessons.json` | 失败经验 |
| `heartbeat.log` | 心跳触发日志 |
| `lifecycle_check.log` | 生命周期检查 |
| `memory_retrieval_log.jsonl` | 记忆检索记录 |

**问题：**
- 想知道某个任务为什么失败，需要手动翻 3-5 个文件
- 没有统一的时间线视图
- 无法快速判断"是触发问题、执行问题、还是回写问题"
- lessons.json 里的经验缺少完整上下文

**task-replay-skill 解决的就是这个拼图问题。**

---

## 3. 核心能力

### 3.1 任务回放（replay）

输入一个 task_id，输出该任务的完整时间线：

```
[T+0s]    SUBMITTED  → task_queue.jsonl (type=code, priority=high)
[T+12s]   PICKED_UP  → heartbeat_v5.py 检测到
[T+13s]   SPAWNED    → spawn_pending.jsonl (agent=coder-dispatcher)
[T+14s]   EXECUTING  → sessions_spawn 调用
[T+29s]   COMPLETED  → task_executions.jsonl (success=true, duration=15.5s)
[T+29s]   WRITEBACK  → 结果写入 spawn_results.jsonl
```

或者失败场景：

```
[T+0s]    SUBMITTED  → task_queue.jsonl (type=research, priority=normal)
[T+30s]   PICKED_UP  → heartbeat_v5.py 检测到
[T+31s]   SPAWNED    → spawn_pending.jsonl (agent=researcher)
[T+31s]   EXECUTING  → sessions_spawn 调用
[T+91s]   FAILED     → task_executions.jsonl (error=api_error, 502 Bad Gateway)
[T+91s]   RETRY_1    → 重试第 1 次
[T+151s]  FAILED     → 重试失败
[T+151s]  RETRY_2    → 重试第 2 次
[T+211s]  FAILED     → 重试失败
[T+211s]  RETRY_3    → 重试第 3 次
[T+271s]  ABANDONED  → 达到最大重试次数
[T+272s]  LESSON     → lessons.json (lesson_id=lesson-ab637d2b, error_type=api_error)
```

### 3.2 批量摘要（summary）

输入时间范围，输出该时段所有任务的执行摘要：

```
=== 2026-03-07 任务执行摘要 ===

总计：12 个任务
成功：9 (75%)
失败：3 (25%)

按类型：
  code:     5 成功 / 1 失败
  analysis: 3 成功 / 0 失败
  learning: 1 成功 / 2 失败

失败归因：
  api_error (502):  2 次 → 建议：检查 API 端点可用性
  timeout:          1 次 → 建议：增加超时或拆分任务

平均执行时长：22.3s
最慢任务：task-xxx (48.1s, type=learning)
```

### 3.3 失败归因（diagnose）

输入一个失败的 task_id，输出结构化的归因分析：

```
=== 失败归因：task-xxx ===

断点位置：EXECUTING → FAILED
错误类型：api_error
错误详情：502 Bad Gateway (chat.apiport.cc.cd)
重试次数：3/3（全部失败）

根因判断：外部 API 不可用（非任务本身问题）

相似历史：
  - lesson-ab637d2b (2026-03-03): 同一 API 端点 502
  - task-yyy (2026-03-05): 同类错误，后自动恢复

建议：
  1. 检查 API 端点状态
  2. 如果是间歇性问题，等待后重试
  3. 如果是持续性问题，切换备用端点
```

---

## 4. 技术设计

### 4.1 数据源

Skill 只读取，不写入任何数据源：

```python
DATA_SOURCES = {
    "task_queue":       "aios/agent_system/task_queue.jsonl",
    "task_executions":  "aios/agent_system/task_executions.jsonl",
    "spawn_pending":    "aios/agent_system/spawn_pending.jsonl",
    "agents":           "aios/agent_system/agents.json",
    "lessons":          "aios/agent_system/lessons.json",
    "heartbeat_log":    "aios/agent_system/heartbeat.log",
    "lifecycle_log":    "aios/agent_system/lifecycle_check.log",
}
```

### 4.2 核心模块

```
task-replay-skill/
├── SKILL.md              # Skill 描述和使用说明
├── task_replay.py        # 主入口
├── timeline_builder.py   # 时间线构建器
├── summary_generator.py  # 批量摘要生成器
├── failure_diagnoser.py  # 失败归因分析器
└── data_loader.py        # 统一数据加载层
```

### 4.3 关键接口

```python
# task_replay.py - 主入口

def replay(task_id: str) -> dict:
    """回放单个任务的完整生命周期"""
    # 返回：
    # {
    #   "task_id": "...",
    #   "timeline": [
    #     {"timestamp": ..., "phase": "SUBMITTED", "source": "task_queue.jsonl", "detail": "..."},
    #     {"timestamp": ..., "phase": "PICKED_UP", "source": "heartbeat.log", "detail": "..."},
    #     ...
    #   ],
    #   "duration_total": 29.0,
    #   "final_status": "completed",
    #   "token_usage": {"input": 3669, "output": 828}
    # }

def summary(start_time: str, end_time: str = None) -> dict:
    """生成时间范围内的任务执行摘要"""
    # start_time/end_time: ISO 格式或 "today" / "yesterday" / "this_week"
    # 返回：
    # {
    #   "period": "2026-03-07",
    #   "total": 12,
    #   "success": 9,
    #   "failed": 3,
    #   "by_type": {...},
    #   "failure_reasons": [...],
    #   "avg_duration": 22.3,
    #   "slowest_task": {...}
    # }

def diagnose(task_id: str) -> dict:
    """对失败任务进行归因分析"""
    # 返回：
    # {
    #   "task_id": "...",
    #   "break_point": "EXECUTING → FAILED",
    #   "error_type": "api_error",
    #   "error_detail": "502 Bad Gateway",
    #   "retry_count": 3,
    #   "root_cause": "外部 API 不可用",
    #   "similar_history": [...],
    #   "suggestions": [...]
    # }
```

### 4.4 timeline_builder.py 核心逻辑

```python
class TimelineBuilder:
    """从多个数据源拼接任务时间线"""

    def build(self, task_id: str) -> list:
        events = []

        # 1. 从 task_queue 找提交记录
        submit_event = self._find_in_queue(task_id)
        if submit_event:
            events.append({
                "timestamp": submit_event["timestamp"],
                "phase": "SUBMITTED",
                "source": "task_queue.jsonl",
                "detail": f"type={submit_event['type']}, priority={submit_event['priority']}"
            })

        # 2. 从 task_executions 找执行记录
        exec_event = self._find_in_executions(task_id)
        if exec_event:
            events.append({
                "timestamp": exec_event["timestamp"],
                "phase": "COMPLETED" if exec_event["status"] == "completed" else "FAILED",
                "source": "task_executions.jsonl",
                "detail": self._format_exec_detail(exec_event)
            })

            # 如果有重试记录
            if exec_event.get("retry_count", 0) > 0:
                for i in range(exec_event["retry_count"]):
                    events.append({
                        "timestamp": exec_event["timestamp"] - (exec_event["retry_count"] - i) * 60,
                        "phase": f"RETRY_{i+1}",
                        "source": "task_executions.jsonl",
                        "detail": f"重试第 {i+1} 次"
                    })

        # 3. 从 lessons 找经验记录
        lesson = self._find_in_lessons(task_id)
        if lesson:
            events.append({
                "timestamp": lesson.get("harvested_at_ts", 0),
                "phase": "LESSON",
                "source": "lessons.json",
                "detail": f"lesson_id={lesson['lesson_id']}, error_type={lesson['error_type']}"
            })

        # 按时间排序
        events.sort(key=lambda e: e["timestamp"])
        return events
```

### 4.5 failure_diagnoser.py 核心逻辑

```python
class FailureDiagnoser:
    """失败归因分析"""

    # 已知错误模式 → 根因映射
    ERROR_PATTERNS = {
        "502": {"root_cause": "外部 API 不可用", "category": "external"},
        "timeout": {"root_cause": "执行超时", "category": "resource"},
        "rate_limit": {"root_cause": "API 限流", "category": "external"},
        "model_error": {"root_cause": "模型调用失败", "category": "model"},
        "parse_error": {"root_cause": "输出解析失败", "category": "internal"},
    }

    def diagnose(self, task_id: str) -> dict:
        # 1. 获取时间线
        timeline = self.timeline_builder.build(task_id)

        # 2. 找到断点
        break_point = self._find_break_point(timeline)

        # 3. 匹配错误模式
        exec_record = self.data_loader.find_execution(task_id)
        error_info = self._match_error_pattern(exec_record)

        # 4. 搜索相似历史
        similar = self._find_similar_failures(error_info)

        # 5. 生成建议
        suggestions = self._generate_suggestions(error_info, similar)

        return {
            "task_id": task_id,
            "break_point": break_point,
            "error_type": error_info["error_type"],
            "error_detail": error_info["detail"],
            "root_cause": error_info["root_cause"],
            "similar_history": similar,
            "suggestions": suggestions,
        }
```

---

## 5. 使用方式

### CLI 调用

```bash
# 回放单个任务
python task_replay.py replay --task-id learning-GitHub_Researcher-20260307211107

# 今日摘要
python task_replay.py summary --period today

# 昨日摘要
python task_replay.py summary --period yesterday

# 指定时间范围
python task_replay.py summary --start 2026-03-07 --end 2026-03-08

# 失败归因
python task_replay.py diagnose --task-id learning-GitHub_Issue_Tracker-20260307211443
```

### 在心跳中调用（可选，未来集成）

```python
# 在 heartbeat 中，如果有失败任务，自动调用 diagnose
failed_tasks = get_recent_failures(hours=24)
for task in failed_tasks:
    report = diagnose(task["task_id"])
    if report["category"] == "internal":
        # 内部问题，记录到 lessons
        append_lesson(report)
```

---

## 6. 输出格式

### 6.1 人类可读格式（默认）

```
═══════════════════════════════════════════
  任务回放：learning-GitHub_Researcher-20260307211107
═══════════════════════════════════════════

[2026-03-07 21:11:07]  SUBMITTED
  来源: task_queue.jsonl
  类型: learning | 优先级: normal
  描述: 搜索 GitHub 最新 AIOS/Agent 项目

[2026-03-07 21:11:19]  PICKED_UP  (+12s)
  来源: heartbeat_v5.py

[2026-03-07 21:11:20]  SPAWNED    (+13s)
  来源: spawn_pending.jsonl
  Agent: coder-dispatcher

[2026-03-07 21:11:35]  COMPLETED  (+28s)
  来源: task_executions.jsonl
  耗时: 15.5s
  Token: 3669 in / 828 out
  状态: ✅ 成功

───────────────────────────────────────────
  总耗时: 28s | 状态: completed
═══════════════════════════════════════════
```

### 6.2 JSON 格式（--format json）

供其他模块消费，结构见 4.3 节接口定义。

---

## 7. 与太极OS 现有模块的关系

```
                    ┌─────────────────┐
                    │  task-replay    │  ← 纯读取
                    │  skill          │
                    └────────┬────────┘
                             │ 读取
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
  task_queue.jsonl    task_executions.jsonl   lessons.json
        ▲                    ▲                    ▲
        │                    │                    │
  heartbeat_v5.py      task_executor.py     experience_harvester
  (写入)               (写入)               (写入)
```

**关键约束：task-replay-skill 只读不写，不改任何现有模块的行为。**

### 服务对象

| 消费者 | 用途 |
|--------|------|
| Reality Ledger | 提供完整时间线数据 |
| skill_candidate_detector | 从失败模式中发现候选 |
| lessons.json | 为经验记录补充完整上下文 |
| heartbeat_alert_deduper | 判断告警是否属于已知模式 |
| 珊瑚海（人工复盘） | 快速了解"发生了什么" |

---

## 8. 边界与约束

### 做什么
- ✅ 读取现有 jsonl/json/log 文件
- ✅ 拼接时间线
- ✅ 生成摘要和归因报告
- ✅ 输出人类可读和 JSON 两种格式

### 不做什么
- ❌ 不写入任何数据文件
- ❌ 不修改任何现有模块
- ❌ 不触发任何 Agent 执行
- ❌ 不做实时监控（那是 monitor 的事）
- ❌ 不做自动修复（那是 self-improving 的事）

### 性能约束
- 单次 replay 应在 2s 内完成
- summary 扫描 1000 条记录应在 5s 内完成
- 不缓存数据（每次从文件读取，保证一致性）

---

## 9. 实施计划

### Phase 1：最小可用（1-2 天）
1. `data_loader.py` - 统一数据加载
2. `timeline_builder.py` - 时间线构建
3. `task_replay.py` - replay 命令
4. 基本的人类可读输出

### Phase 2：摘要与归因（1 天）
5. `summary_generator.py` - 批量摘要
6. `failure_diagnoser.py` - 失败归因
7. JSON 输出格式

### Phase 3：打磨（0.5 天）
8. 错误处理（文件不存在、格式异常）
9. SKILL.md 编写
10. 简单测试

**总计预估：2.5-3.5 天**

---

## 10. 验收标准

1. 输入一个真实的 task_id，能输出完整时间线
2. 输入 "today"，能输出今日摘要
3. 输入一个失败的 task_id，能输出归因报告
4. 所有操作纯读取，不产生任何副作用
5. 在现有数据上运行无报错

---

## 11. 未来扩展点（不在 v1.0 范围内）

- 与 Dashboard 集成，提供可视化时间线
- 自动在心跳中调用，生成每日复盘
- 与 error-pattern-detector 联动，自动发现重复失败模式
- 支持对比两个任务的执行差异（diff 模式）
- 支持从 sessions_history 拉取 spawn 子会话的详细对话

---

**规格书状态：** draft → 待珊瑚海审阅