# AIOS Agent-Skill 架构设计评审

**评审人：** Designer Agent  
**评审日期：** 2026-02-27  
**架构版本：** v1.0  
**评审对象：** `unified_registry.json`

---

## 一、架构概览

当前 AIOS 采用 **Agent-Skill 分离架构**，核心设计理念：
- **12 个专业化 Agent**（11 active + 1 standby）
- **41 个可复用 Skill**（15 个有脚本实现，26 个仅文档）
- **统一注册中心**（unified_registry.json）作为唯一真相来源
- **6 大 Skill 分类**：aios-core、monitoring、development、automation、information、productivity

---

## 二、优点分析

### ✅ 1. 职责清晰的 Agent 分工
每个 Agent 有明确的角色定位和任务类型：
- `coder` → 代码开发（高优先级，Opus 模型）
- `monitor` → 系统监控（高优先级，实时响应）
- `reactor` → 自动修复（关键优先级，快速恢复）
- `evolution` → 自我进化（高思考深度，长期优化）

**优势：** 避免了"万能 Agent"的复杂度，每个 Agent 可以针对特定场景优化 prompt 和模型配置。

### ✅ 2. Skill 可复用性设计
Skill 作为独立能力单元，可被多个 Agent 共享：
- `self-improving-skill` 被 `reactor` 和 `evolution` 共用
- `evaluator-skill` 被 `analyst` 和 `evolution` 共用
- `log-analysis-skill` 被 `analyst` 和 `security` 共用

**优势：** 减少重复开发，提升能力复用率，降低维护成本。

### ✅ 3. 统一注册中心模式
`unified_registry.json` 作为单一真相来源（Single Source of Truth）：
- 集中管理 Agent 配置（模型、优先级、技能）
- 统一 Skill 元数据（分类、描述、脚本状态）
- 实时统计数据（任务完成率、成功率）

**优势：** 避免配置分散，便于全局视图和动态调度。

### ✅ 4. 分层模型配置
根据任务复杂度选择模型：
- **Opus-4-6**：`coder`（代码质量）、`designer`（架构设计）、`game-dev`（创意）
- **Sonnet-4-6**：其他 Agent（平衡性能和成本）
- **Thinking 分级**：off/low/medium/high（按需启用推理）

**优势：** 成本优化，避免过度使用昂贵模型。

---

## 三、缺点与风险

### ⚠️ 1. Skill 实现率低（37%）
**问题：** 41 个 Skill 中仅 15 个有脚本实现（37%），26 个仅有文档（63%）。

**风险：**
- Agent 调用未实现的 Skill 会失败
- 文档与实际能力不匹配，导致调度错误
- 用户期望与实际能力存在巨大鸿沟

**影响范围：**
- `researcher` 的 4 个 Skill 中 3 个无实现
- `automation` 的 7 个 Skill 中 6 个无实现
- `monitor` 的 4 个 Skill 中 3 个无实现

### ⚠️ 2. Agent 利用率极低（8%）
**问题：** 12 个 Agent 中仅 1 个（`coder`）有任务记录，其余 11 个任务数为 0。

**可能原因：**
- 任务路由机制不完善（所有任务都分给了 `coder`）
- Agent 能力未被充分宣传/发现
- 缺少自动任务分发机制

**后果：**
- 资源浪费（11 个 Agent 闲置）
- `coder` 过载风险
- 系统整体效率低下

### ⚠️ 3. 缺少动态能力发现机制
**问题：** 当前架构是静态配置，Agent 无法：
- 自动发现新增的 Skill
- 根据任务需求动态组合 Skill
- 学习哪些 Skill 组合效果最好

**场景示例：**
```
用户："帮我分析这个 API 的性能问题"
理想流程：monitor（检测） → analyst（分析） → reactor（修复）
实际情况：可能只有 coder 响应，其他 Agent 不知道该参与
```

### ⚠️ 4. 归档 Agent 数量过多（28 个）
**问题：** `archived_agents` 有 28 个历史 Agent，是当前活跃 Agent 的 2.3 倍。

**暴露的问题：**
- 早期架构设计不稳定，频繁重构
- 缺少 Agent 生命周期管理策略
- 可能存在重复造轮子（如多个 `coder-*` 变体）

---

## 四、改进建议

### 💡 建议 1：实施 Skill 成熟度分级制度

#### 问题
当前 Skill 只有 `has_script: true/false` 二元状态，无法表达能力的完整性和质量。

#### 方案
引入 **Skill 成熟度模型（Skill Maturity Model）**：

