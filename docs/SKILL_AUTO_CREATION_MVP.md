# 太极OS Skill 自动创建 MVP

**版本：** v1.0  
**日期：** 2026-03-09  
**状态：** 设计阶段

---

## 一句话目标

让太极OS第一次具备这种能力：

**在发现重复问题后，自动生成一个 Skill 草案，经过验证后进入隔离注册区，并在使用后留下改进记录。**

注意是 **MVP**，不是一次做完整自动闭环。

第一版只追求：
```
发现 → 生成 → 验证 → 隔离注册 → 使用后留痕
```

先不追求自动上生产。

---

## 设计原则

### 1. 不碰主链路
观察期内只做设计，不接生产，不改 heartbeat 主流程。

### 2. 先隔离，后接入
自动生成的 Skill 先进入 **sandbox / draft registry**，不是直接进入正式 Skill 池。

### 3. 先做半自动闭环
第一版不要求全自动部署，允许：
- 自动生成
- 自动验证
- 人工确认注册

### 4. 保留太极OS独特能力
Skill 自动创建不能只是模仿 hermes-agent，必须融入：
- **Reality Ledger**：记录整个 Skill 生命周期
- **Evolution Score**：衡量新 Skill 是否带来真实进化
- **易经状态引擎**：决定当前适不适合生成/试验/推广 Skill

---

## MVP 范围

### 本次做
- Skill 触发条件定义
- Skill 草案自动生成
- 基础验证
- 隔离注册
- 使用后记录与反馈

### 本次不做
- 自动直接部署到正式生产
- 自动替换旧 Skill
- 自动删除 Skill
- 大规模多 Skill 并发生成
- 自主重写整个 Skill 框架

---

## 最小闭环

### Step 1：触发（Discover）

当系统发现某类问题反复出现时，生成一个 `skill_creation_candidate`。

#### 触发条件建议
满足任一即可进入候选：
1. 同类任务连续出现 ≥ 3 次
2. 同类修复步骤被人工重复执行 ≥ 2 次
3. 某类分析/转换/检查任务有稳定输入输出模式
4. lessons / experience 中出现可抽象规则
5. GitHub 学习发现明确可借鉴的 Skill 模式

#### 输入来源
- Reality Ledger
- task_execution records
- lessons / experience
- GitHub learning notes
- manual proposal

---

### Step 2：生成（Generate）

由 `skill_drafter` 生成 Skill 草案。

#### 输出内容
生成一个 Skill 草案包，至少包含：
- `skill_manifest.json`（包含 skill_trigger_spec）
- `skill_trigger.py`（触发条件实现）
- `skill_logic.py` 或 `skill_template.py`
- `skill_test_cases.json`
- `skill_risk_profile.json`
- `README.md`

#### manifest 最小字段
- `skill_name`
- `purpose`
- `trigger_pattern`
- `input_schema`
- `output_schema`
- `dependencies`
- `risk_level`
- `validation_mode`
- `rollback_strategy`
- `created_from`

#### skill_trigger_spec（新增）

每个 Skill 草案必须包含触发条件定义，用于实现"按需激活"而非"全量加载"。

**最小字段：**
- `activation_signals` - 激活信号（什么情况下应该加载这个 Skill）
- `negative_conditions` - 排除条件（什么情况下不应该加载）
- `priority_score` - 优先级（0-100，多个 Skill 同时匹配时的排序依据）
- `required_context_keys` - 必需的上下文字段（缺失时不激活）

**示例（heartbeat_alert_deduper）：**
```json
{
  "activation_signals": ["has_alerts == true", "heartbeat_mode == active"],
  "negative_conditions": ["heartbeat_status == clean", "alerts_disabled == true"],
  "priority_score": 70,
  "required_context_keys": ["heartbeat_text", "known_alerts", "quarantined_modules"]
}
```

**为什么重要：**
- 防止 Skill 数量增加后的上下文爆炸
- 提高 Skill 触发准确性
- 降低无效加载的 token 成本
- 为未来的动态上下文匹配引擎铺路

**实施路径：**
1. `skill_drafter` 从候选模式中提取触发条件
2. 生成 `skill_trigger.py` 模板
3. 在验证阶段测试触发条件准确性
4. 在 draft registry 中记录触发表现

---

### Step 3：验证（Validate）

由 `skill_validator` 做三层验证。

#### V1 语法验证
- 文件结构完整
- 代码可解析
- schema 合法
- 依赖声明存在
- **触发条件定义完整且可执行**

#### V2 行为验证
- 用 1~3 个测试样例跑通
- 输出格式符合预期
- 不出现明显异常

