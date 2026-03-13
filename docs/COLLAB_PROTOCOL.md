# 双 AI 协作协议 v0.1

## 核心理念

**一句话：** 两个 AI 通过文件中转协作，不依赖 Telegram bot 互聊。

---

## 角色定义

### Hanzo（审查者）
- **职责：** 审查、拆解、给建议、把关质量
- **权限：** 只读系统状态，不直接执行命令
- **输出：** 任务拆解、审查意见、改进建议

### 小九（执行者）
- **职责：** 执行任务、写代码、跑命令、交付结果
- **权限：** 完整系统访问权限
- **输出：** 代码、执行日志、状态更新

---

## 协作流程

### 1. 任务下发（珊瑚海 → 小九）
```
珊瑚海：把需求发给小九
小九：接收任务，开始执行
```

### 2. 结果审查（小九 → Hanzo）
```
珊瑚海：把小九的输出贴给 Hanzo
Hanzo：审查结果，给出意见
```

### 3. 迭代修正（循环）
```
Hanzo：发现问题 → 给建议
珊瑚海：转达给小九
小九：修正 → 交付新版本
重复 2-3 直到通过
```

---

## 中转器方案（B 方案）

### 目录结构
```
aios/agent_system/collab_bus/
├── inbox/          # 小九写入，Hanzo 读取
├── outbox/         # Hanzo 写入，小九 读取
├── archive/        # 已完成任务归档
└── schemas/        # 消息格式定义
```

### 消息格式

#### 任务请求（outbox/task_*.json）
```json
{
  "id": "task_20260313_001",
  "type": "code_review",
  "from": "hanzo",
  "to": "xiaojiu",
  "timestamp": "2026-03-13T19:00:00Z",
  "payload": {
    "file": "aios/agent_system/router.py",
    "focus": ["状态迁移", "错误处理", "v0 克制度"]
  },
  "status": "pending"
}
```

#### 任务结果（inbox/result_*.json）
```json
{
  "id": "result_20260313_001",
  "task_id": "task_20260313_001",
  "from": "xiaojiu",
  "to": "hanzo",
  "timestamp": "2026-03-13T19:30:00Z",
  "payload": {
    "status": "completed",
    "files": ["router.py", "state_machine.py"],
    "summary": "已完成 v0 router 实现，状态迁移表已补齐"
  },
  "status": "ready_for_review"
}
```

#### 审查意见（outbox/review_*.json）
```json
{
  "id": "review_20260313_001",
  "result_id": "result_20260313_001",
  "from": "hanzo",
  "to": "xiaojiu",
  "timestamp": "2026-03-13T20:00:00Z",
  "payload": {
    "verdict": "needs_revision",
    "issues": [
      "状态迁移表缺少 HEALING_FAILED 处理",
      "错误处理未覆盖文件不存在场景"
    ],
    "suggestions": [
      "补充 HEALING_FAILED → PENDING 的迁移规则",
      "添加 FileNotFoundError 异常处理"
    ]
  },
  "status": "pending"
}
```

---

## 状态机

### 任务状态
- `pending` - 等待处理
- `in_progress` - 执行中
- `ready_for_review` - 等待审查
- `needs_revision` - 需要修正
- `approved` - 审查通过
- `archived` - 已归档

### 状态迁移规则
```
pending → in_progress (小九开始执行)
in_progress → ready_for_review (小九交付结果)
ready_for_review → approved (Hanzo 审查通过)
ready_for_review → needs_revision (Hanzo 发现问题)
needs_revision → in_progress (小九修正)
approved → archived (任务完成，归档)
```

---

## v0 实现范围（最小可运行）

### 小九需要交付
1. **router.py** - 消息路由器（读 inbox/outbox，分发消息）
2. **state_machine.py** - 状态迁移表（任务状态管理）
3. **schemas/** - 3 个 JSON schema（task, result, review）

### Hanzo 需要交付
1. **审查清单** - 代码审查标准（状态迁移、错误处理、v0 克制度）
2. **测试用例** - 验证 router 和状态机是否正常工作

---

## 执行纪律

### 小九
- 交付前自检：文件是否完整、状态是否更新、日志是否清晰
- 交付格式：result_*.json + 实际文件 + 执行日志
- 不交付半成品，不交付"看起来像成功"的结果

### Hanzo
- 审查前等待：小九没交文件前不聊抽象设计
- 审查重点：主链路、状态迁移、v0 克制度
- 审查输出：review_*.json + 具体问题 + 可执行建议

---

## 当前进度

- **阶段：** 协议设计完成，等待 v0 实现
- **下一步：** 小九交付 router + state_machine + schemas
- **验收标准：** 能跑通一个完整任务流程（task → result → review → revision → approved）

---

**版本：** v0.1  
**最后更新：** 2026-03-13  
**维护者：** Hanzo + 小九 + 珊瑚海
