# 太极OS Skill 自动创建 MVP v1.1 详细规格书

**Version:** v1.1  
**Status:** spec_finalized  
**Phase:** design_only  
**Constraint:** no production chain change during observation  
**Created:** 2026-03-09  
**Author:** 小九 + 珊瑚海

---

## 1. 文档目标

定义太极OS第一版 Skill 自动创建系统的详细设计，使系统能够在不改动生产主链路的前提下，完成以下最小闭环：

**自动检测候选 + Agent 主动策展 + 标准化 Skill 生成 + 三层验证 + draft registry 注册 + feedback/patch 留痕**

这不是"全自动上生产"的方案，而是**隔离环境中的能力孵化机制**。

---

## 2. 设计目标

### 2.1 核心目标

让太极OS第一次具备"把重复工作模式沉淀为可复用 Skill"的系统能力。

### 2.2 子目标

第一版必须解决这 6 个问题：

1. 如何发现值得沉淀的模式
2. 如何让 Agent 主动判断"这次工作值不值得存成 Skill"
3. 如何生成统一格式的 Skill 能力包
4. 如何验证 Skill 的格式、行为和风险
5. 如何在不接主链路的前提下注册和试运行
6. 如何记录反馈，并支持后续 patch 更新

### 2.3 非目标

第一版不做这些事：

* 不自动进入正式生产 registry
* 不自动替换旧 Skill
* 不自动删除 Skill
* 不引入复杂依赖图和全局规则引擎
* 不实现完整 Context Engineering 引擎
* 不做高风险 Skill 的自动执行

---

## 3. 核心设计原则

### 3.1 双轨制

Skill 来源有两条路径，同时存在：

**路径 A：自动检测**  
系统从日志、ledger、task records、lessons 中识别重复模式，生成 `skill_candidate`。

**路径 B：Agent 主动策展**  
Agent 在任务结束后主动判断此次工作是否值得保存，生成 `skill_proposal`。

### 3.2 Skill 是记忆化能力单元

Skill 不是单纯一段代码，而是一个完整能力包，至少应包含：

* 目的
* 触发条件
* 输入输出
* 使用说明
* 风险等级
* 验证方式
* 来源样本
* 更新记录

### 3.3 渐进式加载

避免未来 Skill 数量增加后全量加载爆炸。Skill 加载分 3 级：

* **Level 0：** 只加载 metadata
* **Level 1：** 加载摘要与 trigger
* **Level 2：** 加载完整能力包

### 3.4 先隔离后试运行

所有自动生成或 Agent 策展生成的 Skill，先进入 draft registry，不直接接生产。

### 3.5 Patch 优先

Skill 更新优先采用 patch/edit，而不是整体重写。

---

## 4. 系统边界

### 4.1 输入边界

系统允许读取：

* task execution records
* Reality Ledger
* lessons / experience
* heartbeat logs
* GitHub 学习记录
* Agent 任务结束后的自反思结果

### 4.2 输出边界

系统允许写入：

* `skill_candidates.jsonl`
* `skill_proposals.jsonl`
* `skill_generation_events.jsonl`
* `draft_registry/`
* `skill_feedback.jsonl`
* `skill_patch_history.jsonl`

### 4.3 禁止边界

MVP 禁止：

* 修改生产主链路配置
* 自动接入正式通知链
* 自动发外部通知
* 自动执行高风险文件操作
* 自动重启服务
* 自动修改核心生产代码

---

## 5. 总体流程

### 5.1 自动检测路径

```
task records / lessons / ledger / logs
↓
skill_candidate_detector
↓
skill_candidate
↓
agent_review_prompt
↓
确认值得保存
↓
skill_drafter
↓
SKILL.md + supporting files
↓
skill_validator
↓
draft_registry
↓
limited trial
↓
feedback / patch
```

### 5.2 Agent 策展路径

```
Agent task completed
↓
agent_self_reflection
↓
skill_curator
↓
skill_proposal
↓
skill_drafter
↓
skill_validator
↓
draft_registry
↓
limited trial
↓
feedback / patch
```

---

## 6. 核心模块定义

### 6.1 skill_candidate_detector.py

**职责：** 从系统历史记录中识别"值得沉淀为 Skill 的重复模式"。

**输入：**
* task_records
* reality_ledger
* lessons
* error_patterns
* github_learning_notes

**输出：** skill_candidate

**最小接口：**
```python
def detect_candidates(
    task_records: list,
    ledger_records: list,
    lessons: list,
    logs: list
) -> list[dict]:
    ...
```

**最小判定条件：**

命中任一即可生成候选：

* 7 天内同类任务重复 ≥ 3 次
* 同类判断规则被重复使用 ≥ 2 次
* 同类修复步骤重复 ≥ 2 次
* 输入输出模式稳定
* 已形成可重放测试样本

---

### 6.2 agent_skill_curator.py

**职责：** 在 Agent 完成任务后，判断此次工作是否值得保存为 Skill。

**输入：**
* task_summary
* tool_call_count
* errors_overcome
* user_corrections
* workflow_steps
* task_outcome

**输出：** skill_proposal

