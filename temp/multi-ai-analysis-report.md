# 三AI协同系统分析报告

**分析时间：** 2026-03-13 18:23  
**分析对象：** 多AI协同-多文件拆分版  
**分析人：** 小九 + 珊瑚海

---

## 📊 系统定性

**不是"真正的多智能体系统"，而是"多模型流水线编排器"**

- 本质：有序的 API 调用链
- 核心：豆包做调度中心，DeepSeek/GLM 按固定顺序执行
- 价值：只要调度层做稳，实用价值很高

---

## 🎯 核心架构

### 三AI分工模型
- **豆包 1.8** - 总调度 + 上下文管家 + 代码整合
- **DeepSeek V3.2** - 后端逻辑/算法/数据处理（禁止写前端）
- **GLM-4.7** - 前端 UI/样式/暗黑模式（禁止写后端）

### 两阶段工作流
1. **讨论阶段** - 三个模型轮流发言，形成共识（2-10轮可调）
2. **制作阶段** - 调度 DS/GLM 输出代码，支持插队指令（1-100轮）

### 代码打包规范
```
=== filename: index.html ===
=== filename: css/style.css ===
=== filename: js/script.js ===
=== filename: backend/app.js ===
```

---

## ⚠️ 最大风险：调度层失控

**不是三AI分工本身的问题，而是：**
1. **上下文越来越长** - 每轮都把全量历史传给豆包，25轮后可能爆炸
2. **状态越来越乱** - 没有持久化，刷新页面全丢
3. **失败后没法续跑** - 某个模型调用失败，整个流程卡住

---

## 🔧 必须先补的三个基础件

### 1. 状态持久化（P0）
**当前问题：**
- 刷新页面 → 所有状态丢失
- 浏览器崩溃 → 25轮工作白做

**必须持久化的状态：**
```javascript
{
  "phase": "production",           // 当前阶段
  "discussionCurrent": 3,          // 讨论进度
  "productionCurrent": 12,         // 制作进度
  "consensusJSON": {...},          // 讨论共识
  "files": {                       // 各文件最新版本
    "index.html": "...",
    "css/style.css": "..."
  },
  "conversationHistory": [...]     // 对话历史（压缩后）
}
```

**实现方案：**
- 每轮结束后自动保存到 `localStorage`
- 提供"恢复上次会话"按钮
- 支持导出/导入状态文件（JSON）

---

### 2. 失败恢复（P0）
**当前问题：**
- API 调用失败 → 整个流程卡住
- 没有重试机制
- 没有跳过机制
- 没有手动续跑

**必须实现的能力：**
```javascript
// 单模型失败 → 自动重试 3 次
async callWithRetry(model, messages, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await this.callAPI(model, messages);
    } catch (err) {
      if (i === maxRetries - 1) {
        // 最后一次失败 → 记录错误，提供选项
        return {
          error: true,
          message: err.message,
          options: ['重试', '跳过', '手动输入']
        };
      }
      await sleep(2000 * (i + 1)); // 指数退避
    }
  }
}
```

**UI 层面：**
- 失败时弹出对话框：`[重试] [跳过] [手动输入] [停止]`
- 提供"从第 X 轮继续"功能
- 显示失败原因和重试次数

---

### 3. 上下文压缩（P0）
**当前问题：**
- 讨论 5 轮 + 制作 20 轮 = 25 轮全量历史
- 豆包每次都要处理几万 token
- 后期响应越来越慢，成本越来越高

**必须实现的策略：**

#### 讨论阶段 → 制作阶段
```javascript
// 讨论结束后，生成"共识文档"
const consensus = await this.callDoubao([
  {role: 'system', content: '总结讨论共识，输出JSON'},
  ...discussionHistory
]);

// 制作阶段只传共识，不传讨论历史
const productionContext = [
  {role: 'system', content: DOUBAO_ROLE_PROMPT},
  {role: 'user', content: `项目需求：${userInput}`},
  {role: 'assistant', content: `讨论共识：${consensus}`}
];
```

#### 制作阶段内部压缩
```javascript
// 每 5 轮摘要一次
if (productionCurrent % 5 === 0) {
  const summary = await this.callDoubao([
    {role: 'system', content: '摘要最近5轮的关键决策和代码变更'},
    ...recentHistory
  ]);
  
  // 替换最近5轮为摘要
  productionHistory = [
    ...productionHistory.slice(0, -5),
    {role: 'assistant', content: `[摘要] ${summary}`}
  ];
}
```

#### 只保留关键信息
```javascript
// 不需要保留的内容
- 调度过程（"正在调用 DeepSeek..."）
- 重复的系统提示词
- 已经整合到最终代码的中间版本

// 必须保留的内容
- 用户需求
- 讨论共识
- 插队指令
- 最终代码
```

---

## 📋 推荐优先级

