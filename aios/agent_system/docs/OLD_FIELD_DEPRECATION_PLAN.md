# 旧字段退场计划

**版本：** v1.0  
**日期：** 2026-03-11  
**状态：** Phase 1 - 冻结旧入口

---

## 1. 当前状态

### 旧字段仍存在

**Agent：**
- `agent['status']` - 旧状态字段（混用："active" / "idle" / "sleeping" / "failed"）
- `agent['state']` - 旧状态字段（部分 Agent）

**Skill：**
- `skill['status']` - 旧状态字段（部分 Skill）

**Task：**
- `task['status']` - 当前仍在使用（pending / running / completed / failed）

### 新字段已引入

**Agent：**
- `agent['lifecycle_status']` - 新状态字段（部分 Agent）
- 统一适配层推导逻辑（`status_adapter.py`）

**Skill：**
- `skill['lifecycle_status']` - 新状态字段（部分 Skill）
- 统一适配层推导逻辑

**Task：**
- 保持 `task['status']`（已统一）

---

## 2. 退场时间表

### Phase 1：冻结旧入口（当前）

**时间：** 2026-03-11 - 2026-03-18

**目标：** 禁止新代码直接读取旧字段

**行动：**
- ✅ 所有新消费者必须通过 `status_adapter`
- ✅ 旧字段保留，但不再更新
- ✅ 在代码审查中拒绝直接读取旧字段的 PR

**验收标准：**
- 所有新代码通过 `status_adapter` 读取状态
- 无新代码直接读取 `agent['status']` 或 `skill['status']`

---

### Phase 2：标记废弃（2026-03-18 - 2026-03-25）

**目标：** 明确标记旧字段为废弃

**行动：**
- 在旧字段上加 `@deprecated` 注释
- 在文档中明确标记为废弃
- 开始迁移旧消费者（heartbeat_v5.py, task_executor.py 等）

**验收标准：**
- 所有旧字段有 `@deprecated` 标记
- 文档中明确说明废弃时间表
- 至少 50% 旧消费者已迁移

---

### Phase 3：完全移除（2026-03-25+）

**目标：** 删除所有旧字段和旧推导逻辑

**行动：**
- 删除所有旧字段（`agent['status']`, `skill['status']`）
- 删除所有旧推导逻辑
- 只保留 `status_adapter` 作为唯一入口

**验收标准：**
- 所有旧字段已删除
- 所有旧推导逻辑已删除
- 回归测试全部通过

---

## 3. 禁止直接读取旧字段的模块

### 已迁移（adapter-only）

- ✅ `health_check_v2.py`
- ✅ `daily_report_v2.py`
- ✅ `dashboard_v2.py`
- ✅ `weekly_report_v2.py`

### 待迁移

- ⏳ `heartbeat_v5.py`（部分逻辑）
- ⏳ `task_executor.py`（部分逻辑）
- ⏳ 其他旧脚本

---

## 4. 迁移指南

### 旧代码（禁止）

```python
# ❌ 禁止直接读取旧字段
status = agent['status']
if status == 'active':
    ...
```

### 新代码（推荐）

```python
# ✅ 通过 status_adapter 读取
from core.status_adapter import get_agent_status

status = get_agent_status(agent)
if status == 'stable':
    ...
```

---

## 5. 代码审查清单

在代码审查时，检查以下内容：

- [ ] 是否直接读取 `agent['status']`？
- [ ] 是否直接读取 `skill['status']`？
- [ ] 是否通过 `status_adapter` 读取状态？
- [ ] 是否使用统一状态词表？

如果发现直接读取旧字段，要求修改为通过 `status_adapter` 读取。

---

## 6. 回滚计划

如果在 Phase 2 或 Phase 3 中发现严重问题，可以回滚到 Phase 1：

1. 恢复旧字段
2. 恢复旧推导逻辑
3. 保留 `status_adapter` 作为可选入口
4. 分析问题原因
5. 修复后重新进入 Phase 2

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-11
