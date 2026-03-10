# Bug_Hunter 未执行根因剖析

**日期：** 2026-03-10  
**分析人：** 小九

---

## 1. 现象

Bug_Hunter 从未执行过任何任务。

**证据：**
- `agents.json` 中的统计：
  - tasks_total: 0
  - tasks_completed: 0
  - tasks_failed: 0
  - success_rate: 0.0
- `task_executions.jsonl`：无 Bug_Hunter 执行记录
- `learning_trigger_state.json`：last_bug_hunt: null

---

## 2. 排查过程

### 2.1. 触发条件检查

**Bug_Hunter 的触发机制：**

```python
def trigger_bug_hunter():
    """触发 Bug 猎人（有新失败时）"""
    state = load_state()
    current_failures = count_recent_failures()
    
    # 如果失败数量增加了 3+ 个，触发 Bug_Hunter
    if current_failures >= state['last_failure_count'] + 3:
        task_id = add_task(
            'Bug_Hunter',
            f'分析最近 {current_failures} 个失败任务，识别共性问题和根因',
            priority='high'
        )
        ...
```

**触发条件：** 最近 24h 失败数量增加 ≥3 个

**实际情况：**
- 最近 24h 失败数量：0
- last_failure_count：0
- 触发条件未满足

**结论：** Bug_Hunter 不是定时触发，而是条件触发。由于系统稳定，失败数量为 0，触发条件从未满足。

### 2.2. 调度分配检查

**learning_agent_triggers.py 的调用：**
- 在 `heartbeat_v5.py` 中每小时整点（current_minute == 0）执行
- `run_triggers()` 会检查所有 Learning Agent 的触发条件
- Bug_Hunter 的触发条件是"失败数量增加 ≥3"

**实际情况：**
- 触发器正常运行
- Bug_Hunter 的触发条件从未满足
- 没有任务被添加到队列

**结论：** 调度器正常，但 Bug_Hunter 的触发条件太严格。

### 2.3. 执行接线检查

**Bug_Hunter 的定义：**
- 在 `learning_agents.py` 中定义
- 在 `agents.json` 中注册
- 在 `learning_agent_triggers.py` 中有触发逻辑

**实际情况：**
- Bug_Hunter 已正确注册
- 触发逻辑存在
- 执行链路完整

**结论：** 执行接线正常，不是"配置上存在，链路上没接"的问题。

### 2.4. 状态语义检查

**lifecycle_check.log 中的状态：**
```
Bug_Hunter
  Stage: 既济 - 功成身退（稳定运行）
  Failure Rate: 0.0%
  Timeout: 60s | Priority: normal
```

**实际情况：**
- Bug_Hunter 从未执行过任何任务
- lifecycle 显示"稳定运行"
- 这是"零失败"被误解为"稳定"的典型案例

**结论：** 状态语义有误导性。"既济 - 功成身退"应该是"从未启用"或"待命中"。

---

## 3. 根因分类

**Bug_Hunter 未执行的根因：未触发**

**具体原因：**
1. 触发条件太严：要求失败数量增加 ≥3 个
2. 系统稳定：最近 24h 失败数量为 0
3. 触发条件从未满足：last_bug_hunt: null

**不是以下原因：**
- ❌ 未路由：触发器正常运行
- ❌ 未接线：执行链路完整
- ❌ 伪激活：有真实的触发逻辑，只是条件未满足

---

## 4. 影响评估

**这个问题影响的是：备用 Agent 未启用**

**具体影响：**
- Bug_Hunter 是一个"应急响应 Agent"，只在系统出现问题时触发
- 当前系统稳定，没有触发需求
- 这不是能力缺失，而是设计如此

**是否需要修复：**
- 如果希望 Bug_Hunter 定期主动巡检，需要修改触发条件
- 如果只希望它在出现问题时响应，当前设计合理

---

## 5. 处理建议

### 选项 1：维持待命（推荐）

**理由：**
- Bug_Hunter 的设计初衷是"应急响应"
- 当前系统稳定，没有触发需求
- 不需要修改

**建议：**
- 修正 lifecycle 状态语义：从"稳定运行"改为"待命中"或"未触发"
- 在 agents.json 中增加 `mode: "standby"` 标记

### 选项 2：激活定期巡检

**理由：**
- 希望 Bug_Hunter 定期主动巡检，而不是被动响应
- 可以提前发现潜在问题

**建议：**
- 修改触发条件：从"失败数量增加 ≥3"改为"每周一次定期巡检"
- 增加定时触发逻辑：
  ```python
  def trigger_bug_hunter():
      state = load_state()
      today = datetime.now().strftime('%Y-%m-%d')
      last_hunt = state.get('last_bug_hunt', '')
      
      # 每周五触发
      if datetime.now().weekday() == 4 and last_hunt != today:
          task_id = add_task(
              'Bug_Hunter',
              '主动巡检系统，识别潜在问题',
              priority='normal'
          )
          state['last_bug_hunt'] = today
          save_state(state)
          return task_id
      return None
  ```

### 选项 3：降低触发阈值

**理由：**
- 保持"应急响应"的设计，但降低触发门槛
- 从"失败数量增加 ≥3"改为"失败数量增加 ≥1"

**建议：**
- 修改 `learning_agent_triggers.py` 中的触发条件：
  ```python
  if current_failures >= state['last_failure_count'] + 1:  # 从 3 改为 1
  ```

---

## 6. 验收标准回答

### 1. Bug_Hunter 为什么从未执行？

**答：** 触发条件太严格（失败数量增加 ≥3），而系统稳定（最近 24h 失败数量为 0），触发条件从未满足。

### 2. 它是没被触发，没被路由，没接进链路，还是只是伪激活？

**答：** 没被触发。触发器正常运行，执行链路完整，但触发条件从未满足。

### 3. 这个问题影响的是能力缺失，还是只是备用 Agent 未启用？

**答：** 备用 Agent 未启用。Bug_Hunter 是应急响应 Agent，当前系统稳定，没有触发需求。

### 4. 下一步应该激活触发、接入调度、补入口，还是维持待命？

**答：** 维持待命（推荐）。如果希望定期巡检，可以修改触发条件为"每周一次定期巡检"。

---

## 7. 附加发现

**lifecycle 状态语义问题：**

Bug_Hunter 的状态显示为"既济 - 功成身退（稳定运行）"，但实际上它从未执行过任何任务。

**建议修正：**
- 对于 tasks_total == 0 的 Agent，状态应该是"待命中"或"未触发"，而不是"稳定运行"
- 这是 P1/P1.5 修复的延续：不要把"零失败"误解为"稳定"

---

**P2 完成。**