**最小接口：**
```python
def propose_skill_from_task(task_context: dict) -> dict | None:
    ...
```

**最小触发条件：**

满足任一即可提出提议：

* 工具调用数 ≥ 5
* 成功克服错误
* 用户进行了关键纠正
* 完成非平凡多步工作流
* 未来可复用性明显

---

### 6.3 skill_drafter.py

**职责：** 将 skill_candidate 或 skill_proposal 转成标准化 Skill 能力包。

**输出文件：**
* SKILL.md
* skill_trigger.py
* skill_test_cases.json
* skill_risk_profile.json
* manifest.json

**最小接口：**
```python
def draft_skill(source: dict, output_dir: str) -> dict:
    ...
```

**输出要求：**

必须产生：

* 唯一 skill name
* 标准 frontmatter
* trigger_spec
* test cases
* risk profile
* created_from 信息

---

### 6.4 skill_validator.py

**职责：** 执行三层验证：

* 格式验证
* 行为验证
* 风险验证

**最小接口：**
```python
def validate_skill(skill_dir: str) -> dict:
    ...
```

**返回结构：**
```json
{
  "passed": true,
  "format_check": {...},
  "behavior_check": {...},
  "risk_check": {...},
  "issues": []
}
```

---

### 6.5 skill_registry.py

**职责：** 管理 Skill 的生命周期状态与 draft registry。

**状态枚举：**
* candidate
* proposed
* draft
* validated
* approved_for_trial
* quarantined
* rejected

**最小接口：**
```python
def register_skill(skill_meta: dict, registry_path: str) -> dict:
    ...
```

---

### 6.6 skill_feedback_loop.py

**职责：** 记录试运行效果，产生 feedback，并为 Evolution Score 和 patch 提供输入。

**最小接口：**
```python
def record_skill_feedback(feedback: dict, feedback_path: str) -> None:
    ...
```

---

### 6.7 skill_patcher.py

**职责：** 对已存在 Skill 做 patch/update。

**MVP 约束：** 第一版只预留接口，不做复杂合并逻辑。

**最小接口：**
```python
def patch_skill(skill_dir: str, patch_request: dict) -> dict:
    ...
```

---

## 7. Skill 标准格式规范

### 7.1 SKILL.md 结构

#### 第一部分：YAML frontmatter

必须字段：

```yaml
name: heartbeat_alert_deduper
version: 0.1.0
status: draft
source: auto_detected
purpose: 对 heartbeat 输出中的告警进行去重判断
risk_level: low
validation_mode: offline_replay
created_from:
  - historical_heartbeat_samples
  - deduper_shadow_log.jsonl
rollback_strategy: quarantine_only
trigger_spec:
  activation_signals:
    - has_alerts
  negative_conditions:
    - heartbeat_clean
  priority_score: 70
  required_context_keys:
    - heartbeat_text
    - known_alerts
    - quarantined_modules
input_schema:
  heartbeat_text: string
output_schema:
  classified_alerts: list
```

#### 第二部分：Markdown body

建议段落：

* Purpose
* When to use
* When not to use
* Input / Output
* Trigger logic
* Validation notes
* Known limitations
* Update history

---

### 7.2 manifest.json

用于系统扫描和快速索引，建议与 SKILL.md frontmatter 保持同构。

---

### 7.3 skill_trigger.py

必须暴露两个方法：

```python
class SkillTrigger:
    def should_activate(self, context: dict) -> bool:
        ...
    
    def get_priority(self, context: dict) -> int:
        ...
```

---

### 7.4 skill_test_cases.json

至少包含：

* 正例样本
* 反例样本
* 边界样本

---

### 7.5 skill_risk_profile.json

至少包含：

* risk_level
* file_operations
* network_access
* external_write
* privileged_actions
* rollback_possible

---

## 8. Trigger 规范

### 8.1 必填字段

每个 Skill 必须包含 `skill_trigger_spec`：

* `activation_signals`
* `negative_conditions`
* `priority_score`
* `required_context_keys`

### 8.2 判定原则

Trigger 必须：

* 可解释
* 可测试
* 不依赖模糊自然语言才成立
* 不与生产状态耦合过深

### 8.3 示例

以 heartbeat_alert_deduper 为例：

* activation_signals: has_alerts == true
* negative_conditions: heartbeat_clean == true
* priority_score: 70
* required_context_keys: heartbeat_text, known_alerts, quarantined_modules

---

## 9. 数据结构规范

### 9.1 skill_candidate

```json
{
  "candidate_id": "cand-20260309-001",
  "source_type": "auto_detected",
  "pattern_type": "repeated_alert_judgment",
  "summary": "过去 7 天内多次重复进行 heartbeat 告警去重判断",
  "evidence_sources": [
    "heartbeat logs",
    "manual judgment records"
  ],
  "repeat_count": 5,
  "suggested_skill_name": "heartbeat_alert_deduper",
  "confidence": 0.88,
  "created_at": "2026-03-09T10:00:00+08:00"
}
```

### 9.2 skill_proposal

