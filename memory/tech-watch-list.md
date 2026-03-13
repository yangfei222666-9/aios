# 技术观察清单

**用途：** 记录拆解过的开源项目，快速查阅借鉴价值

**更新频率：** 每拆一个项目就追加一条

---

## 记录格式

每个项目按以下格式记录：

```
### [项目名] - [日期]

**一句话判断：** 

**最值得借的 3 点：**
1. 
2. 
3. 

**最不能抄的 3 点：**
1. 
2. 
3. 

**下一步动作：**
- [ ] 

**详细报告：** memory/YYYY-MM-DD-[项目名]-analysis.md
```

---

## 已拆解项目

### Macrohard (Tesla/xAI) - 2026-03-11

**一句话判断：** Grok 做 planner/navigator (System 2)，Tesla Agent 负责 real-time screen + kbm 执行 (System 1)，目标模拟完整软件公司

**最值得借的 3 点：**
1. 屏幕理解 → 任务规划 → 执行分离的架构
2. System 1 (快速执行) + System 2 (深度规划) 双系统设计
3. 真实软件公司流程的模拟（PM → 工程师 → QA）

**最不能抄的 3 点：**
1. 依赖 Tesla 的屏幕理解能力（太极OS 暂无）
2. 需要大量算力支撑（Grok 级别）
3. 执行层挑战巨大（如何保证可靠性）

**下一步动作：**
- [x] 持续观察 Macrohard 的执行层实现
- [ ] 评估太极OS是否需要类似的 System 1/2 分离
- [ ] 关注 Tesla Agent 的开源进展

**详细报告：** memory/tech-watch-list.md（内部诊断记录）

---

## 待拆解项目

### Paperclip - 待定

**状态：** 任务已下发，等待拆解报告

**GitHub：** 待补充

**关注点：**
- orchestration / scheduler
- task / state
- approval / retry / pending / blocked
- memory / trace / audit / dashboard

---

**版本：** v1.0  
**创建时间：** 2026-03-13  
**维护者：** 小九 + 珊瑚海
