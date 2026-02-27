# CHANGELOG

## [1.0.0] - 2026-02-27

### 🎉 重大里程碑：完整的自我进化闭环

#### 核心系统
- **Storage Manager** - SQLite 持久化存储（Agent 状态/上下文/事件/任务历史）
- **DataCollector** - 统一数据采集层（5 种标准 Schema）
- **Evaluator** - 量化评估系统（任务/Agent/系统/改进评估）
- **Quality Gates** - 三层质量门禁（L0 自动测试/L1 回归测试/L2 人工审核）
- **Self-Improving Loop v2.0** - 安全自我进化闭环（10 步完整流程）
- **Heartbeat v4.0/v5.0** - 自动监控和任务队列处理

#### SDK 模块化
- **Planning SDK** - 任务拆解和规划（CoT/ReAct/ToT 三种模式）
- **Memory SDK** - 短期/长期记忆管理（向量检索 + 分层存储）
- **Action SDK** - 工具调用和执行（统一接口）
- **Storage SDK** - 持久化存储（SQLite + 异步支持）

#### Agent 生态
- **统一注册表** - Learning Agents（27 个）+ Skill Agents（37 个）
- **Agent 部署器** - Skill → Agent 一键转换
- **Agent 团队模板** - 核心技术团队/设计研究团队/社区安全团队

#### Skills（新增 10+）
- **pdf-skill** - PDF 提取/生成/合并/拆分
- **perplexity-search** - AI 搜索（基础/对话/深度研究）
- **git-skill** - Git 操作封装
- **docker-skill** - Docker 容器管理
- **database-skill** - SQLite/PostgreSQL 操作
- **api-testing-skill** - API 测试和验证
- **vm-controller-skill** - VM 生命周期管理
- **data-collector-skill** - 数据采集 CLI
- **evaluator-skill** - 评估 CLI
- **quality-gates-skill** - 质量门禁 CLI
- **self-improving-skill** - 自我改进 CLI

#### 文档完善
- 20+ 份完整使用指南
- 统一文档结构（README.md 为主入口）
- 完整的 API 参考和示例

#### 清理和归档
- 归档旧文档到 `aios/archive/`
- 清理临时测试文件
- 统一代码风格（LF → CRLF）

### 技术细节
- 总代码：~134,550 行新增
- 总测试：27/27 ✅
- 文件数：328 个改动
- 数据库：SQLite（8 个索引，4 张表）

### 核心价值
从"盲飞"到"安全自我进化"的质变：
```
DataCollector（眼睛）→ Evaluator（大脑）→ Quality Gates（刹车）→ Self-Improving Loop（进化）→ Heartbeat（监控）
```

## [Unreleased]

### Fixed
- **insight.py**: Separate test critical events from real critical events
  - Critical events now split into real vs test (identified by `sig="sig_abc"` or `test=True` in payload)
  - Output format: `⚠️ 致命事件(含测试): 1 (测试1)` when test events present
  - Output format: `⚠️ 致命事件: N` when only real critical events
- **insight.py**: Exclude deploy/restart windows from loop detection
  - Loop detection now filters out consecutive KERNEL events when all are `deploy/restart/rollout` operations
  - Reduces false positives from normal deployment batches
  - Added `excluded_deploy_restart` counter for traceability
  - Output includes: `ℹ️ 已排除部署窗口: N` when deployment windows excluded

### Technical Details
- `alerts.py`: No changes - maintains existing rule-based CRIT detection (does not read event logs directly)
- `baseline.py`: No changes - `evolution_score` and `grade` continue to be computed by `evolution_score()` function based on historical snapshots, not stored in baseline.jsonl

### Commit
```
fix(insight): separate test critical events and exclude deploy/restart windows from loop detection
```

---

## [0.2.0] - 2026-02-19

### Added
- 5-layer event architecture (KERNEL/COMMS/TOOL/MEM/SEC)
- Alert state machine (alert_fsm.py) with OPEN/ACK/RESOLVED states
- Safe execution wrapper (safe_run.py) with risk levels and rollback
- Job queue system (job_queue.py) with retry and dead-letter handling
- Daily insight reports with loop detection
- Reflection engine with rule-based strategy generation

### Changed
- Migrated from v0.1 flat event schema to v0.2 layered schema
- Backward compatibility maintained for v0.1 events

---

## [0.1.0] - 2026-02-18

### Added
- Initial AIOS event logging system
- Basic autolearn framework
- ARAM Helper integration
- Memory management (MEMORY.md, daily logs)