```json
{
  "proposal_id": "prop-20260309-001",
  "source_type": "agent_curated",
  "agent_name": "GitHub_Researcher",
  "task_id": "task-001",
  "reason": "多步工作流可复用，且未来重复使用概率高",
  "tool_call_count": 6,
  "errors_overcome": 1,
  "user_corrections": 0,
  "suggested_skill_name": "github_learning_digestor",
  "created_at": "2026-03-09T10:10:00+08:00"
}
```

### 9.3 skill_feedback

```json
{
  "skill_name": "heartbeat_alert_deduper",
  "run_time": "2026-03-09T12:00:00+08:00",
  "trial_mode": "shadow",
  "sample_count": 5,
  "match_rate": 0.92,
  "false_positive": 0,
  "false_negative": 1,
  "notes": "旧告警抑制正确，好转状态识别正常"
}
```

---

## 10. 验证流程细节

### 10.1 V1 格式验证

检查项：

* SKILL.md frontmatter 可解析
* 必填字段完整
* supporting files 存在
* JSON 文件可加载
* Python 文件可 py_compile

不通过则直接拒绝进入 `validated`。

---

### 10.2 V2 行为验证

检查项：

* 测试样例可运行
* 输入输出符合 schema
* trigger 行为与预期一致
* 正例能命中
* 反例不误触发

最小要求：

* 正例命中率 ≥ 90%
* 反例误触发率 ≤ 10%

---

### 10.3 V3 风险验证

检查项：

* 是否有高危文件操作
* 是否有外部写请求
* 是否需要高权限
* 是否影响主链路
* 是否有隔离/回滚能力

MVP 只允许 `low` 风险 Skill 进入试运行。

---

## 11. 渐进式加载设计

### 11.1 Level 0：Metadata

加载字段：

* name
* status
* purpose
* trigger_spec
* risk_level

用途：快速筛选是否相关。

### 11.2 Level 1：Summary

额外加载：

* 适用场景
* 输入输出摘要
* 限制条件

用途：判断是否值得真正加载。

### 11.3 Level 2：Full Skill

加载全部内容：

* SKILL.md
* skill_trigger.py
* tests
* risk profile

用途：试运行或执行。

---

## 12. Registry 规范

### 12.1 Draft Registry 目录

建议：

```
skills/
  draft_registry/
  approved_registry/
  quarantined/
```

### 12.2 注册规则

只有满足这些条件，才能进入 `draft_registry`：

* 通过 V1/V2/V3
* 风险等级为 low
* 输出可追溯
* 不依赖主链路改动

### 12.3 Quarantine 规则

以下情况直接隔离：

* 验证通过率不足
* trigger 误判过高
* 风险边界不清晰
* 试运行中产生明显副作用

---

## 13. 第一批实施路径

### Phase 1：标准化现有样板

目标：把 `heartbeat_alert_deduper` 转成标准 Skill 能力包。

产出：

* 标准 SKILL.md
* skill_trigger.py
* skill_test_cases.json
* skill_risk_profile.json

### Phase 2：补 agent_skill_curator.py

让 Agent 在任务结束后能提出 `skill_proposal`。

### Phase 3：补 skill_candidate_detector.py

从历史记录中自动检测候选。

### Phase 4：合流

让 skill_candidate 与 skill_proposal 都能进入统一 drafter/validator/registry 流程。

### Phase 5：补 patch 接口

先支持记录 patch 请求，再支持简单 patch 应用。

---

## 14. 验收标准

本版本通过标准：

1. 至少能通过自动检测产生 1 个 skill_candidate
2. 至少能通过 Agent 策展产生 1 个 skill_proposal
3. 能生成标准化 SKILL.md
4. 能生成 skill_trigger.py
5. 能通过三层验证
6. 能进入 draft registry
7. 能记录至少 1 条 feedback
8. 能记录至少 1 条 patch/update 请求

---

## 15. 太极OS 特性融合

### 15.1 Reality Ledger

必须记录：

* 为什么创建这个 Skill
* 来自哪些真实样本
* 谁确认它值得保存
* 验证结果如何
* 试运行效果如何

### 15.2 Evolution Score

只有当 Skill 产生真实收益时才算进化：

* 减少重复劳动
* 提高准确率
* 降低人工介入
* 降低 token 成本
* 降低错误率

### 15.3 易经状态引擎

作为门控，不直接参与生成逻辑：

* 观察期：允许 candidate/proposal/draft
* 调整期：允许 validation/trial
* 进取期：允许正式推广

---

## 16. 风险与约束

### 当前最大风险

不是"生成不出来 Skill"，而是"生成出来但边界不清"。

### 对应约束

* 只允许 low risk
* 只允许隔离注册
* 只允许 shadow / limited trial
* 不自动接主链路

---

## 17. 当前状态与下一步

### 当前状态

* heartbeat_alert_deduper 已是首个真实样板
* Skill 自动创建 v1.1 骨架已定
* Trigger 已被证明是必要模块

### 下一步

详细规格书完成后，按实施路径推进，不在观察期内改生产主链路。

---

## 18. 一句话定义

太极OS Skill 自动创建 MVP v1.1，不是自动乱长 Skill，而是把"重复工作模式"通过自动检测与 Agent 策展，沉淀成可验证、可隔离、可渐进加载的记忆化能力单元。
