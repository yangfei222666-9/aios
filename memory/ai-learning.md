# AI 学习计划 - 珊瑚海

> 创建日期：2025-07-15
> 最后更新：2025-07-15
> 状态：🟢 进行中

---

## 当前水平评估

### 已掌握 ✅
- Python 工程能力扎实（AIOS 项目 100+ 文件，架构清晰）
- 事件驱动架构设计（EventBus / Pub-Sub 模式）
- 状态机设计（Agent StateMachine）
- 熔断器 / 断路器模式（circuit_breaker.py）
- 基于规则的决策系统（Scheduler / Reactor / Playbook 匹配）
- 指数衰减权重（analyze.py 中的时间衰减函数 `e^(-λΔt)`）
- 模糊匹配算法（Jaccard 相似度，三层匹配策略）
- A/B 测试框架设计（evolution_ab_test.py）
- 基本的模型路由概念（model_router.py，按任务复杂度分流）
- Whisper 语音识别部署（large-v3 + faster-whisper + GPU fp16/int8）
- PyTorch 环境已就绪（2.10.0 + CUDA 12.8 + RTX 5070 Ti）

### 待加强 🔧
- 机器学习理论基础（损失函数、梯度下降、正则化、交叉验证等）
- 神经网络原理（反向传播、激活函数、优化器的数学推导）
- 深度学习模型实现（CNN / RNN / Transformer 从零实现）
- 注意力机制与 Transformer 架构深入理解
- LLM 原理（tokenization、预训练、微调、RLHF、推理优化）
- 向量数据库与 Embedding（RAG 系统）
- Agent 框架理论（ReAct、CoT、Tool Use、Planning）
- 强化学习基础（可用于游戏 AI / AIOS 自动调参）
- 模型训练与微调实操

### 独特优势 🎯
- 有真实的 Agent 系统项目（AIOS），学到的知识可以立刻应用
- 有游戏开发背景，强化学习可以结合游戏 AI
- 硬件配置强（RTX 5070 Ti），可以本地跑中等规模模型
- 工程能力强，理论补上后可以快速落地

---

## 3 个月路线图

### 第 1-4 周：机器学习基础

#### 第 1 周：Python 数学基础 + ML 概览
- 主题：NumPy 矩阵运算、线性代数复习、ML 全景图
- 项目：用纯 NumPy 实现线性回归（梯度下降法）
- 资源：
  - 3Blue1Brown《线性代数的本质》系列（B站有中文字幕）
  - Andrew Ng Machine Learning Specialization（Coursera，第1周）
  - 《动手学深度学习》第2章：预备知识

#### 第 2 周：监督学习核心
- 主题：损失函数、梯度下降、逻辑回归、决策树、过拟合与正则化
- 项目：用 scikit-learn 做一个分类器（可以用 AIOS 的事件数据做异常检测）
- 资源：
  - Andrew Ng ML Specialization 第2-3周
  - scikit-learn 官方教程
  - StatQuest YouTube 频道（直觉讲解）

#### 第 3 周：模型评估与特征工程
- 主题：交叉验证、混淆矩阵、ROC/AUC、特征选择、数据预处理
- 项目：用 AIOS events.jsonl 数据训练一个"错误预测模型"
- 资源：
  - Kaggle Learn 系列（Intro to ML + Intermediate ML）
  - 《Hands-On Machine Learning》第2-3章

#### 第 4 周：无监督学习 + ML 总结
- 主题：K-Means、PCA、聚类评估、降维可视化
- 项目：对 AIOS Agent 行为数据做聚类分析，发现行为模式
- 资源：
  - Andrew Ng ML Specialization 无监督学习部分
  - scikit-learn 聚类教程

### 第 5-8 周：深度学习

#### 第 5 周：神经网络基础
- 主题：感知机、多层网络、反向传播、激活函数、PyTorch 入门
- 项目：用 PyTorch 从零实现一个 MNIST 手写数字分类器
- 资源：
  - 3Blue1Brown《神经网络》系列
  - 《动手学深度学习》(d2l.ai) 第3-4章
  - PyTorch 官方 60 分钟入门教程

#### 第 6 周：CNN 与计算机视觉
- 主题：卷积、池化、经典架构（LeNet → ResNet）、迁移学习
- 项目：用 PyTorch 训练一个游戏截图分类器（识别 LOL 不同游戏阶段）
- 资源：
  - d2l.ai 第6-7章
  - CS231n 课程笔记
  - torchvision 预训练模型教程

#### 第 7 周：RNN / LSTM / 序列模型
- 主题：循环网络、LSTM、GRU、序列建模、时间序列预测
- 项目：用 LSTM 预测 AIOS 系统资源使用趋势（CPU/内存时序数据）
- 资源：
  - d2l.ai 第8-9章
  - Andrej Karpathy《The Unreasonable Effectiveness of RNNs》
  - colah's blog: Understanding LSTM Networks

#### 第 8 周：Transformer 架构（重点！）
- 主题：Self-Attention、Multi-Head Attention、位置编码、Encoder-Decoder
- 项目：从零实现一个简化版 Transformer（参考 Annotated Transformer）
- 资源：
  - 论文：《Attention Is All You Need》（精读）
  - Jay Alammar: The Illustrated Transformer
  - d2l.ai 第10-11章
  - Andrej Karpathy: Let's build GPT from scratch

### 第 9-12 周：LLM 与 Agent 系统

#### 第 9 周：LLM 原理
- 主题：Tokenization（BPE）、预训练目标、Scaling Laws、涌现能力
- 项目：用 nanoGPT 训练一个小型语言模型（用 AIOS 日志数据）
- 资源：
  - Andrej Karpathy: Let's build GPT from scratch（YouTube）
  - 论文：GPT-1/2/3 系列（重点读 GPT-2）
  - Lilian Weng: Large Language Model (blog)

