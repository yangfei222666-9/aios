# 太极OS 架构概览

**版本：** v1.0  
**最后更新：** 2026-03-10

---

## 系统架构

```
太极OS（TaijiOS）
├── Agent System（多 Agent 协作）
│   ├── Learning Agents（学习型 Agent）
│   ├── Task Executors（任务执行器）
│   └── Agent Registry（Agent 注册表）
├── Task Queue（任务队列）
│   ├── Task Submission（任务提交）
│   ├── Task Scheduling（任务调度）
│   └── Task Execution（任务执行）
├── Memory System（记忆系统）
│   ├── Memory Server（常驻进程）
│   ├── Memory Search（记忆检索）
│   └── Memory Ingestion（记忆摄入）
├── Skill System（技能系统）
│   ├── Skill Registry（技能注册表）
│   ├── Skill Execution（技能执行）
│   └── Skill Auto-Creation（技能自动创建）
├── Self-Improving Loop（自我改进闭环）
│   ├── Pattern Detection（模式检测）
│   ├── Improvement Generation（改进生成）
│   └── Quality Gates（质量门禁）
├── Observability（可观测性）
│   ├── Reality Ledger（真实性账本）
│   ├── Evolution Score（进化分数）
│   └── Dashboard（可视化监控）
└── Core Mechanisms（核心机制）
    ├── Heartbeat（心跳检查）
    ├── Alert Deduplication（告警去重）
    └── Observation Period（观察期原则）
```

---

## 核心组件

### 1. Agent System
**功能：** 多 Agent 协作与任务调度

**组件：**
- **Learning Agents** - 学习型 Agent，持续学习与改进
- **Task Executors** - 任务执行器，执行具体任务
- **Agent Registry** - Agent 注册表，管理所有 Agent

**特点：**
- 多 Agent 协作
- 动态调度
- 状态跟踪

### 2. Task Queue
**功能：** 任务队列与执行管理

**组件：**
- **Task Submission** - 任务提交接口
- **Task Scheduling** - 任务调度器
- **Task Execution** - 任务执行器

**特点：**
- 优先级队列
- 自动重试
- 状态更新

### 3. Memory System
**功能：** 记忆系统与上下文管理

**组件：**
- **Memory Server** - 常驻进程，消除冷启动延迟
- **Memory Search** - 语义检索
- **Memory Ingestion** - 记忆摄入

**特点：**
- 语义检索
- 向量化存储
- 快速查询

### 4. Skill System
**功能：** 技能系统与能力扩展

**组件：**
- **Skill Registry** - 技能注册表
- **Skill Execution** - 技能执行器
- **Skill Auto-Creation** - 技能自动创建

**特点：**
- 动态加载
- 触发条件
- 自动创建

### 5. Self-Improving Loop
**功能：** 自我改进闭环

**组件：**
- **Pattern Detection** - 模式检测
- **Improvement Generation** - 改进生成
- **Quality Gates** - 质量门禁（L0/L1/L2）

**特点：**
- 自动检测
- 自动改进
- 三层验证

### 6. Observability
**功能：** 可观测性与监控

**组件：**
- **Reality Ledger** - 真实性账本，记录完整生命周期
- **Evolution Score** - 进化分数，衡量真实收益
- **Dashboard** - 可视化监控

**特点：**
- 完整记录
- 实时监控
- 可视化展示

---

## 核心机制

### 1. Heartbeat（心跳检查）
**功能：** 自动检查与任务处理

**流程：**
1. 处理任务队列
2. 检查并启动休眠 Agent
3. 处理连续失败问题
4. Self-Improving Loop 检查
5. 清理与记录

**频率：** 每 30 秒

### 2. Alert Deduplication（告警去重）
**功能：** 智能告警管理，避免重复通知

**规则：**
- 已发过的告警不重复通知
- 仅在以下情况重新通知：
  - 连续失败次数继续增加
  - 错误类型发生变化
  - 等级升级（WARN → CRIT）
  - 修复后再次复发

### 3. Observation Period（观察期原则）
**功能：** 先看证据，再动主链路

**原则：**
- 不碰主链路
- 先观察，再决策
- 可回滚

---

## 数据流

```
用户输入
  ↓
Task Queue（任务队列）
  ↓
Agent System（Agent 调度）
  ↓
Skill System（技能执行）
  ↓
Memory System（记忆更新）
  ↓
Reality Ledger（记录生命周期）
  ↓
Evolution Score（计算收益）
  ↓
Dashboard（可视化展示）
```

---

## 技术栈

- **语言：** Python 3.12
- **核心依赖：** torch, sentence-transformers, lancedb, fastapi
- **开发环境：** Windows 11 / VS Code
- **硬件：** Ryzen 7 9800X3D + RTX 5070 Ti + 32GB RAM

---

## 设计原则

1. **可靠性优先于花哨功能** - 先保证能跑、能收尾、能回写、能复盘
2. **先修异常，再做新功能** - 优先处理执行断点、僵尸任务、状态不一致
3. **先验证，再扩张** - 先用真实数据证明，再扩大范围
4. **优先做可长期复用的能力** - Runtime、Queue、Memory、Learning Loop
5. **以系统视角判断价值** - 是否增强底层能力、是否让系统更稳

---

**版本：** v1.0  
**最后更新：** 2026-03-10
