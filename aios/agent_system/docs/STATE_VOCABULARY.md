# 太极OS 统一状态词表 v1.0

**目标：** 为 Agent / Skill / Task 建立统一的状态模型，解决"注册 ≠ 可执行 ≠ 已验证"的失真问题。

**原则：**
1. 状态必须可观测、可验证
2. 状态转换必须有明确触发条件
3. 状态命名必须清晰、无歧义
4. 同一实体在不同阶段用同一套词表

---

## 1. Agent 状态词表

### 生命周期状态

| 状态 | 含义 | 验证条件 | 下一步 |
|------|------|----------|--------|
| `registered` | 已在 agents.json 中注册 | 存在 agent_id + name + type | → executable |
| `executable` | 有可执行入口 | 存在 run_*.py 或 agent_*.py | → validated |
| `validated` | 通过 6 项验收 | Trigger/Input/Execution/Output/Writeback/Outcome 全通过 | → production-candidate |
| `production-candidate` | 候选生产 | 通过验收 + 进入观察期 | → production-ready |
| `production-ready` | 生产就绪 | 观察期通过（3 天稳定） | → stable |
| `stable` | 稳定运行 | 连续 30 天无异常 | 持续运行 |

### 异常状态

| 状态 | 含义 | 触发条件 | 处理方式 |
|------|------|----------|----------|
| `not-executable` | 已注册但无执行入口 | registered 但找不到 run_*.py | 补执行链路 |
| `not-evaluable` | 无法验收 | 缺少必要字段或依赖 | 补齐依赖 |
| `failed-validation` | 验收失败 | 6 项验收中任一项失败 | 修复后重新验收 |
| `observation-failed` | 观察期失败 | 3 天内出现异常 | 回退到 validated |
| `degraded` | 性能退化 | 成功率 < 80% 或耗时 > 2x baseline | 触发改进 |
| `suspended` | 暂停运行 | 人工暂停或连续失败 ≥ 5 次 | 人工恢复 |
| `archived` | 已归档 | 长期不用或被替代 | 不再运行 |

### 运行状态（运行时）

| 状态 | 含义 | 持续时间 |
|------|------|----------|
| `idle` | 空闲等待 | - |
| `running` | 正在执行 | 执行期间 |
| `waiting` | 等待依赖 | 等待外部资源 |
| `completed` | 执行完成 | 单次执行结束 |
| `failed` | 执行失败 | 单次执行失败 |

---

## 2. Skill 状态词表

### 生命周期状态

| 状态 | 含义 | 验证条件 | 下一步 |
|------|------|----------|--------|
| `candidate` | 候选 Skill | 被 pattern detector 识别 | → draft |
| `draft` | 草案 | 生成 SKILL.md 草案 | → validated |
| `validated` | 已验证 | 通过格式验证 + 安全扫描 + 风险评级 | → draft-registry |
| `draft-registry` | 隔离注册 | 进入 draft registry，等待试运行 | → trial |
| `trial` | 试运行 | 开始收集使用反馈 | → production-candidate |
| `production-candidate` | 候选生产 | 试运行通过（≥ 3 次成功） | → production-ready |
| `production-ready` | 生产就绪 | 正式注册到 skills/ | → stable |
| `stable` | 稳定可用 | 连续 30 天无异常 | 持续可用 |

### 异常状态

| 状态 | 含义 | 触发条件 | 处理方式 |
|------|------|----------|----------|
| `validation-failed` | 验证失败 | 格式错误 / 安全风险 / 高风险评级 | 修复后重新验证 |
| `trial-failed` | 试运行失败 | 连续 3 次失败 | 回退到 draft |
| `deprecated` | 已废弃 | 被更好的 Skill 替代 | 标记但保留 |
| `archived` | 已归档 | 长期不用 | 移出主目录 |

---

## 3. Task 状态词表

### 生命周期状态

| 状态 | 含义 | 触发条件 | 下一步 |
|------|------|----------|--------|
| `pending` | 待处理 | 刚提交到队列 | → queued |
| `queued` | 已入队 | 进入 task_queue.jsonl | → assigned |
| `assigned` | 已分配 | 分配给 Agent | → running |
| `running` | 执行中 | Agent 正在执行 | → completed / failed |
| `completed` | 已完成 | 执行成功 + 写回完成 | 结束 |
| `failed` | 执行失败 | 执行异常或超时 | → retry / archived |