#### 第 10 周：微调与对齐
- 主题：SFT、RLHF、DPO、LoRA/QLoRA、Prompt Engineering 进阶
- 项目：用 LoRA 微调一个小模型，让它学会 AIOS 的 Playbook 格式
- 资源：
  - HuggingFace PEFT 教程
  - 论文：LoRA、InstructGPT
  - Sebastian Raschka: Build a LLM from Scratch（书）

#### 第 11 周：RAG 与向量数据库
- 主题：Embedding 原理、向量检索、RAG 架构、Chunking 策略
- 项目：为 AIOS 构建 RAG 系统（用 lessons.jsonl + events 做知识库检索）
- 资源：
  - LangChain RAG 教程
  - ChromaDB / FAISS 入门
  - 论文：Retrieval-Augmented Generation

#### 第 12 周：Agent 系统理论与实践
- 主题：ReAct、CoT、Tool Use、Planning、Multi-Agent、Memory 系统
- 项目：用学到的知识重构 AIOS Agent System（加入 LLM 驱动的决策层）
- 资源：
  - 论文：ReAct、Toolformer、AutoGPT 架构分析
  - LangChain / LlamaIndex Agent 教程
  - Lilian Weng: LLM Powered Autonomous Agents (blog)
  - Andrew Ng: AI Agentic Design Patterns

---

## 第一周任务

### 学习资源
1. [ ] 看完 3Blue1Brown《线性代数的本质》（B站，约3小时）
2. [ ] 开始 Andrew Ng ML Specialization 第1周（Coursera，约4小时）
3. [ ] 阅读《动手学深度学习》第2章：预备知识（d2l.ai，约2小时）

### 动手项目
4. [ ] 用纯 NumPy 实现线性回归
   - 生成模拟数据（y = 3x + 2 + noise）
   - 实现梯度下降（手动求导）
   - 画出损失曲线和拟合结果
   - 对比 scikit-learn 的 LinearRegression

### 拓展阅读
5. [ ] 阅读 Google Machine Learning Crash Course 概览部分
6. [ ] 浏览 Kaggle 上的入门 Notebook（Titanic 或 House Prices）

### 与 AIOS 结合思考
7. [ ] 思考：AIOS 的 analyze.py 中的指数衰减权重，本质上是什么 ML 概念？
8. [ ] 思考：Reactor 的 Playbook 匹配，能否用 ML 分类器替代规则匹配？

---

## 学习资源库

### 书籍
- 《动手学深度学习》(d2l.ai) - 李沐等 - 免费在线，PyTorch 版 ⭐⭐⭐⭐⭐
- 《Hands-On Machine Learning》- Aurélien Géron - 实战导向 ⭐⭐⭐⭐⭐
- 《Build a Large Language Model from Scratch》- Sebastian Raschka ⭐⭐⭐⭐
- 《Deep Learning》- Goodfellow et al. - 理论深入（选读）⭐⭐⭐

### 在线课程
- Andrew Ng ML Specialization (Coursera) - ML 入门经典 ⭐⭐⭐⭐⭐
- fast.ai Practical Deep Learning - 自顶向下实战 ⭐⭐⭐⭐⭐
- CS231n (Stanford) - 计算机视觉 ⭐⭐⭐⭐
- CS224n (Stanford) - NLP ⭐⭐⭐⭐
- Andrej Karpathy YouTube 系列 - 从零构建 ⭐⭐⭐⭐⭐

### 视频（中文友好）
- 3Blue1Brown 线性代数 / 神经网络系列（B站有字幕）
- 李沐《动手学深度学习》配套视频（B站）
- StatQuest（直觉讲解，英文但很易懂）

### 必读论文
- 《Attention Is All You Need》(2017) - Transformer 原论文
- 《BERT》(2018) - 预训练范式
- 《GPT-2》(2019) - 语言模型 Scaling
- 《LoRA》(2021) - 高效微调
- 《InstructGPT》(2022) - RLHF
- 《ReAct》(2022) - Agent 推理+行动

### 开源项目（学习用）
- nanoGPT (Karpathy) - 最小 GPT 实现
- minGPT (Karpathy) - 教学用 GPT
- llama.cpp - LLM 推理优化
- LangChain / LlamaIndex - Agent 框架
- ChromaDB / FAISS - 向量数据库

---

## 学习进度追踪

| 周次 | 主题 | 状态 | 完成日期 | 笔记 |
|------|------|------|----------|------|
| W1 | Python 数学基础 + ML 概览 | ⬜ 未开始 | - | - |
| W2 | 监督学习核心 | ⬜ 未开始 | - | - |
| W3 | 模型评估与特征工程 | ⬜ 未开始 | - | - |
| W4 | 无监督学习 | ⬜ 未开始 | - | - |
| W5 | 神经网络基础 + PyTorch | ⬜ 未开始 | - | - |
| W6 | CNN 与计算机视觉 | ⬜ 未开始 | - | - |
| W7 | RNN / LSTM / 序列模型 | ⬜ 未开始 | - | - |
| W8 | Transformer 架构 | ⬜ 未开始 | - | - |
| W9 | LLM 原理 | ⬜ 未开始 | - | - |
| W10 | 微调与对齐 | ⬜ 未开始 | - | - |
| W11 | RAG 与向量数据库 | ⬜ 未开始 | - | - |
| W12 | Agent 系统理论与实践 | ⬜ 未开始 | - | - |

---

## 学习笔记区

> 每周学完后在这里记录关键收获和疑问

### W1 笔记
（待填写）

---

*这个文件会随着学习进度持续更新。加油珊瑚海！🚀*