#### V3 风险验证
检查是否涉及：
- 文件删除/覆盖
- 网络请求
- 外部系统写操作
- 高权限执行
- 不可回滚动作

**高风险 Skill 一律不进入自动注册。**

---

### Step 4：隔离注册（Register in Draft Registry）

验证通过后，不直接上生产，而是进入：
```
skills/draft_registry/
```

#### 状态建议
- `draft`
- `validated`
- `quarantined`
- `approved`
- `rejected`

#### Reality Ledger 记录
必须写入：
- 触发原因
- 来源样本
- 生成时间
- 验证结果
- 风险级别
- 当前状态

---

### Step 5：试运行与反馈（Observe / Improve）

对已验证 Skill，在隔离环境里跑有限样本。

#### 观察指标
- 命中率
- 成功率
- 平均耗时
- 是否减少人工步骤
- 是否引入新错误
- 对 Evolution Score 是否有正贡献
- **触发条件准确性**（误触发率、漏触发率）

#### 改进输出
产生一条 `skill_improvement_note`：
- 哪些输入没覆盖
- 哪些输出不稳定
- 是否值得进入正式注册池

---

## 需要的 5 个核心模块

### 1. `skill_candidate_detector.py`
**职责：**
- 从 ledger / lessons / task records 中发现可抽象的重复模式
- 输出候选任务

### 2. `skill_drafter.py`
**职责：**
- 根据候选模式生成 Skill 草案包
- 从候选模式中提取触发条件
- 生成 `skill_trigger.py` 实现

### 3. `skill_validator.py`
**职责：**
- 做语法、行为、风险三层验证

### 4. `skill_draft_registry.py`
**职责：**
- 管理 draft / validated / approved / quarantined 状态

### 5. `skill_feedback_loop.py`
**职责：**
- 记录试运行结果
- 产出改进建议
- 回写 Reality Ledger / Evolution Score 输入源

---

## 太极OS特色怎么融进去

### 1. Reality Ledger
不是只记"Skill 创建成功"，而是记录完整链路：
- 为什么创建
- 从哪些样本归纳而来
- 验证是否通过
- 是否试运行成功
- 是否带来真实收益

这会让 Skill 自动创建具备**可追溯性**。

---

### 2. Evolution Score
新 Skill 不是"生成了就算进化"，而是要看：
- 是否减少重复劳动
- 是否提高成功率
- 是否降低延迟
- 是否减少人工介入
- 是否减少同类错误

只有带来正向变化，才计入进化收益。

---

### 3. 易经状态引擎
这个很适合做**生成门控**。

例如：
- **坤 / 守势阶段**：只允许分析，不允许注册
- **震 / 变化阶段**：允许生成 draft
- **兑 / 调整阶段**：允许验证与小范围试运行
- **乾 / 进取阶段**：允许批准进入正式池

这样 Skill 自动创建就不是机械流程，而是和系统状态绑定。

---

## MVP 数据流

```text
Reality Ledger / lessons / task records
          ↓
skill_candidate_detector
          ↓
skill_creation_candidate
          ↓
skill_drafter
          ↓
draft skill package
          ↓
skill_validator
          ↓
validated / quarantined
          ↓
draft registry
          ↓
limited trial
          ↓
feedback loop
          ↓
Reality Ledger + Evolution Score inputs
```

---

## 最小目录建议

```text
taijios/
  skills/
    draft_registry/
    approved_registry/
    quarantined/
  skill_generation/
    skill_candidate_detector.py
    skill_drafter.py
    skill_validator.py
    skill_draft_registry.py
    skill_feedback_loop.py
  memory/
    skill_candidates.jsonl
    skill_generation_events.jsonl
    skill_feedback.jsonl
```

---

## 第一版最小验收标准

只要做到这 5 条，就算 MVP 成功：

1. 能从真实样本中识别出 **1 个 Skill 候选**
2. 能自动生成 1 份 Skill 草案包
3. 能通过基础验证
4. 能进入 draft registry，而不是直接进生产
5. 能在试运行后留下 feedback 记录

---

## 推荐第一批 Skill 类型

不要选高风险 Skill。

### 第一批最适合选：
- 日志分析类
- 报告整理类
- 规则检查类
- GitHub 项目摘要类
- 配置一致性检查类

### 不建议第一批就做：
- 文件修改类
- 自动修复类
- 外部 API 写入类
- 高权限执行类

---

## 下一步

1. 等待珊瑚海提供"第一批最适合自动创建的 Skill 候选清单"
2. 基于清单选择 1 个最小候选
3. 实现 5 个核心模块
4. 完成第一个 Skill 草案的完整闭环

---

**存档 ID：** i2p1l9  
**维护者：** 小九 + 珊瑚海
