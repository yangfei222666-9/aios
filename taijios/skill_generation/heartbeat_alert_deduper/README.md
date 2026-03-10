# heartbeat_alert_deduper

**版本：** 0.1.0  
**状态：** validated (已通过三层验证)  
**风险级别：** low

## 功能

从 Heartbeat 文本中抽取候选告警，按去重规则与隔离模块规则自动分类为：
- 新告警
- 已抑制旧告警
- 已知隔离问题
- 非告警信号

输出结构化结果与是否需要通知的判断。

## 特点

- **只读操作** - 不修改系统配置，不触发通知
- **规则驱动** - 基于明确规则，不依赖模糊推断
- **可回放验证** - 支持历史样本测试
- **低风险** - 只写自己的结果文件

## 使用方式

### 命令行

```bash
cd C:\Users\A\.openclaw\workspace\taijios\skill_generation\heartbeat_alert_deduper
python deduper.py tests/test_samples/sample1_old_alerts.txt
```

### Python API

```python
from deduper import HeartbeatAlertDeduper

deduper = HeartbeatAlertDeduper()
result = deduper.run(heartbeat_text)

print(f"New alerts: {result['summary']['new_alerts']}")
print(f"Suppressed: {result['summary']['suppressed_old_alerts']}")
print(f"Notify count: {result['summary']['notify_count']}")
```

## 输出示例

```json
{
  "run_id": "deduper-2026-03-09T10:00:00+08:00",
  "parsed_alerts_count": 4,
  "results": [
    {
      "alert_key": "skill:api-testing-skill:network_error:ERROR",
      "category": "suppressed_old_alert",
      "should_notify": false,
      "reason": "previously_reported_no_change",
      "evidence": {
        "severity": "ERROR",
        "error_type": "network_error",
        "failure_count": 3
      }
    }
  ],
  "summary": {
    "new_alerts": 0,
    "suppressed_old_alerts": 3,
    "quarantined_known_issues": 1,
    "notify_count": 0
  }
}
```

## 验证结果

**三层验证：** 11/11 通过 (100%)

- ✅ V1: 语法验证
- ✅ V2: 行为验证
- ✅ V3: 风险验证

## 配置文件

### memory/known_alerts.json
历史告警记录

### memory/quarantined_modules.json
隔离模块列表

### memory/dedup_rules.json
去重规则配置

## 测试

```bash
cd tests
python test_deduper.py
```

## 下一步

1. 在真实 heartbeat 输出上试运行
2. 收集反馈数据
3. 记录到 skill_feedback.jsonl
4. 根据反馈调整规则

## 太极OS 集成

- **Reality Ledger**: 记录完整生命周期
- **Evolution Score**: 预留指标接口
- **易经状态引擎**: 门控设计/试运行/生产阶段

---

**创建时间：** 2026-03-09  
**作者：** taijios_skill_generator  
**MVP 规格书存档 ID：** 9x1dxh
