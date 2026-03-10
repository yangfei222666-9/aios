# Phase 3 实施计划

**目标：** 更新核心模块，使用统一的 agent_type 分类

---

## 需要修改的模块

### 1. agent_lifecycle_engine.py
**修改点：**
- 读取 agent_type 字段
- 根据 agent_type 生成不同的 lifecycle stage
- standby_emergency → "坎 - 险中求进（待命中）"
- disabled → "剥 - 剥落退场（已禁用）"
- shadow → "蒙 - 启蒙待发（影子模式）"

### 2. health_report.py（如果存在）
**修改点：**
- 根据 agent_type 生成不同的 health status
- standby_emergency → "STANDBY"，不生成建议
- disabled → "DISABLED"，不生成建议

### 3. suggestion_generator.py（如果存在）
**修改点：**
- standby_emergency 和 disabled 不生成"建议激活"
- degraded 生成"检查失败原因"

### 4. diagnostics.py（如果存在）
**修改点：**
- 根据 agent_type 生成不同的诊断信息
- standby_emergency → "应急待命中，触发条件未满足"
- disabled → "已禁用，按设计停用"

---

## 实施顺序

1. ✅ Phase 2: 更新 agents.json（已完成）
2. Phase 3.1: 修改 agent_lifecycle_engine.py
3. Phase 3.2: 检查并修改 health_report.py
4. Phase 3.3: 检查并修改 suggestion_generator.py
5. Phase 3.4: 检查并修改 diagnostics.py
6. Phase 4: 验证

---

## 当前状态

**已完成：**
- ✅ Phase 1: 定义分类规范
- ✅ Phase 2: 更新 agents.json

**分类结果：**
- active_routable: 2
- degraded: 7
- disabled: 19
- standby_emergency: 2

**下一步：**
- Phase 3.1: 修改 agent_lifecycle_engine.py