```json
{
  "name": "api-testing-skill",
  "maturity": "beta",  // alpha | beta | stable | deprecated
  "implementation": {
    "script": true,
    "tests": true,
    "docs": "complete",
    "examples": 3
  },
  "quality": {
    "success_rate": 0.92,
    "avg_execution_time_ms": 1200,
    "last_tested": "2026-02-26"
  },
  "capabilities": [
    "http_get", "http_post", "auth_bearer", "response_validation"
  ],
  "limitations": [
    "不支持 GraphQL",
    "不支持 WebSocket"
  ]
}
```

#### 实施步骤
1. **Phase 1（1 周）：** 为所有 Skill 添加 `maturity` 字段
   - `alpha`：仅文档，无实现
   - `beta`：有实现，但未充分测试
   - `stable`：生产可用
   - `deprecated`：计划废弃

2. **Phase 2（2 周）：** 建立自动化测试流程
   ```python
   # aios/core/skill_validator.py
   def validate_skill(skill_name):
       """验证 Skill 的实际能力"""
       script_path = f"skills/{skill_name}/main.py"
       if not exists(script_path):
           return {"maturity": "alpha", "reason": "无脚本"}
       
       test_results = run_skill_tests(skill_name)
       if test_results.success_rate < 0.8:
           return {"maturity": "beta", "reason": "测试通过率低"}
       
       return {"maturity": "stable"}
   ```

3. **Phase 3（持续）：** 在 Dashboard 中展示成熟度
   - 红色：alpha（不可用）
   - 黄色：beta（谨慎使用）
   - 绿色：stable（推荐）

#### 预期收益
- Agent 可以根据成熟度选择 Skill（优先使用 stable）
- 用户清楚知道哪些功能可用
- 开发团队有明确的优化目标（提升 alpha → beta → stable）

---

### 💡 建议 2：构建智能任务路由系统

#### 问题
当前 11/12 Agent 任务数为 0，说明任务分发机制失效。

#### 方案
实现 **基于能力匹配的任务路由器（Capability-Based Task Router）**：

```python
# aios/core/task_router.py
class TaskRouter:
    def __init__(self, registry):
        self.registry = registry
        self.skill_index = self._build_skill_index()
    
    def route(self, task_description: str) -> List[str]:
        """
        根据任务描述，返回最适合的 Agent ID 列表
        
        示例：
        "分析 API 性能问题" → ["monitor", "analyst"]
        "修复登录 bug" → ["coder", "tester"]
        """
        # 1. 提取任务关键词
        keywords = self._extract_keywords(task_description)
        
        # 2. 匹配 Agent 的 task_types
        candidates = []
        for agent in self.registry["agents"]:
            score = self._calculate_match_score(
                keywords, 
                agent["task_types"],
                agent["skills"]
            )
            if score > 0.5:
                candidates.append((agent["id"], score))
        
        # 3. 按优先级和匹配度排序
        candidates.sort(key=lambda x: (
            self._get_priority_weight(x[0]),
            x[1]
        ), reverse=True)
        
        return [agent_id for agent_id, _ in candidates[:3]]
    
    def _calculate_match_score(self, keywords, task_types, skills):
        """计算任务与 Agent 的匹配度"""
        # 关键词匹配
        type_match = sum(1 for k in keywords if k in task_types) / len(keywords)
        
        # Skill 能力匹配
        skill_match = 0
        for skill_name in skills:
            skill = self.skill_index.get(skill_name)
            if skill and skill["maturity"] == "stable":
                skill_match += 0.2
        
        return 0.6 * type_match + 0.4 * min(skill_match, 1.0)
```

#### 集成到调度流程
```python
# aios/core/dispatcher.py
def dispatch_task(task):
    router = TaskRouter(load_registry())
    
    # 获取候选 Agent
    candidates = router.route(task.description)
    
    if len(candidates) == 0:
        return fallback_to_coder(task)
    
    # 选择负载最低的 Agent
    selected = select_least_loaded(candidates)
    
    # 分配任务
    assign_task(selected, task)
    
    # 记录路由决策（用于后续优化）
    log_routing_decision(task, candidates, selected)
```

#### 实施步骤
1. **Week 1：** 实现基础路由器（关键词匹配）
2. **Week 2：** 添加负载均衡（避免单个 Agent 过载）
3. **Week 3：** 引入机器学习（根据历史成功率优化路由）

#### 预期收益
- Agent 利用率从 8% 提升到 60%+
- 任务响应时间降低（专业 Agent 更快）
- 系统整体吞吐量提升 3-5 倍

---

### 💡 建议 3：建立 Agent 协作编排机制

#### 问题
当前 Agent 是孤立的，无法协作完成复杂任务。

#### 方案
实现 **Agent 工作流编排器（Agent Workflow Orchestrator）**：

