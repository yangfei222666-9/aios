# LLM Agent 核心知识点

*提取自大模型面试题资料（2026-02-26）*

---

## 一、Agent 核心组件

### 1. Planning（规划）

**任务拆解的 7 种方法：**

1. **Chain of Thought (CoT)** - 逐步思考
   - 让模型 step by step 拆解复杂问题
   - 适合：逻辑推理、数学计算

2. **Tree of Thoughts (ToT)** - 思维树
   - 在每个步骤探索多个可能性
   - 可以回溯和剪枝
   - 适合：需要探索多条路径的问题

3. **任务分解（Task Decomposition）**
   - 将大任务拆成子任务
   - 方法：
     - 直接让 LLM 拆解："Steps for XYZ?\n1."
     - 用特定指令："What are the subgoals for achieving XYZ?"
     - 人工输入任务列表

4. **Graph of Thoughts (GoT)** - 思维图
   - 图结构，支持任意节点间的连接
   - 比 ToT 更灵活
   - 适合：复杂的多步骤推理

5. **LLM+P** - 规划领域定义语言（PDDL）
   - 用 PDDL 描述问题和领域
   - LLM 生成 PDDL Plan
   - 外部 Planner 执行计划
   - 适合：需要形式化规划的场景

6. **ReAct** - Reasoning + Action
   - Thought → Action → Observation 循环
   - 边思考边行动
   - 适合：需要与环境交互的任务

7. **Reflexion** - 反思
   - 从失败中学习
   - 用 Wikipedia Search 等工具验证
   - 适合：需要迭代改进的任务

---

### 2. Self-Reflection（自我反省）

**两种实现方式：**

1. **ReAct 模式**
   - 即时反馈：Action → Observation → Thought
   - 在 LLM 内部完成推理步骤

2. **Reflexion 模式**
   - 延迟反馈：执行完整任务 → 分析失败 → 改进
   - 用外部工具验证（如 Wikipedia Search）

**核心流程：**
```
Thought → Action → Observation → (循环)
```

---

### 3. Memory（记忆）

**三种记忆类型：**

1. **短期记忆（Short-term Memory）**
   - 当前上下文窗口内的信息
   - 受限于模型的 context length

2. **长期记忆（Long-term Memory）**
   - 持久化存储
   - 可以跨会话访问

3. **工作记忆（Working Memory）**
   - 当前任务相关的临时信息
   - 任务结束后清理

---

### 4. Tool Use（工具使用）

**核心能力：**
- Agent 能够调用外部工具（API、数据库、搜索引擎等）
- 根据任务需求选择合适的工具
- 解析工具返回结果并继续推理

---

## 二、多模态 Agent

### 1. CLIP（Contrastive Language-Image Pretraining）
- 对比学习：图像和文本在同一空间对齐
- 用途：图像分类、检索、zero-shot 识别

### 2. DALL-E
- 文本生成图像
- 基于 Transformer 架构

### 3. blip2
- 2023 年提出，图像理解 + 文本生成
- 核心：Q-Former（连接视觉和语言）
- 冻结预训练模型，只训练 Q-Former

---

## 三、Word2Vec 核心技术

### 1. Hierarchical Softmax（分层 Softmax）
- 用 Huffman 树替代传统 Softmax
- 复杂度：O(log N) vs O(N)
- 适合：词表很大的场景

### 2. Negative Sampling（负采样）
- 随机采样负样本（非目标词）
- 只更新少量参数
- 比 Hierarchical Softmax 更快

### 3. 训练技巧
- 高频词降采样
- 动态窗口大小
- 学习率衰减

---

## 四、CV 基础知识

### 1. 归一化 vs 标准化

**归一化（Min-Max Normalization）：**
```
x' = (x - min) / (max - min)
```
- 结果范围：[0, 1]

**标准化（Z-score Normalization）：**
```
z = (x - μ) / σ
```
- 结果：均值 0，标准差 1

### 2. 激活函数

**常用激活函数：**
- Sigmoid：输出 [0, 1]，梯度消失问题
- Tanh：输出 [-1, 1]，比 Sigmoid 好
- ReLU：max(0, x)，最常用
- Leaky ReLU：解决 ReLU 的"死神经元"问题

### 3. 空洞卷积（Atrous Convolution）
- 扩大感受野，不增加参数
- 用途：语义分割、目标检测
- 原理：在卷积核中插入"空洞"

---

## 五、RAG（Retrieval-Augmented Generation）

**核心思路：**
- 检索相关文档 → 增强 LLM 输入 → 生成答案

**优势：**
- 减少幻觉
- 实时更新知识
- 降低训练成本

**关键步骤：**
1. 文档切块（Chunking）
2. 向量化（Embedding）
3. 检索（Retrieval）
4. 生成（Generation）

---

## 六、Agent 系统设计要点

### 1. 模块化设计
- Planning、Memory、Action、Tool Use 分离
- 每个模块可独立升级

### 2. 状态管理
- Agent 状态机（idle → planning → executing → reflecting）
- 状态持久化

### 3. 错误处理
- 熔断机制（连续失败自动停止）
- 自动重试（指数退避）
- 降级策略（失败后用简单方法）

### 4. 可观测性
- 记录所有决策过程
- 性能指标（成功率、耗时、成本）
- 可视化 Dashboard

---

## 七、面试高频问题

### 1. Agent 和普通 LLM 的区别？
- Agent 有自主性（Planning + Action）
- Agent 能使用工具
- Agent 有记忆和反思能力

### 2. 如何设计一个生产级 Agent？
- 模块化架构
- 状态管理
- 错误处理和熔断
- 可观测性
- 成本控制

### 3. Agent 的最大挑战是什么？
- 可靠性（如何保证不出错）
- 成本（LLM 调用成本高）
- 延迟（多步推理很慢）
- 安全性（工具调用的权限控制）

---

*最后更新：2026-02-26*  
*来源：大模型面试题资料*