### 异常状态

| 状态 | 含义 | 触发条件 | 处理方式 |
|------|------|----------|----------|
| `retry` | 等待重试 | 失败但未达重试上限 | 重新入队 |
| `timeout` | 执行超时 | 超过 runTimeoutSeconds | 标记失败 |
| `zombie` | 僵尸任务 | 长时间 running 但无心跳 | 人工介入 |
| `cancelled` | 已取消 | 人工取消 | 结束 |
| `archived` | 已归档 | 失败且达重试上限 | 不再重试 |

---

## 4. Lesson 状态词表

### 生命周期状态

| 状态 | 含义 | 验证条件 | 下一步 |
|------|------|----------|--------|
| `recorded` | 已记录 | 写入 lessons.json | → pending |
| `pending` | 待提炼 | 等待提炼为规则 | → extracted |
| `extracted` | 已提炼 | 提炼出可复用规则 | → applied |
| `applied` | 已应用 | 规则写回到系统 | → validated |
| `validated` | 已验证 | 规则生效且有效 | → stable |
| `stable` | 稳定有效 | 连续 30 天有效 | 持续有效 |

### 异常状态

| 状态 | 含义 | 触发条件 | 处理方式 |
|------|------|----------|----------|
| `extraction-failed` | 提炼失败 | 无法提炼出规则 | 人工介入 |
| `invalid` | 规则无效 | 应用后无效或有害 | 回滚 |
| `deprecated` | 已废弃 | 被更好的规则替代 | 标记但保留 |

---

## 5. 状态转换规则

### Agent 状态转换

```
registered → executable → validated → production-candidate → production-ready → stable
    ↓            ↓            ↓                ↓                    ↓
not-executable  not-evaluable  failed-validation  observation-failed  degraded
                                                                        ↓
                                                                    suspended
                                                                        ↓
                                                                    archived
```

### Skill 状态转换

```
candidate → draft → validated → draft-registry → trial → production-candidate → production-ready → stable
              ↓         ↓             ↓            ↓              ↓
         validation-failed  validation-failed  trial-failed  trial-failed  deprecated
                                                                              ↓
                                                                          archived
```

### Task 状态转换

```
pending → queued → assigned → running → completed
                                 ↓
                              failed → retry (< 3 次)
                                 ↓
                              archived (≥ 3 次)
```

### Lesson 状态转换

```
recorded → pending → extracted → applied → validated → stable
              ↓          ↓          ↓          ↓
         extraction-failed  extraction-failed  invalid  deprecated
```

---

## 6. 实施计划

### Phase 1: 状态字段标准化（本周）
- [ ] 在 agents.json 中增加 `status` 字段
- [ ] 在 skills/ 中增加 `status` 字段（frontmatter）
- [ ] 在 task_queue.jsonl 中增加 `status` 字段
- [ ] 在 lessons.json 中增加 `status` 字段

### Phase 2: 状态迁移脚本（本周）
- [ ] 编写 `migrate_agent_status.py`
- [ ] 编写 `migrate_skill_status.py`
- [ ] 编写 `migrate_task_status.py`
- [ ] 编写 `migrate_lesson_status.py`

### Phase 3: 状态验证工具（下周）
- [ ] 编写 `validate_status.py`（检查状态一致性）
- [ ] 集成到 health check
- [ ] 集成到 Dashboard

### Phase 4: 状态转换自动化（下周）
- [ ] Agent 状态自动转换
- [ ] Skill 状态自动转换
- [ ] Task 状态自动转换
- [ ] Lesson 状态自动转换

---

## 7. 验收标准

### 最小验收（Phase 1 完成后）
- [ ] 所有 Agent 都有 `status` 字段
- [ ] 所有 Skill 都有 `status` 字段
- [ ] 所有 Task 都有 `status` 字段
- [ ] 所有 Lesson 都有 `status` 字段
- [ ] 状态值符合词表定义

### 完整验收（Phase 4 完成后）
- [ ] 状态转换自动化
- [ ] Dashboard 显示正确状态
- [ ] Health check 基于状态判断
- [ ] 日报基于状态生成
- [ ] 无状态失真问题

---

**版本：** v1.0  
**创建时间：** 2026-03-11  
**维护者：** 小九 + 珊瑚海  
**状态：** draft → review-pending
