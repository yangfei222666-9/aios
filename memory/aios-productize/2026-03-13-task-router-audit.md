# AIOS 产品化打磨记录 - task_router.py

## 2026-03-13 - Session 2: task_router.py

### 选择模块
`aios/agent_system/task_router.py` - 智能任务路由系统

**选择理由：**
- AIOS 核心路由引擎，决定任务分发质量
- 代码量适中（~500 行），逻辑清晰
- 已有基础功能，适合打磨成开源标准

---

## 开源标准审查结果

| 维度 | 原始状态 | 问题 |
|------|---------|------|
| 可读性 | ✅ 良好 | 代码结构清晰，注释充分 |
| 文档 | ⚠️ 基础 | 有 docstring，但缺少模块级架构说明 |
| 错误处理 | ⚠️ 部分 | `_load_registry` 等方法缺少异常处理 |
| 测试 | ❌ 无 | 零测试覆盖（只有 CLI test 命令） |
| 类型注解 | ✅ 完整 | 所有函数都有类型注解 |
| 日志 | ❌ 无 | 无任何日志输出 |
| 性能 | ⚠️ 未知 | 未做性能测试 |
| 国际化 | ❌ 差 | 中文硬编码，Windows 控制台乱码 |

---

## 待改进项

### 1. 错误处理改进
- `_load_registry()`: 捕获 JSON 解析错误
- `_load_stats()`: 已有 try-except，但应记录日志
- `_save_stats()`: 捕获写入失败
- `_log_route()`: 捕获写入失败
- `submit()`: 捕获队列写入失败

### 2. 日志系统
- 添加 `logging` 模块
- 关键操作记录日志：路由决策、队列操作、错误
- 日志级别：DEBUG（路由细节）、INFO（任务提交）、ERROR（异常）

### 3. 单元测试
需要测试：
- `_identify_task_type()` - 关键词识别
- `_find_agents_for_type()` - Agent 匹配
- `_fuzzy_match()` - 模糊匹配
- `_rank_candidates()` - 排名算法
- `route()` - 完整路由流程
- `submit()` - 任务提交
- `get_queue()` - 队列读取
- `plan_and_submit()` - Planning 集成

### 4. 性能优化
- `_load_registry()` 每次调用都读文件 → 缓存 + 文件监控
- `get_queue()` 每次都读整个文件 → 增量读取
- `_fuzzy_match()` 遍历所有 Agent → 建立索引

### 5. 国际化
- 提取中文字符串到常量
- 支持 UTF-8 输出（Windows 控制台）
- 关键词映射表支持多语言

### 6. 文档改进
- 添加模块级架构图（路由流程）
- 添加配置说明（如何添加新 Agent）
- 添加故障排查指南

---

## 重构计划

### Phase 1: 错误处理 + 日志（30 分钟）
- 添加 `logging` 配置
- 所有文件 I/O 添加 try-except
- 关键决策点记录日志

### Phase 2: 单元测试（60 分钟）
- 创建 `test_task_router.py`
- 测试所有核心方法
- Mock 文件 I/O

### Phase 3: 性能优化（30 分钟）
- Registry 缓存
- 队列增量读取
- 模糊匹配索引

### Phase 4: 文档（20 分钟）
- 模块级 docstring
- README_task_router.md
- 配置示例

---

## 开始重构...
