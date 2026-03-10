# Skill Trigger Design - 太极OS 触发条件设计

**存档 ID:** t6q4hn  
**状态:** confirmed / design-only  
**版本:** v1.0  
**日期:** 2026-03-10  
**定性:** 太极OS 有效设计资产

---

## 核心定位

Trigger 不是附属品，它是 **Skill 自动创建 ↔️ 按需激活** 之间的桥梁。

没有触发条件的 Skill 不能规模化。

---

## 设计哲学

> "Adding more rules makes the agent smarter, not more confused — because the engine filters context relevance, not the LLM."  
> — Parlant

Trigger 系统的核心价值：
- 让 Skill 按需激活，不是全量加载
- 让多个 Skill 能共存，不是互相干扰
- 让每次激活都有证据，不是黑盒决策

---

## 分层架构

Trigger 不是单一机制，而是分层的：

### Layer 1: 快速过滤（semantic-router 风格）
- **activation_signals** - 示例语句，用于 embedding 匹配
- **negative_conditions** - 排除条件
- **required_context_keys** - 必需的上下文字段（硬门槛）
- **速度:** 10ms 级别
- **目的:** 快速排除明显不相关的 Skill

### Layer 2: 精确判断（Parlant 风格）
- **condition** - 自然语言条件，LLM 判断
- **priority** - 优先级（0-100）
- **速度:** 100-500ms 级别
- **目的:** 精确判断是否应该激活

### Layer 3: 关系管理
- **dependencies** - 依赖的 observation/skill
- **exclusions** - 排斥的 skill
- **目的:** 防止冲突的 Skill 同时激活

### Layer 4: 证据留痕
- **TriggerDecision** - 完整的决策记录
- **目的:** 支持 shadow 观察、误触发分析、Self-Improving Loop

---

## Phase 1: 最小可用版本（MVP）

### SkillTrigger 定义

```python
class SkillTrigger:
    """Skill 触发条件定义（Phase 1 最小版本）"""
    
    # Layer 1: 快速过滤
    activation_signals: List[str]      # 示例语句，embedding 匹配
    negative_conditions: List[str]     # 排除条件
    required_context_keys: List[str]   # 必需的上下文字段（硬门槛）
    
    def should_activate(self, context: dict) -> TriggerDecision:
        """判断是否应该激活"""
        # 1. 检查必需字段
        missing_keys = [k for k in self.required_context_keys if k not in context]
        if missing_keys:
            return TriggerDecision(
                should_activate=False,
                score=0.0,
                matched_signals=[],
                blocked_by=missing_keys,
                reason=f"Missing required context keys: {missing_keys}"
            )
        
        # 2. 检查排除条件
        for neg_cond in self.negative_conditions:
            if self._matches_condition(context, neg_cond):
                return TriggerDecision(
                    should_activate=False,
                    score=0.0,
                    matched_signals=[],
                    blocked_by=[neg_cond],
                    reason=f"Blocked by negative condition: {neg_cond}"
                )
        
        # 3. 计算激活信号匹配分数
        matched, score = self._match_signals(context, self.activation_signals)
        
        return TriggerDecision(
            should_activate=score >= 0.7,  # 阈值可配置
            score=score,
            matched_signals=matched,
            blocked_by=[],
            reason=f"Matched {len(matched)}/{len(self.activation_signals)} signals, score={score:.2f}"
        )
```

### TriggerDecision 定义

```python
class TriggerDecision:
    """触发决策结果"""
    
    should_activate: bool              # 是否激活
    score: float                       # 匹配分数（0-1）
    matched_signals: List[str]         # 命中的信号
    blocked_by: List[str]              # 被什么阻止（negative_conditions / missing_keys）
    reason: str                        # 判断原因
    
    # 扩展字段（用于证据留痕）
    timestamp: str                     # 判断时间
    context_snapshot: dict             # 上下文快照（可选）
    skill_id: str                      # Skill ID
```

---

