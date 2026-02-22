# NEXT_STEPS.md — AIOS 收口计划

来源：珊瑚海 2026-02-22 11:13 确认

## 发布路线
- v0.5.1（安全+稳定热修）→ v0.6.0（结构治理）
- 每次发布带"风险变更说明 + 回滚点"

## P0 Day-1：安全补丁
- [ ] sensors.py 命令注入修复
  - 命令白名单 + 参数校验 + 禁 shell=True
  - 补恶意输入测试
  - 加审计日志字段（谁触发、被拦截原因）

## P0 Day-1/2：OOM 修复
- [ ] engine.py load_events 流式加载
  - 分块读取 + 上限保护 + 超大输入提前中止
  - 加内存上界回归测试
  - 确认不再峰值爆涨

## P1：包结构 + 异常处理 + 并发安全
- [ ] 补 pyproject.toml，逐步移除 sys.path.insert
- [ ] 清理 bare except → 具体异常类型
- [ ] 关键共享状态加锁（dispatcher trace_id → contextvars）
- [ ] sensors.py 状态文件原子写入（临时文件 + os.replace）

## P2：结构治理
- [ ] 拆 analyze.py（输入层/分析层/输出层）
- [ ] 解决同名模块（core/orchestrator vs collaboration/orchestrator）
- [ ] 清理隐式循环依赖（engine ↔ learning）

## 管理面（周度指标）
- [ ] 固定三项周度指标：degraded_rate / agent_failure_by_type / p95_task_latency
- [ ] Collaboration Layer SLO：
  - 完整交付率 ≥ 95%
  - 降级交付率 ≥ 99%
  - 超时中止 ≤ 2%
- [ ] Top18 问题挂看板，绑 owner + deadline
