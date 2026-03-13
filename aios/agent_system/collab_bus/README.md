# 双 AI 协作中转器

## 目录结构

```
collab_bus/
├── inbox/          # 小九写入，Hanzo 读取
├── outbox/         # Hanzo 写入，小九 读取
├── archive/        # 已完成任务归档
└── schemas/        # 消息格式定义
    ├── task.schema.json
    ├── result.schema.json
    └── review.schema.json
```

## 消息流向

### 任务下发
```
Hanzo → outbox/task_*.json → 小九读取 → inbox/result_*.json → Hanzo 读取
```

### 审查反馈
```
Hanzo → outbox/review_*.json → 小九读取 → 修正 → inbox/result_*.json → Hanzo 读取
```

## 使用方式

### 小九（执行者）
1. 定期检查 `outbox/` 目录，读取 `task_*.json`
2. 执行任务，完成后写入 `inbox/result_*.json`
3. 如果收到 `review_*.json`，根据意见修正，重新写入 `inbox/result_*.json`

### Hanzo（审查者）
1. 定期检查 `inbox/` 目录，读取 `result_*.json`
2. 审查结果，写入 `outbox/review_*.json`
3. 如果审查通过，将任务归档到 `archive/`

## 状态机

```
pending → in_progress → ready_for_review → approved → archived
                              ↓
                        needs_revision
                              ↓
                        in_progress (循环)
```

## 下一步

等待小九交付：
1. `router.py` - 消息路由器
2. `state_machine.py` - 状态迁移表
3. 测试用例 - 验证完整流程

---

**版本：** v0.1  
**最后更新：** 2026-03-13
