# 状态迁移表 v1.1

## 主链（标准流程）

消息类型主链：
```
task_dispatch -> task_result -> review -> summary
```

对应状态迁移：
```
planned -> dispatched -> executing -> reviewing -> done
```

> `summary` 只负责对用户汇报，不推进状态。任务是否完成由 `review` 决定。

---

## 完整迁移表

| 当前状态 | 可转入状态 | 触发者 | 触发条件 |
|---------|-----------|--------|---------|
| `planned` | `dispatched` | openclaw | task_dispatch 消息到达 |
| `dispatched` | `executing` | xiaojiu | task_result 消息到达（执行者开始执行） |
| `dispatched` | `waiting_user_confirm` | router | 安全闸门触发 |
| `executing` | `reviewing` | xiaojiu | task_result 消息到达（执行者完成） |
| `executing` | `waiting_user_confirm` | router | 安全闸门触发 |
| `reviewing` | `done` | openclaw | review 审查通过，无需确认 |
| `reviewing` | `waiting_user_confirm` | openclaw | review 审查完成，需要用户拍板 |
| `waiting_user_confirm` | `done` | user | 用户同意 |
| `waiting_user_confirm` | `planned` | user | 用户要求修改，重新派发 |
| `failed` | `blocked` | router | 连续失败 ≥3 次 |
| `blocked` | `planned` | user | 人工介入后恢复 |

> `failed` 是全局异常态，通过 `mark_failed()` 从任意状态进入，不受上表限制。

---

## 消息类型 vs 状态（严格区分）

| 消息类型 | 对应状态变化 | 说明 |
|---------|------------|------|
| `task_dispatch` | `planned -> dispatched` | 派发任务 |
| `task_result` | `dispatched -> executing -> reviewing` | 执行者完成 |
| `review` | `reviewing -> done` 或 `reviewing -> waiting_user_confirm` | 审查者决定 |
| `summary` | 不改变状态 | 只做用户汇报 |
| `need_confirm` | 触发 `waiting_user_confirm` | 安全闸门消息类型，不是状态 |
| `error` | 触发 `failed` | 路由失败通知 |

---

## 转换时必须更新的字段

每次状态转换，必须同步更新：
- `stage` — 新状态
- `current_owner` — 当前负责人
- `last_message_from` — 触发者
- `next_action` — 下一步动作
- `last_summary` — 当前摘要
- `updated_at` — 更新时间
- `history[]` — 追加一条迁移记录（含 at / from / action / note）

---

## 异常处理规则

- `failed` — 全局异常态，走 `mark_failed()`，不走普通迁移校验
- `blocked` — 连续失败 ≥3 次，只能人工恢复（`blocked -> planned`）
- 未知消息类型 — 拒绝处理，写入 error_log，生成 error 消息到 inbox

---

## v0 约束

- 不实现自动重试（`retry_count` 字段保留但不触发自动重试）
- 失败先记录到 `error_log`，等人工决定是否重试
- `blocked` 状态只能人工恢复
- `summary` 不推进状态，只做汇报

---

**版本：** v1.1
**变更：** waiting_user_confirm 迁移修正（-> done / -> planned）；补充消息类型 vs 状态对照表；明确 summary 不推进状态
