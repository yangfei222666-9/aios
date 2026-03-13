# Task Router - 智能任务路由系统

## 概述

Task Router 是 AIOS 的核心路由引擎，负责将用户任务智能分发给最合适的 Agent。它通过关键词匹配、模糊匹配和候选排名算法，实现高效的任务路由。

## 架构

```
用户任务描述
    ↓
[1] 任务类型识别 (Task Type Identification)
    - 中文关键词匹配
    - 英文关键词匹配
    - 默认降级到 "code"
    ↓
[2] Agent 匹配 (Agent Matching)
    - 精确匹配 task_types
    - 过滤 standby Agent
    ↓
[3] 模糊匹配 (Fuzzy Matching) [如果无精确匹配]
    - Jaccard 相似度计算
    - role + name 词汇匹配
    ↓
[4] 候选排名 (Candidate Ranking)
    - 基础分数
    - 优先级加分 (critical/high/normal/low)
    - 成功率加分 (success_rate)
    - 任务经验加分 (tasks_completed)
    ↓
[5] 路由结果 (RouteResult)
    - agent_id: 最佳 Agent ID
    - confidence: 置信度 (0.0 ~ 1.0)
    - reason: 路由原因
    - alternatives: 备选 Agent 列表
```

## 核心功能

### 1. 任务类型识别

支持的任务类型：
- `code` - 编写代码
- `debug` - 调试/修复 bug
- `refactor` - 重构代码
- `test` - 编写测试
- `analysis` - 数据分析/报告
- `monitor` - 系统监控
- `health-check` - 健康检查
- `research` - 研究/调研
- `design` - 架构设计
- `fix` - 修复问题
- `automation` - 自动化任务
- `document` - 文档生成
- `game` - 游戏开发
- `security` - 安全审计
- `evolution` - 系统进化
- `optimize` - 性能优化
- `alert` - 告警通知

### 2. 关键词映射

中文关键词示例：
```python
"写代码" → "code"
"调试" → "debug"
"分析" → "analysis"
"监控" → "monitor"
"研究" → "research"
```

英文关键词示例：
```python
"code" → "code"
"debug" → "debug"
"analyze" → "analysis"
"monitor" → "monitor"
```

### 3. 候选排名算法

排名分数计算：
```python
score = base_score
      + priority_bonus (critical: 0.3, high: 0.2, normal: 0.1, low: 0.0)
      + success_rate * 0.2
      + min(tasks_completed * 0.05, 0.2)
```

### 4. Planning 集成

复杂任务自动拆解：
```python
router.plan_and_submit("搜索GitHub项目，然后分析架构，最后写报告")
# → 拆解为 3 个子任务：
#   1. 搜索 GitHub 项目
#   2. 分析架构
#   3. 写报告
```

## 使用方法

### CLI 命令

```bash
# 路由任务（dry-run）
python task_router.py route "写一个排序算法" --dry-run

# 提交任务到队列
python task_router.py submit "分析最近的错误日志" --priority high

# 复杂任务拆解
python task_router.py plan "搜索GitHub项目，然后分析架构，最后写报告"

# 查看队列
python task_router.py queue

# 查看统计
python task_router.py stats

# 运行测试
python task_router.py test
```

### Python API

```python
from task_router import TaskRouter

router = TaskRouter()

# 路由任务
result = router.route("写一个排序算法")
print(f"Agent: {result.agent_id}")
print(f"Confidence: {result.confidence:.0%}")

# 提交任务
task = router.submit("分析最近的错误日志", priority="high")
print(f"Task ID: {task.id}")

# 复杂任务拆解
tasks = router.plan_and_submit("搜索GitHub项目，然后分析架构，最后写报告")
print(f"拆解为 {len(tasks)} 个子任务")

# 查看队列
queue = router.get_queue()
print(f"待处理任务: {len(queue)}")

# 查看统计
stats = router.get_stats()
print(f"总路由数: {stats['total_routed']}")
```

## 配置

