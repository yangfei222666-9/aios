# Agent Tool Use Pattern - 工具使用模式最佳实践

**研究日期：** 2026-03-14  
**主题：** Tool Use Pattern（工具调用模式）  
**来源：** Anthropic Claude, OpenAI GPT, AIOS 实践总结

---

## 1. 核心原理

### 1.1 什么是 Tool Use Pattern？

Tool Use Pattern 是 Agent 系统中最核心的能力之一，定义了 Agent 如何：
- **发现工具**：知道有哪些工具可用
- **选择工具**：根据任务选择合适的工具
- **调用工具**：正确传参、处理返回
- **处理错误**：工具失败时的降级策略
- **学习优化**：从工具使用历史中学习

### 1.2 为什么重要？

工具是 Agent 的"手脚"，没有工具，Agent 只能"空想"。好的工具使用模式能：
- **提高成功率**：正确选择工具 → 任务完成率 ↑
- **降低成本**：避免无效调用 → Token 消耗 ↓
- **增强可靠性**：错误处理 → 系统稳定性 ↑
- **加速学习**：工具使用反馈 → 自我改进 ↑

---

## 2. 业界最佳实践

### 2.1 Anthropic Claude 的 Tool Use 设计

**核心特点：**
1. **Schema-First**：工具定义必须包含完整的 JSON Schema
2. **Strict Validation**：调用前验证参数类型和必填项
3. **Error Propagation**：工具错误直接返回给 Agent，让 Agent 自己决策
4. **Multi-Tool Support**：一次可以调用多个工具（并行）

**示例：**
```json
{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "input_schema": {
    "type": "object",
    "properties": {
      "location": {"type": "string", "description": "City name"},
      "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["location"]
  }
}
```

**优势：**
- 类型安全：Schema 强制约束，减少参数错误
- 自文档化：description 即文档，Agent 能理解工具用途
- 并行调用：提高效率（如同时查天气 + 查日历）

### 2.2 OpenAI Function Calling 的设计

**核心特点：**
1. **Function as Tool**：工具就是函数，直观易懂
2. **Auto-Retry**：参数错误时自动重试（最多 3 次）
3. **Streaming Support**：支持流式返回（长时间工具）
4. **Tool Choice Control**：可以强制使用某个工具

**示例：**
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]
```

**优势：**
- 自动重试：减少人工干预
- 流式返回：适合长时间工具（如代码执行）
- 强制工具：适合特定场景（如"必须用搜索"）

### 2.3 LangChain 的 Tool Pattern

**核心特点：**
1. **Tool Abstraction**：统一的 Tool 接口
2. **Tool Registry**：工具注册中心，动态加载
3. **Tool Chaining**：工具链式调用（A 的输出 → B 的输入）
4. **Error Handling**：统一的错误处理机制

**示例：**
```python
from langchain.tools import Tool

def search_web(query: str) -> str:
    # 实现搜索逻辑
    return results

search_tool = Tool(
    name="search",
    func=search_web,
    description="Search the web for information"
)
```

**优势：**
- 统一接口：所有工具都是 Tool 对象
- 动态加载：可以运行时添加/删除工具
- 链式调用：适合复杂任务（如"搜索 → 总结 → 翻译"）

---

## 3. AIOS 当前实现分析

### 3.1 当前架构

**文件：** `aios/agent_system/action_schema.py`

**核心组件：**
1. **ActionRecord**：动作记录（包含工具调用信息）
2. **状态机**：proposed → locked → executing → completed/failed → released
3. **LedgerEvent**：审计事件（记录每次状态变化）

**工具调用流程：**
```
1. Agent 提议动作（proposed）
2. 锁定资源（locked）
3. 执行工具（executing）
4. 记录结果（completed/failed）
5. 释放资源（released）
```

### 3.2 优势

✅ **严格的状态管理**：每个工具调用都有完整的生命周期  
✅ **审计追踪**：所有工具调用都有 LedgerEvent 记录  
✅ **资源锁定**：避免并发冲突（如同时修改同一文件）  
✅ **幂等性支持**：通过 `idempotency_key` 避免重复执行  

### 3.3 不足

❌ **缺少工具注册中心**：工具定义分散在各个 Agent 中  
❌ **缺少参数验证**：没有 Schema 强制约束  
❌ **缺少错误重试**：工具失败后没有自动重试机制  
❌ **缺少工具链支持**：无法方便地组合多个工具  
❌ **缺少工具使用统计**：不知道哪些工具最常用/最容易失败  

---

## 4. 改进建议

### 4.1 短期改进（1-2 周）

#### 4.1.1 添加工具注册中心

**目标：** 统一管理所有工具定义

**实现：**
```python
# aios/agent_system/tool_registry.py
from typing import Dict, Callable, Any
from dataclasses import dataclass

