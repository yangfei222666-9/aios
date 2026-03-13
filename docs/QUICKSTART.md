# 太极OS 快速入门

## 太极OS 是什么

太极OS 是一个以"自我进化"为核心的个人 AI 操作系统，由 AI Agent 协作驱动，能够自动执行任务、积累经验并持续改进。它不是一个传统的操作系统，而是一套运行在你机器上的智能 Agent 调度与学习框架，目标是让 AI 真正"跑起来"并越用越聪明。

---

## 核心特性

- **自我改进闭环** — 通过 7 步闭环（执行→记录→分析→生成→应用→验证→更新）让 Agent 从失败中自动学习并优化行为。
- **自动回滚保护** — 改进效果变差时自动回滚，成功率下降 >10% 或连续失败 ≥5 次即触发，保护生产稳定性。
- **自适应阈值** — 根据 Agent 运行频率和重要性动态调整触发条件，高频 Agent 和关键 Agent 有独立策略。
- **可观测性优先** — 所有任务执行均有状态记录、日志追踪和历史复盘，系统健康度实时可见。
- **文件即记忆** — 通过 `MEMORY.md`、每日日志和 `lessons.json` 实现跨会话的持久化记忆与经验积累。

---

## 快速开始

### 第 1 步：克隆并安装

```bash
git clone https://github.com/yangfei222666-9/self-improving-loop.git
cd self-improving-loop
pip install -e .
```

验证安装：

```bash
python -c "from self_improving_loop import SelfImprovingLoop; print('安装成功')"
```

### 第 2 步：包装你的第一个 Agent 任务

```python
from self_improving_loop import SelfImprovingLoop

loop = SelfImprovingLoop(data_dir="./data")

result = loop.execute_with_improvement(
    agent_id="my-first-agent",
    task="处理数据",
    execute_fn=lambda: {"status": "ok", "value": 42}
)

print(f"成功: {result['success']}, 耗时: {result['duration_sec']:.2f}s")
```

### 第 3 步：查看 Agent 运行统计

```python
stats = loop.get_improvement_stats("my-first-agent")
print(f"成功率: {stats['agent_stats']['success_rate']:.1%}")
print(f"已触发改进: {stats.get('rollback_count', 0)} 次回滚")
```

### 第 4 步：运行测试，确认系统正常

```bash
python -m pytest tests/
```

### 第 5 步：接入 Telegram 通知（可选）

```python
from self_improving_loop.notifier import TelegramNotifier

notifier = TelegramNotifier(bot_token="YOUR_TOKEN", chat_id="YOUR_CHAT_ID")
loop = SelfImprovingLoop(notifier=notifier)
```

---

## 常见问题

**Q：什么时候会触发自动改进？**
当 Agent 在 6 小时内失败次数达到阈值（默认 3 次）且冷却期（默认 1 小时）已过时触发。关键 Agent 阈值更低，仅需 1 次失败即触发。

**Q：改进会不会把系统搞坏？**
不会。只有低风险改进（如增加超时、添加重试）会自动应用，高风险改进需人工确认。改进后若效果变差，自动回滚机制会在 ~10ms 内恢复原状。

**Q：Agent 的记忆如何跨会话保留？**
太极OS 使用文件作为持久化记忆：`MEMORY.md` 存储长期经验，`memory/YYYY-MM-DD.md` 记录每日日志，`memory/lessons.json` 积累可复用规则。每次启动时读取这些文件即可恢复上下文。
