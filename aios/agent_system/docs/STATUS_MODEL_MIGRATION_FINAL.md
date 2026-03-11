# 状态词表迁移总验收文档

**版本：** v1.0  
**日期：** 2026-03-11  
**状态：** 迁移完成，进入制度化阶段

---

## 1. 核心成果

状态词表迁移已完成四阶段验证，太极OS 获得第一块**统一语义、统一推导、统一输出**的稳定底座。

### 解决的旧问题

1. **状态语义混乱**
   - 旧：`status` 字段混用（"active" / "idle" / "sleeping" / "failed"）
   - 新：统一状态词表（registered / executable / validated / production-ready / stable / not-executable / archived）

2. **推导逻辑分散**
   - 旧：每个消费者各自推导状态
   - 新：统一适配层（`status_adapter.py`）作为唯一入口

3. **输出不一致**
   - 旧：健康报告、日报、Dashboard 各说各话
   - 新：四个消费者输出一致，跨周期稳定

4. **无法追溯**
   - 旧：状态变化无记录
   - 新：状态推导有日志，可追溯

---

## 2. 统一适配层（唯一入口）

**文件：** `aios/agent_system/core/status_adapter.py`

**核心函数：**
```python
def get_agent_status(agent: dict) -> str:
    """统一状态推导入口"""
    pass

def get_skill_status(skill: dict) -> str:
    """统一 Skill 状态推导"""
    pass

def get_task_status(task: dict) -> str:
    """统一 Task 状态推导"""
    pass
```

**硬规则：**
- 所有消费者必须通过 `status_adapter` 读取状态
- 禁止直接读取 `agent['status']` 等旧字段
- 状态推导逻辑只在 `status_adapter` 中维护

---

## 3. 四阶段验证

### Phase 1：读得对（健康报告）
- **消费者：** `health_check_v2.py`
- **验证内容：** 状态推导逻辑正确
- **结果：** ✅ PASS

### Phase 2：说得通（日报）
- **消费者：** `daily_report_v2.py`
- **验证内容：** 状态语义一致，输出可读
- **结果：** ✅ PASS

### Phase 3：算得稳（Dashboard）
- **消费者：** `dashboard_v2.py`
- **验证内容：** 状态统计准确，分类清晰
- **结果：** ✅ PASS

### Phase 4：跨周期稳定（周报）
- **消费者：** `weekly_report_v2.py`
- **验证内容：** 跨周期状态一致，无漂移
- **结果：** ✅ PASS

---

## 4. 旧字段退场计划

### 当前状态（2026-03-11）

**旧字段仍存在：**
- `agent['status']` - 旧状态字段（混用）
- `agent['state']` - 旧状态字段（部分 Agent）
- `skill['status']` - 旧状态字段（部分 Skill）

**新字段已引入：**
- `agent['lifecycle_status']` - 新状态字段（部分 Agent）
- 统一适配层推导逻辑

### 退场时间表

**Phase 1（当前）：冻结旧入口**
- ✅ 禁止新代码直接读取旧字段
- ✅ 所有新消费者必须通过 `status_adapter`
- ⏳ 旧字段保留，但不再更新

**Phase 2（2026-03-18）：标记废弃**
- 在旧字段上加 `@deprecated` 注释
- 在文档中明确标记为废弃
- 开始迁移旧消费者

**Phase 3（2026-03-25）：完全移除**
- 删除所有旧字段
- 删除所有旧推导逻辑
- 只保留 `status_adapter` 作为唯一入口

### 禁止直接读取旧字段的模块

**已迁移（adapter-only）：**
- `health_check_v2.py`
- `daily_report_v2.py`
- `dashboard_v2.py`
- `weekly_report_v2.py`

**待迁移：**
- `heartbeat_v5.py`（部分逻辑）
- `task_executor.py`（部分逻辑）
- 其他旧脚本

---

## 5. 回归基线

### Golden Snapshots

**文件位置：** `aios/agent_system/tests/golden/`

**内容：**
1. `health_check_golden.json` - 健康报告基线
2. `daily_report_golden.json` - 日报基线
3. `dashboard_golden.json` - Dashboard 基线
4. `weekly_report_golden.json` - 周报基线

### Smoke Cases

**测试脚本：** `aios/agent_system/tests/test_status_regression.py`

**测试内容：**
1. 状态推导逻辑不变
2. 输出格式不变
3. 统计数字不漂移
4. 跨周期一致性

**运行方式：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python tests/test_status_regression.py
```

**验收标准：**
- 所有测试通过
- 无状态漂移
- 无输出格式变化

---

## 6. 下一步（Phase 5 候选）

**当前阶段：** 收官 + 制度化

**Phase 5 候选（待状态模型稳定后）：**
1. 告警系统（基于状态自动触发）
2. 自动决策（基于状态自动执行）
3. 状态可视化（Dashboard 增强）
4. 状态历史追踪（时间序列分析）

**进入 Phase 5 的前提：**
- 状态模型已固化为制度
- 回归基线已建立
- 旧字段已完全退场
- 无状态漂移问题

---

## 7. 核心原则

### 统一语义
- 所有状态使用统一词表
- 所有推导使用统一逻辑
- 所有输出使用统一格式

### 统一推导
- 唯一入口：`status_adapter.py`
- 禁止分散推导
- 禁止直接读取旧字段

### 统一输出
- 健康报告、日报、Dashboard、周报输出一致
- 跨周期稳定
- 可追溯、可验证

---

## 8. 一句话总结

> 状态词表迁移已完成，太极OS 获得第一块统一语义、统一推导、统一输出的稳定底座。

下一步不是继续扩张，而是把它固化成制度。

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-11
