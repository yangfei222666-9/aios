# 状态定义 v1

**生效日期：** 2026-03-14

---

## A. 协作状态（提交/审查流程）

| 状态 | 含义 | 谁设置 |
|------|------|--------|
| todo | 已定义，未开始 | 珊瑚海/小正 |
| in_progress | 正在执行 | 小九 |
| pending_review | 已提交，等待审查 | 小九 |
| revision | 审查打回，需修改 | 小正/珊瑚海 |
| done | 总控收口确认 | 珊瑚海 |

### 协作状态流转

```
todo → in_progress → pending_review → done
                                     ↘ revision → in_progress（循环）
```

### 协作状态规则

1. 只有珊瑚海能把状态设为 done
2. 小九不能跳过 pending_review 直接标 done
3. revision 必须附审查意见
4. 状态变更必须有时间戳

---

## B. 运行时状态（执行链）

| 状态 | 含义 | 触发条件 |
|------|------|----------|
| executing | 正在执行中 | 任务被调度器拾取 |
| pending | 执行未完成，等待重试或推进 | 执行中断、超时、部分失败 |
| blocked | 需要人工介入或外部条件才能继续 | pending 超阈值升级、权限/资源缺失、安全边界阻断、关键验证失败 |
| failed | 执行失败，已记录错误 | 重试耗尽、不可恢复错误 |
| completed | 单次执行已完成 | 执行成功并通过验证 |
| manual_review | 需要人工审查才能继续 | 低置信度结果、高风险操作、安全敏感动作 |
| verifying | 执行完成，正在验证结果 | 执行器返回结果后进入验证 |
| retry | 准备重试 | 可恢复错误、pending 推进 |

### 运行时状态流转

```
executing → completed（成功）
executing → pending（中断/超时）
executing → failed（不可恢复）
executing → verifying（需验证）

verifying → completed（验证通过）
verifying → failed（验证失败）
verifying → manual_review（低置信度）

pending → retry → executing（自动重试）
pending → blocked（超阈值，如 retry_count >= 3）
pending → manual_review（需人工判断）

blocked → executing（人工解除后）
blocked → failed（人工判定放弃）

manual_review → executing（人工确认继续）
manual_review → blocked（人工判定阻塞）
manual_review → failed（人工判定放弃）
```

### 运行时状态规则

1. pending 超阈值（默认 retry_count >= 3）自动升级为 blocked
2. 高风险操作执行前必须进入 manual_review
3. heartbeat 不是执行器，只做状态推进、升级和告警
4. blocked 必须注明阻塞原因和阻塞时间
5. completed 和协作层 done 是不同概念：completed 是单次执行完成，done 是总控收口确认
6. 状态变更必须有 ISO 8601+UTC 时间戳

---

## C. 两层状态的关系

- 协作状态面向人（提交、审查、收口）
- 运行时状态面向系统（执行、重试、验证、告警）
- 一个协作任务（in_progress）内部可能经历多次运行时状态流转
- 运行时 completed 不等于协作层 done，必须经过审查收口

---

**版本：** v1
