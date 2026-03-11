# Heartbeat Embedding Load Stall Root Cause Analysis

**日期：** 2026-03-11  
**问题：** Heartbeat exit code 1  
**状态：** 排查中

---

## 1. 现象

**错误：** Heartbeat 执行失败，exit code 1

**卡住位置：** Embedding 模型加载阶段

**日志片段：**
```
Loading weights:   0%|          | 0/103 [00:00<?, ?it/s]
Loading weights:   1%|          | 1/103 [00:00<?, ?it/s, Materializing param=embeddings.LayerNorm.bias]
Loading weights:   2%|▏        | 2/103 [00:00<00:00, 2490.68it/s, Materializing param=embeddings.LayerNorm.weight]
Loading weights:   3%|▎        | 3/103 [00:00<00:00, 2296.99it/s, Materializing param=embeddings.position_embeddings.weight]
Loading weights:   4%|▍        | 4/103 [00:00<00:00, 3062.65it/s, Materializing param=embeddings.token_type_embeddings.weight]
Loading weights:   5%|▌        | 5/103 [00:00<00:00, 2761.95it/s, Materializing param=embeddings.word_embeddings.weight]
```

**进程状态：** 卡在 5/103 权重加载后退出

---

## 2. 排除项

### ✅ learning_agents.py 正常

**验证结果：**
- 语法检查：通过
- 导入检查：通过
- 字段完整性：通过
- JSON 序列化：通过

**结论：** 问题不在 Agent 配置层

---

## 3. 根因方向

**定性：** 依赖阻塞

**具体位置：** Embedding 模型加载卡在 Loading weights

**涉及组件：**
- sentence-transformers
- torch
- all-MiniLM-L6-v2 模型
- Memory Server（如果有）

---

## 4. 排查点

### 4.1 Embedding 模型是否首次冷启动

**检查：** 模型缓存位置

**位置：**
- HuggingFace 缓存：`~/.cache/huggingface/`
- Sentence-transformers 缓存：`~/.cache/torch/sentence_transformers/`

**日志显示：**
```
2026-03-11 09:20:49,501 | INFO | HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/modules.json "HTTP/1.1 307 Temporary Redirect"
```

**判断：** 正在访问 HuggingFace，可能是首次下载或缓存验证

---

### 4.2 本地缓存是否损坏

**待检查：**
- 缓存目录是否存在
- 模型文件是否完整
- 是否有损坏的 checkpoint

---

### 4.3 sentence-transformers / torch 依赖是否卡在权重加载

**日志显示：**
```
Loading weights:   5%|▌        | 5/103 [00:00<00:00, 2761.95it/s, Materializing param=embeddings.word_embeddings.weight]
```

**问题：**
- 加载到 5/103 后卡住
- 没有继续加载后续权重
- 进程直接退出（exit code 1）

**可能原因：**
1. 内存不足（OOM）
2. CUDA 初始化失败
3. 权重文件损坏
4. 超时未设置

---

### 4.4 Memory Server 是否把模型加载放在同步阻塞路径里

**待检查：**
- Memory Server 是否在 heartbeat 启动时同步加载模型
- 是否有超时保护
- 是否有 fallback 路径

---

## 5. 影响范围

### ✅ 当前文档任务未受影响

**Docs_Unified_Writer：** running（正在执行）

**原因：** 任务在 heartbeat 失败前已经启动

### ❌ Heartbeat 不能正常跑

**影响：**
- 无法触发新的定时任务
- 无法执行剩余 3 个 smoke test 任务
- 系统健康检查中断

---

## 6. 下一步排查项

### 6.1 检查缓存

```bash
# 检查 HuggingFace 缓存
ls ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/

# 检查 Sentence-transformers 缓存
ls ~/.cache/torch/sentence_transformers/
```

### 6.2 检查依赖版本

```bash
pip show sentence-transformers torch
```

### 6.3 检查 CUDA 状态

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
```

### 6.4 检查 Memory Server 启动方式

- 是否在 heartbeat 中同步启动
- 是否有独立进程
- 是否有超时设置

---

## 7. 处理策略

### A. 短期：Degraded Mode

**目标：** 让 heartbeat 支持降级模式

**方案：**
- Embedding 没准备好时，不要整轮直接失败
- 先跳过 Memory 相关检查
- 其他健康检查继续跑

**实施：**
```python
try:
    # 加载 embedding 模型
    load_embedding_model()
except Exception as e:
    logger.warning(f"Embedding model load failed: {e}")
    # 继续执行其他检查
    pass
```

### B. 中期：拆分加载路径

**目标：** 把 embedding 模型加载从 heartbeat 主路径里拆出来

**方案：**
1. 预热加载（启动时异步加载）
2. 单独初始化（独立进程）
3. 启动时缓存检查（快速失败）

**实施：**
- 在 Memory Server 启动时预加载模型
- Heartbeat 只检查 Memory Server 状态，不直接加载模型

### C. 长期：增强 Memory Server

**目标：** 给 Memory Server 增加健壮性

**方案：**
1. 模型加载状态（ready / loading / failed）
2. 超时保护（加载超过 30s 自动失败）
3. Fallback 路径（加载失败时使用简单 embedding）

---

## 8. 临时解决方案

### 方案 1：跳过 Memory 检查

**修改 heartbeat_v5.py：**
```python
# 临时跳过 Memory 相关检查
SKIP_MEMORY_CHECK = True

if not SKIP_MEMORY_CHECK:
    # Memory 相关检查
    pass
```

### 方案 2：使用独立 Memory Server

**启动独立 Memory Server：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python memory_server.py &
```

**Heartbeat 只检查连接：**
```python
# 检查 Memory Server 是否可用
response = requests.get("http://localhost:7788/status", timeout=5)
```

---

## 9. 验证步骤

### 9.1 等待当前任务完成

- Docs_Unified_Writer 继续跑
- 不动环境

### 9.2 检查缓存和依赖

- 运行排查脚本
- 确认根因

### 9.3 应用临时方案

- 跳过 Memory 检查或使用独立 Memory Server
- 重新运行 heartbeat

### 9.4 验证剩余 smoke test

- 触发剩余 3 个文档 Agent 任务
- 观察执行结果

---

## 10. 总结

### 问题定性

**类型：** 依赖阻塞  
**层级：** Memory Server / sentence-transformers 启动链  
**不是：** 业务逻辑错、Agent 配置错

### 影响

**✅ 文档任务拆分成功** - learning_agents.py 正常  
**❌ Heartbeat 被阻塞** - embedding 加载卡住

### 下一步

1. 等待 Docs_Unified_Writer 完成
2. 检查缓存和依赖
3. 应用临时方案（跳过 Memory 或独立 Memory Server）
4. 重新运行 heartbeat
5. 完成剩余 3 个 smoke test

---

**报告生成时间：** 2026-03-11 09:29  
**分析人：** 小九  
**状态：** 排查中，等待进一步验证
