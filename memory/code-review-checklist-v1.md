# 代码改动前最终审查清单 v1

**创建时间：** 2026-03-13 20:35  
**来源：** 珊瑚海最终审查要求  
**适用范围：** 502/pending 降级链代码改动

---

## 总原则

这次代码改动必须服从：

1. **安全第一**
2. **最小改动**
3. **向后兼容优先**
4. **先补状态与观测，再补自动恢复**
5. **不在这一轮顺手重构**

---

## 一、允许改动的文件

只允许碰这 3 个文件：

1. `aios/agent_system/agent_fallback.py`
2. `aios/agent_system/execution_logger.py`
3. `aios/agent_system/heartbeat_v6.py`

### 本轮不要碰

- Agent 调度器主流程
- 任务队列总结构
- 其他 Agent 业务代码
- provider 适配层
- 数据库 / 消息队列 / 新依赖

---

## 二、每个文件允许改什么

### 1) agent_fallback.py

**允许改：**

- `detect_error_type()`
- `get_fallback_strategy()`
- 仅为支持：
  - `gateway_error`
  - `transient_network_failure`
  - `client_error`
  - `mark_pending` 动作

**不要改：**

- 原有其他 fallback 主体流程
- 与当前 502/pending 逻辑无关的分支
- 全局接口签名，除非绝对必要

**兼容性要求：**

- `network_error` 作为兜底类保留
- 旧分支默认行为不应大面积变化

---

### 2) execution_logger.py

**允许改：**

- `fail_task()` 参数扩展
- 新增结构化字段写入：
  - `error_type`
  - `endpoint`
  - `pending_since`
  - `pending_retry_count`
  - 必要时 `blocked_at`
- 保持 `_write_record()` 不做重构，除非发现明确阻塞点

**不要改：**

- 不要改函数名
- 不要把记录系统整体重写
- 不要调整现有主账本读取协议

**兼容性要求：**

- 旧调用方不传新字段时，逻辑仍可工作
- 旧记录没有新字段时，不影响读取

**字段要求：**

- `pending_since` 只在首次 pending 时写
- 后续重试失败不得覆盖原值
- `endpoint` 统一记录 host/base endpoint，拿不到写 `unknown`
- ⚠️ `completed_at` 建议改成更中性的 `recorded_at` 或 `updated_at`

---

### 3) heartbeat_v6.py

**允许改：**

- 增加 `process_pending_tasks()`
- 在 `run()` 中插入 pending 扫描重试步骤
- 增加 `mark_blocked()` 及 inbox alert 写入

**不要改：**

- 不要重写 heartbeat 主循环
- 不要改已有主任务派发逻辑
- 不要顺手加并发、线程、队列、守护进程

**位置要求：**

- `process_pending_tasks()` 建议放在：
  - 主任务处理之后
  - 收尾之前
  - 避免 pending 重试抢占主任务流

**过滤要求：**

- 只扫 `status == "pending"`
- `pending_retry_count < 3`
- 只处理最新状态记录
- `pending_since > 24h` 或 `pending_retry_count >= 3` → `blocked`

**健壮性要求：**

- 时间解析失败不能让 heartbeat 崩
- 应进入可观察错误路径

---

## 三、本轮明确不能改的东西

这轮绝对不要做：

1. 多 provider 切换
2. 熔断器 / 断路器框架
3. 数据库存储替换 jsonl
4. 重构调度器
5. 多任务优先级系统
6. 分布式恢复机制
7. 批量 pending 管理
8. 自动告警系统外联

**一句话：**  
只修当前 502/pending 降级链，不顺手升级世界。

---

## 四、代码改动顺序

严格按这个顺序来：

### Step 1
改 `agent_fallback.py`
- 先把错误分类和动作输出定准

### Step 2
改 `execution_logger.py`
- 让状态和字段能被正确写入主账本

### Step 3
改 `heartbeat_v6.py`
- 最后才加 pending 的恢复入口和 blocked alert

**这个顺序不要反。**  
否则 heartbeat 会开始读取一个还没定义好的状态世界。

---

## 五、代码审查重点

等真开始改代码后，重点盯这 8 条：

1. ✅ pending 是否真的是显式状态
2. ✅ `fail_task()` 是否保持兼容
3. ✅ `pending_since` 是否只写一次
4. ✅ `pending_retry_count` 是否真正落盘
5. ✅ blocked 是否保留上下文
6. ✅ heartbeat 是否只扫最新状态
7. ✅ 时间解析异常是否可观察
8. ✅ 是否偷偷扩大了改动面

---

## 六、通过标准

这轮真改代码后，要算"通过"，至少满足：

1. ✅ 502 第二次失败后能进入 pending
2. ✅ 主账本能正确写入新字段
3. ✅ heartbeat 能识别并重试 pending
4. ✅ 超阈值能进入 blocked
5. ✅ inbox 能收到 blocked alert
6. ✅ 旧逻辑没明显被误伤
7. ✅ 没有引入大规模副作用

---

## 七、一句话决策

**现在可以进入真实代码修改，但必须严格按这份清单改，不能自由发散。**

---

**版本：** v1  
**状态：** 生效中  
**维护者：** 小九 + 珊瑚海