## Phase 2: 精确判断（v1.2）

增加 LLM 判断能力：

```python
class SkillTrigger:
    # Phase 1 字段
    activation_signals: List[str]
    negative_conditions: List[str]
    required_context_keys: List[str]
    
    # Phase 2 新增
    condition: str                     # 自然语言条件，LLM 判断
    priority: int                      # 优先级（0-100）
    
    def should_activate(self, context: dict) -> TriggerDecision:
        # Phase 1 逻辑
        decision = self._phase1_check(context)
        if not decision.should_activate:
            return decision
        
        # Phase 2: LLM 精确判断
        if self.condition:
            llm_result = self._llm_judge(context, self.condition)
            if not llm_result.holds:
                return TriggerDecision(
                    should_activate=False,
                    score=decision.score,
                    matched_signals=decision.matched_signals,
                    blocked_by=[f"LLM: {self.condition}"],
                    reason=f"Phase 1 passed but LLM judged condition not met: {llm_result.reason}"
                )
        
        return decision
```

---

## Phase 3: 关系管理（v2.0）

增加 Skill 之间的依赖和排斥：

```python
class SkillTrigger:
    # Phase 1 & 2 字段
    activation_signals: List[str]
    negative_conditions: List[str]
    required_context_keys: List[str]
    condition: str
    priority: int
    
    # Phase 3 新增
    dependencies: List[str]            # 依赖的 observation/skill
    exclusions: List[str]              # 排斥的 skill
    
    def should_activate(
        self, 
        context: dict,
        active_skills: List[str]       # 当前已激活的 Skill
    ) -> TriggerDecision:
        # Phase 1 & 2 逻辑
        decision = self._phase1_and_2_check(context)
        if not decision.should_activate:
            return decision
        
        # Phase 3: 检查依赖
        for dep in self.dependencies:
            if dep not in active_skills:
                return TriggerDecision(
                    should_activate=False,
                    score=decision.score,
                    matched_signals=decision.matched_signals,
                    blocked_by=[f"Missing dependency: {dep}"],
                    reason=f"Dependency not met: {dep}"
                )
        
        # Phase 3: 检查排斥
        for excl in self.exclusions:
            if excl in active_skills:
                return TriggerDecision(
                    should_activate=False,
                    score=decision.score,
                    matched_signals=decision.matched_signals,
                    blocked_by=[f"Excluded by: {excl}"],
                    reason=f"Excluded by active skill: {excl}"
                )
        
        return decision
```

---

## Phase 4: 完整证据留痕（v2.1）

增加完整的审计和回溯能力：

```python
class TriggerDecision:
    # Phase 1-3 字段
    should_activate: bool
    score: float
    matched_signals: List[str]
    blocked_by: List[str]
    reason: str
    
    # Phase 4 新增
    timestamp: str
    skill_id: str
    context_snapshot: dict             # 完整上下文快照
    phase1_result: dict                # Phase 1 判断结果
    phase2_result: dict                # Phase 2 判断结果（如果有）
    phase3_result: dict                # Phase 3 判断结果（如果有）
    llm_trace: dict                    # LLM 判断的完整 trace（如果有）
    
    def to_audit_log(self) -> dict:
        """转换为审计日志格式"""
        return {
            "decision_id": self.generate_id(),
            "timestamp": self.timestamp,
            "skill_id": self.skill_id,
            "should_activate": self.should_activate,
            "score": self.score,
            "reason": self.reason,
            "matched_signals": self.matched_signals,
            "blocked_by": self.blocked_by,
            "context_keys": list(self.context_snapshot.keys()),
            "phase_results": {
                "phase1": self.phase1_result,
                "phase2": self.phase2_result,
                "phase3": self.phase3_result,
            },
            "llm_trace": self.llm_trace,
        }
```

---

## 实施路径