@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable
    schema: Dict[str, Any]  # JSON Schema
    tags: list[str] = []
    
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> ToolDefinition:
        return self._tools.get(name)
    
    def list_by_tag(self, tag: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if tag in t.tags]
```

**好处：**
- 集中管理：所有工具定义在一个地方
- 动态加载：可以运行时添加新工具
- 标签过滤：按场景筛选工具（如"文件操作"、"网络请求"）

#### 4.1.2 添加参数验证

**目标：** 调用前验证参数，减少错误

**实现：**
```python
# aios/agent_system/tool_validator.py
import jsonschema

def validate_tool_params(tool_name: str, params: dict) -> tuple[bool, str]:
    """验证工具参数是否符合 Schema"""
    tool = ToolRegistry.get(tool_name)
    if not tool:
        return False, f"Tool {tool_name} not found"
    
    try:
        jsonschema.validate(params, tool.schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, str(e)
```

**好处：**
- 提前发现错误：避免执行后才发现参数错误
- 清晰的错误信息：告诉 Agent 哪个参数错了

#### 4.1.3 添加自动重试

**目标：** 工具失败时自动重试（可配置）

**实现：**
```python
# aios/agent_system/tool_executor.py
import time

def execute_tool_with_retry(
    tool_name: str,
    params: dict,
    max_retries: int = 3,
    backoff: float = 1.0
) -> tuple[bool, Any]:
    """执行工具，失败时自动重试"""
    tool = ToolRegistry.get(tool_name)
    
    for attempt in range(max_retries):
        try:
            result = tool.func(**params)
            return True, result
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(backoff * (2 ** attempt))  # 指数退避
                continue
            return False, str(e)
```

**好处：**
- 提高成功率：网络抖动、临时错误可以自动恢复
- 减少人工干预：不需要 Agent 手动重试

### 4.2 中期改进（1-2 月）

#### 4.2.1 工具使用统计

**目标：** 记录工具使用情况，用于优化

**实现：**
```python
# aios/agent_system/tool_stats.py
from collections import defaultdict
import json

class ToolStats:
    def __init__(self):
        self.calls = defaultdict(int)       # 调用次数
        self.successes = defaultdict(int)   # 成功次数
        self.failures = defaultdict(int)    # 失败次数
        self.avg_duration = defaultdict(float)  # 平均耗时
    
    def record_call(self, tool_name: str, success: bool, duration: float):
        self.calls[tool_name] += 1
        if success:
            self.successes[tool_name] += 1
        else:
            self.failures[tool_name] += 1
        
        # 更新平均耗时（增量计算）
        n = self.calls[tool_name]
        old_avg = self.avg_duration[tool_name]
        self.avg_duration[tool_name] = (old_avg * (n-1) + duration) / n
    
    def get_top_tools(self, n: int = 10) -> list:
        """返回最常用的 N 个工具"""
        return sorted(self.calls.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def get_failure_rate(self, tool_name: str) -> float:
        """返回工具失败率"""
        total = self.calls[tool_name]
        if total == 0:
            return 0.0
        return self.failures[tool_name] / total
```

**好处：**
- 发现热点工具：优先优化最常用的工具
- 发现问题工具：失败率高的工具需要修复
- 性能优化：耗时长的工具需要优化

#### 4.2.2 工具链支持

**目标：** 方便地组合多个工具

**实现：**
```python
# aios/agent_system/tool_chain.py
from typing import List, Callable

class ToolChain:
    def __init__(self, steps: List[tuple[str, Callable]]):
        """
        steps: [(tool_name, transform_func), ...]
        transform_func: 将上一步输出转换为下一步输入
        """
        self.steps = steps
    
    def execute(self, initial_input: Any) -> tuple[bool, Any]:
        """执行工具链"""
        current_input = initial_input
        
        for tool_name, transform in self.steps:
            # 执行工具
            success, result = execute_tool_with_retry(tool_name, current_input)
            if not success:
                return False, f"Tool {tool_name} failed: {result}"
            
            # 转换输出为下一步输入
            current_input = transform(result)
        
        return True, current_input

# 示例：搜索 → 总结 → 翻译
chain = ToolChain([
    ("search", lambda x: {"query": x}),
    ("summarize", lambda x: {"text": x["results"]}),
    ("translate", lambda x: {"text": x["summary"], "target": "zh"})
])

success, result = chain.execute("AI news")
```

**好处：**
- 简化复杂任务：一次调用完成多步操作
- 可复用：常用的工具链可以保存为模板

### 4.3 长期改进（3-6 月）

#### 4.3.1 工具推荐系统

**目标：** 根据任务自动推荐合适的工具

**实现思路：**
1. 收集历史数据：任务描述 + 使用的工具 + 成功/失败
2. 训练分类器：输入任务描述 → 输出推荐工具列表
3. 在线推荐：Agent 提出任务时，系统推荐最可能成功的工具

**好处：**
- 提高效率：Agent 不需要遍历所有工具
- 提高成功率：推荐最适合的工具

#### 4.3.2 工具自动生成

**目标：** 根据需求自动生成新工具

**实现思路：**
1. Agent 发现缺少某个工具（如"压缩文件"）
2. 系统搜索相关代码示例（GitHub、Stack Overflow）
3. 生成工具代码 + Schema
4. 自动测试 + 注册到 ToolRegistry

**好处：**
- 快速扩展：不需要人工编写每个工具
- 自我进化：系统能力随需求增长

---

## 5. 实施计划

### Week 1-2: 工具注册中心 + 参数验证
- [ ] 实现 `tool_registry.py`
- [ ] 实现 `tool_validator.py`
- [ ] 迁移现有工具到注册中心
- [ ] 添加单元测试

### Week 3-4: 自动重试 + 工具统计
- [ ] 实现 `tool_executor.py`（带重试）
- [ ] 实现 `tool_stats.py`
- [ ] 集成到 ActionRecord 流程
- [ ] 添加统计 Dashboard

### Month 2: 工具链 + 推荐系统（原型）
- [ ] 实现 `tool_chain.py`
- [ ] 收集工具使用历史数据
- [ ] 训练简单的推荐模型（基于规则）
- [ ] 集成到 Agent 决策流程

### Month 3-6: 工具自动生成（探索）
- [ ] 调研工具生成技术
- [ ] 实现原型（简单场景）
- [ ] 评估可行性

---

## 6. 关键指标

### 6.1 成功率指标
- **工具调用成功率**：目标 >95%
- **首次调用成功率**：目标 >85%（减少重试）
- **参数验证通过率**：目标 >90%

### 6.2 效率指标
- **平均工具调用时间**：目标 <2s
- **工具选择时间**：目标 <500ms
- **重试次数**：目标 <1.2 次/调用

### 6.3 学习指标
- **工具推荐准确率**：目标 >80%（Top-3）
- **新工具生成成功率**：目标 >60%（能通过测试）

---

## 7. 风险与挑战

### 7.1 技术风险
- **Schema 定义复杂**：复杂工具的 Schema 难以维护
- **重试逻辑复杂**：哪些错误该重试？重试几次？
- **工具链调试困难**：中间步骤失败时难以定位

### 7.2 缓解措施
- **Schema 生成工具**：自动从函数签名生成 Schema
- **重试策略配置化**：每个工具可以自定义重试策略
- **工具链可视化**：提供调试界面，显示每步的输入输出

---

## 8. 参考资料

- Anthropic Claude Tool Use: https://docs.anthropic.com/claude/docs/tool-use
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- LangChain Tools: https://python.langchain.com/docs/modules/agents/tools/
- AIOS Reality Ledger: `aios/docs/REALITY_LEDGER.md`

---

## 9. 总结

Tool Use Pattern 是 Agent 系统的核心能力。AIOS 当前的状态机设计已经很好地解决了**资源管理**和**审计追踪**问题，但在**工具发现**、**参数验证**、**错误处理**、**工具组合**方面还有提升空间。

通过引入**工具注册中心**、**参数验证**、**自动重试**、**工具链**、**工具统计**等机制，可以显著提高工具使用的成功率和效率，为 AIOS 的自我进化提供更坚实的基础。

**下一步：** 开始实施 Week 1-2 的改进（工具注册中心 + 参数验证）。