### Phase 1：基础稳定性（1-2天）
1. ✅ 状态持久化（localStorage + 导出/导入）
2. ✅ 失败重试机制（3次重试 + 手动选项）
3. ✅ 上下文压缩（讨论→共识，制作每5轮摘要）

### Phase 2：错误恢复（1天）
4. ✅ 断点续跑（从第 X 轮继续）
5. ✅ 手动干预（失败时手动输入内容）
6. ✅ 错误日志（记录所有失败和重试）

### Phase 3：体验优化（1-2天）
7. ✅ 版本快照（每轮保存，支持回退）
8. ✅ 插队指令增强（支持复杂指令解析）
9. ✅ 代码提取容错（支持多种格式）

### Phase 4：高级功能（可选）
10. 🔲 集成到太极OS（作为 Skill）
11. 🔲 动态调度（根据任务类型选模型）
12. 🔲 学习反馈（记录有效提示词）

---

## 💡 可借鉴到太极OS的模式

### 1. 硬约束提示词
```python
# 太极OS 的 Agent 也可以加"禁止清单"
CODER_DISPATCHER_CONSTRAINTS = """
禁止清单：
1. 禁止修改 AIOS 核心文件（events.db, agents.json）
2. 禁止执行 rm -rf / 等危险命令
3. 禁止脑补需求，只实现 task_queue 里的任务
4. 禁止过度封装，保持代码简洁
"""
```

### 2. 插队机制
```python
# 太极OS 可以加"紧急任务"
# 用户发送 "!urgent 修复 memory_server.py 的内存泄漏"
# 系统立即暂停当前任务，插入紧急任务
task_queue.insert(0, {
    "type": "urgent",
    "priority": 999,
    "task": "修复 memory_server.py 的内存泄漏"
})
```

### 3. 阶段性摘要
```python
# 太极OS 的 Learning Loop 可以加"阶段摘要"
# 每完成 5 个任务，生成摘要
if len(completed_tasks) % 5 == 0:
    summary = generate_summary(completed_tasks[-5:])
    lessons.append({
        "type": "batch_summary",
        "tasks": completed_tasks[-5:],
        "summary": summary
    })
```

### 4. 状态快照
```python
# 太极OS 可以加"改进历史"
# 每次 Self-Improving Loop 应用改进后
# 保存快照到 memory/snapshots/YYYY-MM-DD-HH-MM.json
snapshot = {
    "timestamp": now(),
    "improvement": improvement,
    "before": read_file(target_file),
    "after": read_file(target_file),
    "metrics": get_metrics()
}
save_snapshot(snapshot)
```

---

## 🎯 最小可落地重构方案（下一步）

如果要推进，建议按以下模块拆分：

### 模块 1：状态管理器（state-manager.js）
```javascript
class StateManager {
  save() { ... }           // 保存到 localStorage
  load() { ... }           // 加载状态
  export() { ... }         // 导出 JSON
  import(json) { ... }     // 导入 JSON
  snapshot() { ... }       // 创建快照
  restore(id) { ... }      // 恢复快照
}
```

### 模块 2：重试管理器（retry-manager.js）
```javascript
class RetryManager {
  async callWithRetry(fn, maxRetries) { ... }
  handleFailure(error) { ... }  // 弹出选项对话框
  skipRound() { ... }           // 跳过当前轮
  manualInput() { ... }         // 手动输入内容
}
```

### 模块 3：上下文压缩器（context-compressor.js）
```javascript
class ContextCompressor {
  generateConsensus(history) { ... }     // 讨论→共识
  summarizeRecent(history, n) { ... }    // 摘要最近N轮
  filterKeyInfo(history) { ... }         // 过滤关键信息
}
```

### 模块 4：调度引擎增强（engine-enhanced.js）
```javascript
class EnhancedEngine extends TripleAIEngine {
  constructor() {
    super();
    this.stateManager = new StateManager();
    this.retryManager = new RetryManager();
    this.compressor = new ContextCompressor();
  }
  
  async runDiscussion() {
    // 每轮后自动保存状态
    // 失败时自动重试
    // 结束时生成共识
  }
  
  async runProduction() {
    // 每5轮摘要一次
    // 失败时提供选项
    // 每轮保存快照
  }
}
```

---

## 📝 总结

**核心判断：**
- 这是一个"多模型流水线编排器"，不是真正的多智能体系统
- 最大风险是"调度层失控"（上下文爆炸、状态混乱、失败卡死）
- 只要补齐三个基础件（状态持久化、失败恢复、上下文压缩），实用价值很高

**推荐路径：**
1. 先补基础件（1-2天）
2. 再补错误恢复（1天）
3. 再做体验优化（1-2天）
4. 最后考虑集成到太极OS

**可借鉴的模式：**
- 硬约束提示词（防加戏）
- 插队机制（紧急任务）
- 阶段性摘要（压缩上下文）
- 状态快照（版本管理）

---

**报告生成：** 小九  
**审核：** 珊瑚海  
**版本：** v1.0