### Phase 1（当前 MVP）
- ✅ 定义 `SkillTrigger` 最小结构
- ✅ 定义 `TriggerDecision` 留痕结构
- ⏳ 实现 embedding 匹配
- ⏳ 实现硬门槛过滤
- ⏳ 实现排除条件检查

### Phase 2（v1.2）
- ⏳ 增加 LLM 条件判断
- ⏳ 增加优先级排序
- ⏳ 支持多个 Skill 同时命中时的处理

### Phase 3（v2.0）
- ⏳ 增加依赖关系
- ⏳ 增加排斥关系
- ⏳ 支持 Skill 之间的关系管理

### Phase 4（v2.1）
- ⏳ 完整证据留痕
- ⏳ 支持审计和回溯
- ⏳ 集成 OpenTelemetry

---

## 与其他模块的关系

### Skill 自动创建
- `skill_drafter.py` 生成 Skill 时，同时生成 `skill_trigger.py`
- 从候选模式中提取触发条件
- 生成 `activation_signals` 和 `required_context_keys`

### 按需激活
- 每次任务开始前，遍历所有 Skill 的 trigger
- 只激活 `should_activate=True` 的 Skill
- 记录激活决策到 `trigger_decisions.jsonl`

### Context Engineering
- Trigger 是 Context Engineering 的第一步
- 先过滤出相关的 Skill，再构建上下文
- 减少无效的 Skill 加载和 token 消耗

### Self-Improving Loop
- 从 `trigger_decisions.jsonl` 中分析误触发
- 自动调整 `activation_signals` 和 `negative_conditions`
- 优化触发阈值

---

## 关键设计决策

### 为什么先做硬门槛过滤？
- 防止"像但不该激活"
- 减少 embedding 计算量
- 提高触发准确性

### 为什么分 4 个 Phase？
- Phase 1 最简单，可以快速验证
- Phase 2-4 逐步增加复杂度
- 每个 Phase 都是独立可用的

### 为什么要留痕？
- 支持 shadow 观察
- 支持误触发分析
- 支持 Self-Improving Loop
- 支持审计和合规

### 为什么不直接用 LLM 判断？
- LLM 判断慢（100-500ms）
- embedding 匹配快（10ms）
- 先快速过滤，再精确判断

---

## 参考项目

### semantic-router
- **核心思路:** 用语义向量空间做快速路由
- **优势:** 超快速（10ms 级别）
- **劣势:** 不支持复杂关系管理
- **借鉴:** Layer 1 快速过滤

### Parlant
- **核心思路:** 动态上下文匹配 + 关系管理
- **优势:** 支持依赖/排斥，完整 explainability
- **劣势:** 依赖 LLM 判断，速度较慢
- **借鉴:** Layer 2-4 精确判断和关系管理

---

## 下一步

1. **在 `skill_drafter.py` 中增加 `generate_trigger()` 函数**
2. **从候选模式中提取触发条件**
3. **生成 `skill_trigger.py` 模板**
4. **在 Skill 验证时测试触发条件的准确性**
5. **在 draft registry 中记录触发条件的表现**

---

## 附录：示例

### 示例 1: heartbeat_alert_deduper

```python
trigger = SkillTrigger(
    activation_signals=[
        "检查告警去重",
        "有新的 Skill 失败告警",
        "需要判断是否应该通知",
    ],
    negative_conditions=[
        "用户明确要求发送所有告警",
        "系统处于调试模式",
    ],
    required_context_keys=[
        "skill_failure_alerts",  # 必须有告警数据
    ],
)
```

### 示例 2: github_researcher

```python
trigger = SkillTrigger(
    activation_signals=[
        "学习 GitHub 项目",
        "研究 AIOS 相关项目",
        "找最新的 Agent 系统",
    ],
    negative_conditions=[
        "观察期内",
        "系统健康度 < 60",
    ],
    required_context_keys=[
        "learning_mode",  # 必须处于学习模式
    ],
)
```

---

**最后更新:** 2026-03-10  
**维护者:** 小九 + 珊瑚海