```python
# aios/core/workflow.py
class AgentWorkflow:
    """
    定义多 Agent 协作流程
    
    示例：API 性能优化工作流
    monitor → analyst → coder → tester → reactor
    """
    def __init__(self, name: str):
        self.name = name
        self.stages = []
    
    def add_stage(self, agent_id: str, task: dict, 
                  depends_on: List[str] = None):
        """添加工作流阶段"""
        self.stages.append({
            "agent": agent_id,
            "task": task,
            "depends_on": depends_on or [],
            "status": "pending"
        })
    
    async def execute(self):
        """执行工作流"""
        results = {}
        
        for stage in self.stages:
            # 等待依赖完成
            await self._wait_for_dependencies(stage, results)
            
            # 执行当前阶段
            agent = get_agent(stage["agent"])
            result = await agent.execute(stage["task"])
            
            results[stage["agent"]] = result
            stage["status"] = "completed"
        
        return results

# 预定义工作流模板
WORKFLOW_TEMPLATES = {
    "api_performance_issue": AgentWorkflow("API 性能问题处理")
        .add_stage("monitor", {"action": "detect_slow_api"})
        .add_stage("analyst", {"action": "analyze_bottleneck"}, 
                   depends_on=["monitor"])
        .add_stage("coder", {"action": "optimize_code"}, 
                   depends_on=["analyst"])
        .add_stage("tester", {"action": "verify_performance"}, 
                   depends_on=["coder"]),
    
    "security_incident": AgentWorkflow("安全事件响应")
        .add_stage("security", {"action": "detect_anomaly"})
        .add_stage("analyst", {"action": "assess_impact"}, 
                   depends_on=["security"])
        .add_stage("reactor", {"action": "execute_playbook"}, 
                   depends_on=["analyst"])
}
```

#### 使用示例
```python
# 用户请求："我的 API 响应很慢，帮我优化"
workflow = WORKFLOW_TEMPLATES["api_performance_issue"]
results = await workflow.execute()

# 自动执行：
# 1. monitor 检测慢查询
# 2. analyst 分析瓶颈（数据库索引缺失）
# 3. coder 添加索引
# 4. tester 验证性能提升
```

#### 在 unified_registry.json 中添加工作流定义
```json
{
  "workflows": [
    {
      "id": "api_perf_optimization",
      "name": "API 性能优化",
      "trigger": ["slow_api", "high_latency"],
      "stages": [
        {"agent": "monitor", "action": "detect"},
        {"agent": "analyst", "action": "analyze"},
        {"agent": "coder", "action": "fix"},
        {"agent": "tester", "action": "verify"}
      ],
      "success_rate": 0.85,
      "avg_duration_min": 15
    }
  ]
}
```

#### 实施步骤
1. **Week 1：** 实现基础工作流引擎（顺序执行）
2. **Week 2：** 添加依赖管理（并行执行）
3. **Week 3：** 定义 5 个常用工作流模板
4. **Week 4：** 集成到 Dashboard（可视化工作流执行）

#### 预期收益
- 复杂任务成功率从 40% 提升到 85%
- 减少人工干预（自动化端到端流程）
- 知识沉淀（工作流模板可复用）

---

## 五、优先级建议

| 改进项 | 优先级 | 预计工期 | 影响范围 | ROI |
|--------|--------|----------|----------|-----|
| **建议 1：Skill 成熟度分级** | 🔴 高 | 3 周 | 全局 | ⭐⭐⭐⭐⭐ |
| **建议 2：智能任务路由** | 🔴 高 | 3 周 | 调度层 | ⭐⭐⭐⭐⭐ |
| **建议 3：Agent 协作编排** | 🟡 中 | 4 周 | 复杂任务 | ⭐⭐⭐⭐ |

**推荐实施顺序：**
1. **先做建议 1**（Skill 成熟度）→ 建立能力基线
2. **再做建议 2**（任务路由）→ 提升 Agent 利用率
3. **最后做建议 3**（协作编排）→ 解决复杂场景

---

## 六、总结

当前 AIOS 架构的核心设计（Agent-Skill 分离、统一注册中心）是**正确且先进的**，但存在三个关键问题：

1. **能力虚高**：63% 的 Skill 无实现
2. **资源闲置**：92% 的 Agent 未被使用
3. **协作缺失**：Agent 无法组队完成复杂任务

通过实施上述三个改进建议，预计可以：
- **Skill 可用率**：37% → 80%
- **Agent 利用率**：8% → 60%
- **复杂任务成功率**：40% → 85%

**下一步行动：**
1. 召开架构评审会议，讨论改进方案
2. 创建 GitHub Issues 跟踪实施进度
3. 分配开发资源（建议 1-2 名工程师，3 个月）

---

**评审完成时间：** 2026-02-27  
**文档版本：** v1.0  
**联系人：** Designer Agent
