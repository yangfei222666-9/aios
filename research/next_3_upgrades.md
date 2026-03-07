# Next 3 Upgrades — 1周内可落地的改进项

> 基于 gap analysis 筛选，只选 3 个，避免分心
> 筛选标准：影响大 × 落地快 × 和现有架构兼容

---

## 候选项评分

| 候选项 | 影响分(1-5) | 落地难度(1-5,低=易) | 兼容性(1-5) | 总分 | 入选 |
|-------|-----------|-------------------|-----------|------|------|
| Token预算控制 | 5 | 2 | 5 | 12 | ✅ |
| 执行回放/审计链 | 4 | 3 | 4 | 11 | ✅ |
| 记忆分层加载(L0/L1/L2) | 4 | 3 | 4 | 11 | ✅ |
| 安全沙箱 | 4 | 5 | 2 | 11 | ❌ 难度太高 |
| 标准化评估 | 3 | 3 | 4 | 10 | ❌ 下期 |
| 渐进式技能加载 | 3 | 2 | 4 | 9 | ❌ 下期 |

---

## 🏆 Upgrade #1: Token Budget Controller

### 问题
当前AIOS没有任何成本控制。一个失控的Agent可以无限消耗token，没有预警、没有熔断。

### 参考
Shannon 的 Token Budget Control：硬预算限制 + 80%时自动切换便宜模型。

### 方案

**文件：** `aios/agent_system/token_budget.py`

**核心逻辑：**
```python
class TokenBudget:
    def __init__(self, max_tokens: int, fallback_model: str = "sonnet"):
        self.max_tokens = max_tokens
        self.used_tokens = 0
        self.fallback_model = fallback_model
        self.threshold = 0.8  # 80%时触发降级
    
    def check(self, estimated_tokens: int) -> dict:
        """返回 {allowed: bool, model_override: str|None, remaining: int}"""
        if self.used_tokens + estimated_tokens > self.max_tokens:
            return {"allowed": False, "reason": "budget_exceeded"}
        
        usage_ratio = self.used_tokens / self.max_tokens
        model_override = self.fallback_model if usage_ratio >= self.threshold else None
        
        return {
            "allowed": True,
            "model_override": model_override,
            "remaining": self.max_tokens - self.used_tokens,
            "usage_pct": round(usage_ratio * 100, 1)
        }
    
    def consume(self, tokens: int):
        self.used_tokens += tokens
```

**集成点：**
1. `task_executor.py` — 每次执行前 check()，执行后 consume()
2. `heartbeat_v5.py` — 每次心跳报告预算使用情况
3. `agents.json` — 每个Agent可配置独立预算
4. Dashboard — 新增预算使用卡片

**配置示例：**
```json
{
  "budget": {
    "daily_max_tokens": 500000,
    "per_task_max_tokens": 50000,
    "fallback_model": "sonnet",
    "alert_threshold": 0.8,
    "hard_stop_threshold": 0.95
  }
}
```

**预期效果：**
- 成本可控：每日/每任务硬上限
- 自动降级：80%预算时切换便宜模型
- 95%预算时硬停止，防止失控
- Dashboard实时显示预算消耗

**工期：** 1-2天

---

## 🏆 Upgrade #2: Execution Replay（执行回放）

### 问题
Agent执行失败时，我们只能看日志猜测原因。无法回放执行过程，无法精确定位失败步骤。

### 参考
Shannon 的 Time-Travel Debugging：可以回放任何执行步骤，逐步查看每个决策、工具调用和状态变化。

### 方案

**文件：** `aios/agent_system/execution_replay.py`

**核心逻辑：**
```python
class ExecutionRecorder:
    """记录每个执行步骤，支持回放"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.steps = []
        self.start_time = datetime.now()
    
    def record_step(self, step_type: str, data: dict):
        """记录一个执行步骤"""
        self.steps.append({
            "seq": len(self.steps),
            "timestamp": datetime.now().isoformat(),
            "type": step_type,  # "decision" | "tool_call" | "state_change" | "error"
            "data": data
        })
    
    def save(self):
        """保存到 execution_traces/{task_id}.jsonl"""
        trace_dir = "execution_traces"
        os.makedirs(trace_dir, exist_ok=True)
        path = f"{trace_dir}/{self.task_id}.jsonl"
        with open(path, "w") as f:
            for step in self.steps:
                f.write(json.dumps(step, ensure_ascii=False) + "\n")
    
    def replay(self, from_step: int = 0, to_step: int = None):
        """回放指定范围的步骤"""
        end = to_step or len(self.steps)
        for step in self.steps[from_step:end]:
            yield step
```

**记录的事件类型：**
```
TASK_STARTED      — 任务开始（输入、Agent、模型）
DECISION_MADE     — Agent做出决策（选择工具/策略）
TOOL_INVOKED      — 工具调用（输入参数）
TOOL_RESULT       — 工具返回（输出结果）
STATE_CHANGED     — 状态变化（Evolution Score、卦象）
ERROR_OCCURRED    — 错误发生（异常信息、堆栈）
BUDGET_WARNING    — 预算警告（与Upgrade #1联动）
TASK_COMPLETED    — 任务完成（结果、耗时、token消耗）
```

