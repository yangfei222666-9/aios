# Day 3 最小实现顺序 + 测试清单

**目标：** 重试机制上线 + 验证 SLO 达标（90% 成功率、75% 重试恢复率、MTTR ≤10min）

**时间：** 2026-03-06 19:15 开始

---

## 📋 实现顺序（按依赖关系排序）

### 1️⃣ 重试策略配置（15min）
**文件：** `retry_config.py`

**内容：**
```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay_ms": 1000,
    "max_delay_ms": 10000,
    "backoff_multiplier": 2.0,
    "jitter_factor": 0.1,
    
    # 错误类型映射
    "error_strategies": {
        "timeout": {"max_attempts": 2, "base_delay_ms": 2000},
        "dependency_error": {"max_attempts": 3, "base_delay_ms": 500},
        "resource_exhausted": {"max_attempts": 1, "base_delay_ms": 5000},
        "logic_error": {"max_attempts": 0}  # 不重试
    },
    
    # 风险前置检查
    "storm_protection": {
        "max_retry_rate": 1.5,  # 重试放大量阈值
        "check_window_seconds": 60,
        "alert_threshold": 10  # 1分钟内重试超过10次告警
    }
}
```

**测试：**
```bash
python -c "from retry_config import RETRY_CONFIG; print(RETRY_CONFIG['max_attempts'])"
# 预期输出：3
```

---

### 2️⃣ 重试执行器（30min）
**文件：** `retry_executor.py`

**核心函数：**
```python
def execute_with_retry(task_id: str, agent_id: str, task_desc: str) -> dict:
    """
    带重试的任务执行器
    
    返回：
    {
        "success": bool,
        "attempts": int,
        "final_error": str | None,
        "retry_history": [{"attempt": 1, "error": "...", "delay_ms": 1000}]
    }
    """
    pass

def calculate_backoff(attempt: int, base_delay_ms: int, max_delay_ms: int) -> int:
    """指数退避 + 抖动"""
    pass

def should_retry(error_type: str, attempt: int) -> bool:
    """根据错误类型决定是否重试"""
    pass
```

**测试：**
```bash
python test_retry_executor.py
# 预期：3个测试全部通过
# - test_timeout_retry（超时重试2次）
# - test_logic_error_no_retry（逻辑错误不重试）
# - test_backoff_calculation（退避计算正确）
```

---

### 3️⃣ Retry Storm 风险前置检查（20min）
**文件：** `storm_detector.py`

**核心函数：**
```python
def check_retry_storm() -> dict:
    """
    检查最近1分钟的重试率
    
    返回：
    {
        "is_storm": bool,
        "retry_rate": float,  # 实际重试放大量
        "threshold": float,   # 阈值（1.5）
        "alert_message": str | None
    }
    """
    pass

def record_retry_attempt(task_id: str):
    """记录重试事件到 retry_storm_log.jsonl"""
    pass
```

**测试：**
```bash
python test_storm_detector.py
# 预期：2个测试通过
# - test_normal_retry_rate（正常重试率 < 1.5）
# - test_storm_detection（重试率 > 1.5 触发告警）
```

---

### 4️⃣ 集成到 Task Executor（15min）
**文件：** `task_executor.py`（修改现有文件）

**修改点：**
```python
# 原代码：
result = execute_task(task)

# 新代码：
from retry_executor import execute_with_retry
from storm_detector import check_retry_storm, record_retry_attempt

# 风险前置检查
storm_status = check_retry_storm()
if storm_status["is_storm"]:
    log_alert(f"[STORM] Retry rate too high: {storm_status['retry_rate']}")
    # 暂停新任务提交，等待恢复

# 执行任务（带重试）
result = execute_with_retry(task_id, agent_id, task_desc)

# 记录重试事件
if result["attempts"] > 1:
    record_retry_attempt(task_id)
```

**测试：**
```bash
python test_task_executor_integration.py
# 预期：端到端测试通过
# - 任务失败 → 自动重试 → 成功
# - 重试率超标 → 触发告警
```

---

### 5️⃣ 监控指标收集（10min）
**文件：** `retry_metrics.py`

**指标：**
```python
METRICS = {
    "retry_success_rate": 0.0,  # 重试恢复率（目标 75%+）
    "retry_attempts_avg": 0.0,  # 平均重试次数
    "retry_rate": 0.0,          # 重试放大量（目标 ≤1.5）
    "mttr_seconds": 0.0,        # 平均恢复时间（目标 ≤600s）
    "storm_alerts": 0           # 风险告警次数
}
```

