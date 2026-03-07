# Adversarial Validation System v1.0 - 集成指南

## 🚀 30秒快速集成

### 1. 在高风险决策点调用

在任何需要辩论的地方（如 coder-dispatcher、重构任务、生产部署）：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents" / "adversarial_validator"))

from adversarial_validator import run_adversarial_validation, should_validate

# 判断是否需要辩论
if should_validate(task_description, risk_level="high"):
    result = run_adversarial_validation(
        task_id=task_id,
        task_description=task_description,
        context={"priority": "high", "affected_modules": ["scheduler"]},
        risk_level="high"
    )
    
    # 使用调解后的方案
    final_plan = result["reconciled_plan"]
    final_confidence = result["final_confidence"]
    
    print(f"[ADVERSARIAL] 辩论完成，置信度: {final_confidence:.2f}%")
    print(f"[PLAN] {final_plan}")
```

### 2. Heartbeat 自动生成报告

已集成到 `heartbeat_v5.py`，每小时整点自动生成报告。

### 3. 手动触发辩论

```bash
cd C:\Users\A\.openclaw\workspace\agents\adversarial_validator
python adversarial_validator.py
```

### 4. 查看报告

```bash
# 生成报告
python validation_dashboard.py

# 查看报告
cat C:\Users\A\.openclaw\workspace\aios\reports\adversarial_validation_report.md
```

## 📊 核心功能

### Bull 辩手（支持方）
- 自动识别任务优势
- 基于 Evolution Score 生成支持论据
- 结合卦象智慧提供建议

### Bear 辩手（反对方）
- 自动识别风险点
- 基于风险系数评估危险程度
- 提供风险管控建议

### 64卦调解
- 根据当前卦象（大过卦/坤卦/乾卦等）调解
- 风险系数自动调整（<1.0=低风险，>1.0=高风险）
- 生成融合方案

## 🎯 触发条件

自动触发（`should_validate` 返回 True）：
- `risk_level="high"` 的任务
- 包含高风险关键词：重构、删除、迁移、生产、部署、回滚、清理、覆盖
- Evolution Score < 92.0

## 📈 预期效果

- 关键决策失败率降低 30%+
- Evolution Score 每次辩论 +0.4
- Phase 3 自动记录辩论结果
- 每小时自动生成可视化报告

## 🔧 自定义

### 添加新卦象

编辑 `adversarial_validator.py` 中的 `HEXAGRAM_WISDOM`：

```python
HEXAGRAM_WISDOM = {
    "新卦名": {
        "no": 卦序号,
        "judgment": "卦辞",
        "advice": "调解建议",
        "risk_modifier": 0.8  # <1.0=低风险，>1.0=高风险
    }
}
```

### 自定义 Bull/Bear 论据

修改 `bull_argue()` 和 `bear_argue()` 函数。

## 📝 示例输出

```
[ADVERSARIAL] 启动辩论: adv-test-001
  卦象: 坤卦 | Evolution Score: 94.86
  [BULL] 代码质量提升将带来长期维护成本降低 30%+...
  [BEAR] 重构引入回归风险，需完整测试覆盖...
  [OK] 调解完成 | 最终置信度: 95.26

【坤卦调解方案】
卦辞：元亨，利牝马之贞。
执行方案：
1. 全力推进，同时保留快速回滚能力
2. Bull核心论点采纳：代码质量提升...
3. Bear风险管控：重构引入回归风险...
```

---

**维护者:** 小九 + 珊瑚海 🐾  
**版本:** v1.0  
**日期:** 2026-03-05