### Agent 注册表

路由器从 `unified_registry.json` 加载 Agent 信息：

```json
{
  "agents": [
    {
      "id": "coder",
      "name": "代码开发专家",
      "role": "编写高质量代码",
      "task_types": ["code", "refactor"],
      "status": "active",
      "priority": "high",
      "stats": {
        "success_rate": 0.85,
        "tasks_completed": 100
      }
    }
  ]
}
```

### 添加新 Agent

1. 在 `unified_registry.json` 中添加 Agent 定义
2. 指定 `task_types` 列表
3. 设置 `status` 为 `"active"`
4. 重启路由器

### 添加新关键词

编辑 `task_router.py` 中的 `KEYWORD_MAP`：

```python
KEYWORD_MAP = {
    "新关键词": "task_type",
    # ...
}
```

## 数据文件

- `unified_registry.json` - Agent 注册表
- `task_queue.jsonl` - 任务队列（JSONL 格式）
- `route_log.jsonl` - 路由日志
- `router_stats.json` - 路由统计

## 日志

路由器使用 Python `logging` 模块：

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # 启用调试日志
```

日志级别：
- `DEBUG` - 路由细节（关键词匹配、候选选择）
- `INFO` - 任务提交、路由结果
- `WARNING` - 降级、无匹配
- `ERROR` - 文件 I/O 错误、JSON 解析错误

## 性能

- 路由延迟: < 10ms（典型）
- 队列吞吐: > 1000 tasks/s
- 内存占用: < 50MB（1000 agents）

## 故障排查

### 问题：所有任务都路由到 coder

**原因：** 无精确匹配，降级到默认 Agent

**解决：**
1. 检查 `unified_registry.json` 是否存在
2. 确认 Agent 的 `task_types` 包含目标类型
3. 确认 Agent 的 `status` 为 `"active"`
4. 添加更多关键词到 `KEYWORD_MAP`

### 问题：队列任务未执行

**原因：** 路由器只负责路由，不负责执行

**解决：**
- 使用 Agent 执行器（如 `agent_executor.py`）消费队列
- 或手动调用 Agent 执行任务

### 问题：Planning 不工作

**原因：** Planner 模块未安装或导入失败

**解决：**
1. 确认 `core/planner.py` 存在
2. 检查 Planner 依赖是否安装
3. 查看日志中的 ImportError

## 测试

运行单元测试：

```bash
cd aios/agent_system
python -m pytest test_task_router.py -v
```

测试覆盖：
- 任务类型识别（6 tests）
- Agent 匹配（4 tests）
- 候选排名（4 tests）
- 模糊匹配（2 tests）
- 完整路由（2 tests）
- 队列管理（4 tests）
- 统计（3 tests）
- 错误处理（2 tests）
- Planning 集成（2 tests）

**总计：29 tests**

## 扩展

### 自定义路由策略

继承 `TaskRouter` 并重写 `_rank_candidates`：

```python
class CustomRouter(TaskRouter):
    def _rank_candidates(self, candidates, task_type, description):
        # 自定义排名逻辑
        for c in candidates:
            c["_score"] = custom_score(c, task_type, description)
        candidates.sort(key=lambda x: x["_score"], reverse=True)
        return candidates[0]
```

### 自定义任务类型识别

重写 `_identify_task_type`：

```python
class CustomRouter(TaskRouter):
    def _identify_task_type(self, description):
        # 使用 NLP 模型识别
        task_type = nlp_model.predict(description)
        confidence = nlp_model.confidence()
        return task_type, confidence
```

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## License

MIT License

## 作者

AIOS Team

## 更新日志

### v2.0 (2026-03-13)
- ✅ 添加完整的错误处理和日志
- ✅ 添加 29 个单元测试（100% 通过）
- ✅ 改进文档和注释
- ✅ Planning 集成
- ✅ 优先级队列

### v1.0 (2026-03-12)
- 初始版本
- 关键词匹配
- 模糊匹配
- 候选排名