**测试：**
```bash
python retry_metrics.py --report
# 预期输出：
# Retry Success Rate: 80.0%
# Retry Rate: 1.2
# MTTR: 8.5min
```

---

### 6️⃣ 集成到 Heartbeat（5min）
**文件：** `heartbeat_v5.py`（修改现有文件）

**新增检查：**
```python
from retry_metrics import get_retry_metrics
from storm_detector import check_retry_storm

# 每小时检查重试指标
metrics = get_retry_metrics()
if metrics["retry_success_rate"] < 0.75:
    log_alert(f"[SLO] Retry success rate too low: {metrics['retry_success_rate']}")

# 检查 Retry Storm
storm_status = check_retry_storm()
if storm_status["is_storm"]:
    log_alert(f"[STORM] {storm_status['alert_message']}")
```

---

### 7️⃣ Dashboard 可视化（10min）
**文件：** `dashboard/server.py`（修改现有文件）

**新增接口：**
```python
@app.route('/api/retry_metrics')
def get_retry_metrics_api():
    from retry_metrics import get_retry_metrics
    return jsonify(get_retry_metrics())
```

**前端展示：**
- 重试恢复率（目标 75%+）
- 重试放大量（目标 ≤1.5）
- MTTR（目标 ≤10min）
- Retry Storm 告警次数

---

## ✅ 测试清单（Day 3 必须验证）

### 单元测试（30min）
```bash
# 1. 重试策略配置
python test_retry_config.py

# 2. 重试执行器
python test_retry_executor.py

# 3. Retry Storm 检测
python test_storm_detector.py

# 4. Task Executor 集成
python test_task_executor_integration.py

# 5. 监控指标收集
python test_retry_metrics.py
```

**预期：** 所有测试通过（5/5 全绿）

---

### 端到端测试（20min）
```bash
# 1. 提交 10 个任务（5 个会失败）
python submit_test_tasks.py --count 10 --failure_rate 0.5

# 2. 等待 Heartbeat 执行（最多 5 分钟）
# 观察 task_executions.jsonl

# 3. 检查 SLO 指标
python retry_metrics.py --report

# 预期：
# - 成功率 ≥ 90%（5 个失败任务中至少 4 个重试成功）
# - 重试恢复率 ≥ 75%
# - MTTR ≤ 10min
# - 重试放大量 ≤ 1.5
```

---

### 压力测试（10min）
```bash
# 模拟 Retry Storm（1 分钟内提交 50 个失败任务）
python simulate_retry_storm.py --count 50 --duration 60

# 预期：
# - storm_detector.py 触发告警
# - 重试率 > 1.5
# - Heartbeat 暂停新任务提交
# - 告警推送到 Telegram
```

---

## 📊 Day 3 验收标准

### 功能验收（4/4 全绿）
- ✅ 重试机制上线（timeout/dependency_error 自动重试）
- ✅ Retry Storm 风险前置检查（重试率 > 1.5 触发告警）
- ✅ 监控指标收集（retry_metrics.py 正常输出）
- ✅ Dashboard 可视化（重试指标实时展示）

### SLO 验收（4/4 达标）
- ✅ 成功率 ≥ 90%（从 80.4% 提升到 90%+）
- ✅ 重试恢复率 ≥ 75%（失败任务中 75%+ 重试成功）
- ✅ MTTR ≤ 10min（平均恢复时间 ≤ 600s）
- ✅ 重试放大量 ≤ 1.5（retry_rate ≤ 1.5）

### 风险验收（2/2 通过）
- ✅ Retry Storm 检测正常（压力测试触发告警）
- ✅ 重试执行率 = 0（保持硬约束，不要放宽）

---

## 🚀 执行计划

**总时间：** 2 小时（实现 1.5h + 测试 0.5h）

**顺序：**
1. 重试策略配置（15min）
2. 重试执行器（30min）
3. Retry Storm 检测（20min）
4. Task Executor 集成（15min）
5. 监控指标收集（10min）
6. Heartbeat 集成（5min）
7. Dashboard 可视化（10min）
8. 单元测试（30min）
9. 端到端测试（20min）
10. 压力测试（10min）

**完成后：**
- 生成 Day 3 验收报告（D7_DAY3_REPORT.md）
- 推送到 Telegram（包含 SLO 指标截图）
- 进入 Day 4 观察期（2026-03-07 ~ 2026-03-09）

---

**版本：** v1.0  
**创建时间：** 2026-03-06 19:15  
**维护者：** 小九 + 珊瑚海
