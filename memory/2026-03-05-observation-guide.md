# 观察技巧指南（珊瑚海 2026-03-05 14:20 传授）

## 组合信号（核心）

### 组合 A — 系统健康
- success_rate 稳定 + debate_rate 稳定 + fast_ratio 稳定 + latency 稳定
- 判定：system_state = stable

### 组合 B — 复杂任务增加（正常自适应）
- debate_rate ↑ + fast_ratio ↓ + latency ↑
- 判定：系统自动进入防御模式，slow model 使用增加

### 组合 C — 潜在问题（Phase4 重点）
- success_rate ↓ + regen_rate ↑ + latency ↑
- 判定：系统频繁自愈，某类 failure 在增加

## 稳定持续时间
- 不只看数值，看连续几天是否一致
- Day3/Day4/Day5 连续 stable = system rhythm 已形成
- 比单日数据更重要

## Pattern Emergence
- Day5 左右样本量跨过统计阈值
- 之前看不出规律，突然一切清楚
- Day5 是关键时间点

## Failure Concentration（Day5+ 使用）
- 公式：Top1_failure / Total_failures
- >50% → 优化 Top1 就能明显提升系统
- 这是 Phase4 核心逻辑

## Hexagram 专项指标（珊瑚海 2026-03-05 15:21 补充）

### hexagram_change_rate（系统活动度）
- 公式：change_rate = changes / records
- <0.15 → 系统太静态
- 0.20–0.30 → 正常运行
- >0.40 → 系统震荡

### transition shape（比 distribution 更重要）
- 健康形态：坤→坤 / 坤→兑 / 兑→震 / 震→兑 / 兑→坤（缓慢波动）
- 异常形态：坤→坎 / 坎→离 / 离→坎（system oscillation）

### self_transition_ratio（50+ records 后使用）
- 公式：(坤→坤 + 兑→兑 + 震→震 + ...) / total_transitions
- <0.30 → 变化太频繁
- 0.40–0.60 → 正常
- >0.70 → 过于僵化

### Day3 健康预期
- records ≈ 90
- 坤 48–55% / 兑 15–20% / 震 8–12%
- entropy 1.1–1.4
- change_rate 0.22–0.28

## Day3 完整 Observation 结构
- records
- dominant_hexagram
- dominant_transition
- entropy
- transition_entropy
- change_rate
- stability_index
- self_transition_ratio（新增）

## 当前任务
- 纯观察，不调任何东西
- 每天 22:00 生成 observation 发给珊瑚海
- 系统正在自己收敛