**集成点：**
1. `task_executor.py` — 每个关键步骤调用 record_step()
2. `low_success_regeneration.py` — 重生时回放失败轨迹
3. Dashboard — 新增"执行回放"页面
4. CLI — `python replay.py <task_id>` 命令行回放

**预期效果：**
- 任何失败都可以逐步回放
- 重生时可以精确分析失败原因
- 审计链完整，每个决策可追溯
- 和Token Budget联动，记录预算消耗轨迹

**工期：** 2-3天

---

## 🏆 Upgrade #3: Memory Tiered Loading（记忆分层加载）

### 问题
当前记忆系统是扁平的：要么加载全部MEMORY.md（大量token），要么不加载。缺少按需分层加载。

### 参考
OpenViking 的 L0/L1/L2 三层上下文：
- L0（摘要）~100 tokens — 快速判断相关性
- L1（概览）~2k tokens — 理解结构和要点
- L2（完整）— 深度阅读时才加载

### 方案

**文件：** `aios/agent_system/memory_tiered.py`

**核心逻辑：**
```python
class TieredMemory:
    """三层记忆加载系统"""
    
    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir
        self.index = self._build_index()
    
    def _build_index(self):
        """扫描记忆文件，生成L0摘要索引"""
        index = {}
        for f in glob.glob(f"{self.memory_dir}/*.md"):
            content = open(f).read()
            index[f] = {
                "l0": self._generate_l0(content),  # ~100 tokens
                "l1": self._generate_l1(content),  # ~2k tokens
                "l2_path": f                         # 完整内容路径
            }
        return index
    
    def _generate_l0(self, content: str) -> str:
        """生成一句话摘要"""
        # 取第一个标题 + 前100字
        lines = content.split("\n")
        title = next((l for l in lines if l.startswith("#")), "")
        return f"{title} | {content[:200]}..."
    
    def _generate_l1(self, content: str) -> str:
        """生成结构化概览（标题 + 关键点）"""
        lines = content.split("\n")
        headers = [l for l in lines if l.startswith("#")]
        return "\n".join(headers[:20])  # 最多20个标题
    
    def load(self, query: str, level: str = "l1") -> list:
        """根据查询加载相关记忆"""
        results = []
        for path, layers in self.index.items():
            # L0快速筛选
            if self._is_relevant(query, layers["l0"]):
                if level == "l0":
                    results.append({"path": path, "content": layers["l0"]})
                elif level == "l1":
                    results.append({"path": path, "content": layers["l1"]})
                else:  # l2
                    full = open(layers["l2_path"]).read()
                    results.append({"path": path, "content": full})
        return results
```

**加载策略：**
```
1. 心跳/快速检查 → 只加载 L0（~100 tokens/文件）
2. 任务规划 → 加载 L1（~2k tokens/文件）
3. 深度执行 → 按需加载 L2（完整内容）
```

**集成点：**
1. `heartbeat_v5.py` — 心跳时只加载L0，节省token
2. `task_executor.py` — 任务规划时加载L1，执行时按需L2
3. `memory_server.py` — 新增 /load?level=l0|l1|l2 接口
4. MEMORY.md — 自动生成L0/L1索引文件

**预期效果：**
- 心跳token消耗降低 80%+（只加载L0摘要）
- 任务规划token消耗降低 50%+（只加载L1概览）
- 深度执行时才加载完整内容
- 参考OpenViking实测：token成本降低83-96%

**工期：** 2-3天

---

## 实施路线图

```
Week 1 (2026-03-06 ~ 2026-03-12):

Day 1-2: Token Budget Controller
  - 实现 token_budget.py
  - 集成到 task_executor.py
  - Dashboard预算卡片
  - 测试验证

Day 3-4: Execution Replay
  - 实现 execution_replay.py
  - 集成到 task_executor.py
  - CLI回放工具
  - 测试验证

Day 5-6: Memory Tiered Loading
  - 实现 memory_tiered.py
  - 集成到 heartbeat + task_executor
  - memory_server 新接口
  - 测试验证

Day 7: 集成测试 + 文档
  - 三个升级联合测试
  - 更新 MEMORY.md
  - 更新 Dashboard
```

---

## 预期总收益

| 指标 | 当前 | 升级后 | 提升 |
|------|------|-------|------|
| 成本可控性 | ❌ 无 | ✅ 硬预算+自动降级 | 从0到1 |
| 调试效率 | 🟡 看日志猜 | ✅ 逐步回放 | 5x+ |
| 心跳token消耗 | ~5000 tokens | ~500 tokens | -90% |
| 任务token消耗 | ~10000 tokens | ~3000 tokens | -70% |
| 失败分析时间 | 30min+ | 5min | -83% |

---

*三个升级互相联动：Token Budget记录消耗 → Execution Replay记录轨迹 → Memory Tiered Loading降低消耗。形成完整的成本控制+可观测+效率提升闭环。*
