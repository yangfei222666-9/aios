# Skill 三层触发器决策输出样例 v0.1

**创建时间：** 2026-03-09  
**状态：** Draft  
**目标：** 定义决策输出格式，指导实现

---

## 设计原则

输出不只是"匹配到 skill"，而是完整的决策链：
- 候选 skill
- L0 命中原因
- L1 场景判断
- L2 最终决策
- 未选 skill 的淘汰原因

---

## 输入定义

```json
{
  "task_text": "帮我分析最近的错误日志",
  "task_type": "analysis",
  "file_signals": [],
  "error_signals": [],
  "runtime_state": {
    "queue_length": 2,
    "active_agents": ["analyst"],
    "recent_failures": []
  },
  "recent_history": [
    "上次任务：提交代码（成功）",
    "上上次任务：查看日志（成功）"
  ]
}
```

---

## 输出定义

### 完整输出结构

```json
{
  "trigger_result": {
    "final_skill": "log-analysis-skill",
    "confidence": 0.92,
    "decision_reason": "任务明确为日志分析，log-analysis-skill 最近成功率 95%，无风险",
    "execution_time_ms": 45
  },
  "l0_signal_filter": {
    "candidates": [
      "log-analysis-skill",
      "database-skill",
      "api-testing-skill"
    ],
    "hits": [
      {
        "skill": "log-analysis-skill",
        "signals": ["错误", "日志", "分析"],
        "match_score": 0.95
      },
      {
        "skill": "database-skill",
        "signals": ["分析"],
        "match_score": 0.30
      },
      {
        "skill": "api-testing-skill",
        "signals": ["错误"],
        "match_score": 0.25
      }
    ]
  },
  "l1_context_match": {
    "matches": [
      {
        "skill": "log-analysis-skill",
        "context_score": 0.90,
        "reasons": [
          "任务类型匹配（analysis）",
          "历史记录显示用户最近在查看日志",
          "当前无冲突任务"
        ]
      },
      {
        "skill": "database-skill",
        "context_score": 0.40,
        "reasons": [
          "任务类型匹配（analysis）",
          "但无数据库相关信号"
        ]
      }
    ],
    "rejected": [
      {
        "skill": "api-testing-skill",
        "reason": "上下文不匹配：任务不涉及 API 测试"
      }
    ]
  },
  "l2_policy_decision": {
    "final_decision": {
      "skill": "log-analysis-skill",
      "priority": "high",
      "risk_level": "low",
      "requires_confirmation": false,
      "strategy": "direct_execute"
    },
    "policy_checks": [
      {
        "check": "success_rate",
        "value": 0.95,
        "threshold": 0.80,
        "passed": true
      },
      {
        "check": "recent_failures",
        "value": 0,
        "threshold": 3,
        "passed": true
      },
      {
        "check": "resource_available",
        "value": true,
        "passed": true
      },
      {
        "check": "risk_level",
        "value": "low",
        "threshold": "medium",
        "passed": true
      }
    ],
    "alternatives": [
      {
        "skill": "database-skill",
        "reason": "也可以分析数据库日志",
        "rejected_because": "任务未明确涉及数据库"
      }
    ]
  }
}
```

---

## 样例 1：成功匹配（低风险）

### 输入
```json
{
  "task_text": "帮我提交代码",
  "task_type": "code",
  "file_signals": [],
  "error_signals": [],
  "runtime_state": {
    "queue_length": 1,
    "active_agents": ["coder"],
    "recent_failures": []
  },
  "recent_history": ["上次任务：查看 git 状态（成功）"]
}
```

### 输出
```json
{
  "trigger_result": {
    "final_skill": "git-skill",
    "confidence": 0.98,
    "decision_reason": "代码提交任务，git-skill 成功率 98%，直接执行",
    "execution_time_ms": 32
  },
  "l0_signal_filter": {
    "candidates": ["git-skill", "docker-skill"],
    "hits": [
      {
        "skill": "git-skill",
        "signals": ["提交", "代码"],
        "match_score": 0.98
      },
      {
        "skill": "docker-skill",
        "signals": ["代码"],
        "match_score": 0.20
      }
    ]
  },
  "l1_context_match": {
    "matches": [
      {
        "skill": "git-skill",
        "context_score": 0.95,
        "reasons": [
          "任务类型匹配（code）",
          "历史记录显示用户刚查看了 git 状态",
          "当前无冲突任务"
        ]
      }
    ],
    "rejected": [
      {
        "skill": "docker-skill",
        "reason": "上下文不匹配：任务不涉及容器"
      }
    ]
  },
  "l2_policy_decision": {
    "final_decision": {
      "skill": "git-skill",
      "priority": "high",
      "risk_level": "low",
      "requires_confirmation": false,
      "strategy": "direct_execute"
    },
    "policy_checks": [
      {
        "check": "success_rate",
        "value": 0.98,
        "threshold": 0.80,
        "passed": true
      },
      {
        "check": "recent_failures",
        "value": 0,
        "threshold": 3,
        "passed": true
      },
      {
        "check": "resource_available",
        "value": true,
        "passed": true
      },
      {
        "check": "risk_level",
        "value": "low",
        "threshold": "medium",
        "passed": true
      }
    ],
    "alternatives": []
  }
}
```

---

## 样例 2：需要确认（高风险）

### 输入
```json
{
  "task_text": "删除所有旧日志文件",
  "task_type": "maintenance",
  "file_signals": [],
  "error_signals": [],
  "runtime_state": {
    "queue_length": 0,
    "active_agents": [],
    "recent_failures": []
  },
  "recent_history": []
}
```

### 输出
```json
{
  "trigger_result": {
    "final_skill": "aios-cleanup",
    "confidence": 0.85,
    "decision_reason": "清理任务，但涉及删除操作，需要用户确认",
    "execution_time_ms": 58
  },
  "l0_signal_filter": {
    "candidates": ["aios-cleanup", "log-analysis-skill"],
    "hits": [
      {
        "skill": "aios-cleanup",
        "signals": ["删除", "日志", "文件"],
        "match_score": 0.90
      },
      {
        "skill": "log-analysis-skill",
        "signals": ["日志"],
        "match_score": 0.40
      }
    ]
  },
  "l1_context_match": {
    "matches": [
      {
        "skill": "aios-cleanup",
        "context_score": 0.85,
        "reasons": [
          "任务类型匹配（maintenance）",
          "明确涉及文件删除"
        ]
      }
    ],
    "rejected": [
      {
        "skill": "log-analysis-skill",
        "reason": "任务不是分析，而是删除"
      }
    ]
  },
  "l2_policy_decision": {
    "final_decision": {
      "skill": "aios-cleanup",
      "priority": "normal",
      "risk_level": "high",
      "requires_confirmation": true,
      "strategy": "confirm_before_execute"
    },
    "policy_checks": [
      {
        "check": "success_rate",
        "value": 0.92,
        "threshold": 0.80,
        "passed": true
      },
      {
        "check": "recent_failures",
        "value": 0,
        "threshold": 3,
        "passed": true
      },
      {
        "check": "resource_available",
        "value": true,
        "passed": true
      },
      {
        "check": "risk_level",
        "value": "high",
        "threshold": "medium",
        "passed": false,
        "action": "requires_confirmation"
      }
    ],
    "alternatives": []
  }
}
```

---

## 样例 3：无匹配 Skill

### 输入
```json
{
  "task_text": "帮我订外卖",
  "task_type": "unknown",
  "file_signals": [],
  "error_signals": [],
  "runtime_state": {
    "queue_length": 0,
    "active_agents": [],
    "recent_failures": []
  },
  "recent_history": []
}
```

### 输出
```json
{
  "trigger_result": {
    "final_skill": null,
    "confidence": 0.0,
    "decision_reason": "无匹配 Skill，建议用户明确任务类型或安装相关 Skill",
    "execution_time_ms": 28
  },
  "l0_signal_filter": {
    "candidates": [],
    "hits": []
  },
  "l1_context_match": {
    "matches": [],
    "rejected": []
  },
  "l2_policy_decision": {
    "final_decision": {
      "skill": null,
      "priority": null,
      "risk_level": null,
      "requires_confirmation": false,
      "strategy": "no_skill_available"
    },
    "policy_checks": [],
    "alternatives": [],
    "suggestions": [
      "检查是否有 food-order skill",
      "或者明确任务类型（如：查询外卖订单）"
    ]
  }
}
```

---

## 样例 4：多个候选，优先级决策

### 输入
```json
{
  "task_text": "分析这个 PDF 文件",
  "task_type": "analysis",
  "file_signals": ["pdf"],
  "error_signals": [],
  "runtime_state": {
    "queue_length": 1,
    "active_agents": ["analyst"],
    "recent_failures": []
  },
  "recent_history": []
}
```

### 输出
```json
{
  "trigger_result": {
    "final_skill": "pdf-skill",
    "confidence": 0.88,
    "decision_reason": "PDF 文件分析，pdf-skill 专门处理 PDF，优先级高于通用分析工具",
    "execution_time_ms": 52
  },
  "l0_signal_filter": {
    "candidates": ["pdf-skill", "document-agent", "log-analysis-skill"],
    "hits": [
      {
        "skill": "pdf-skill",
        "signals": ["PDF", "文件"],
        "match_score": 0.95
      },
      {
        "skill": "document-agent",
        "signals": ["文件", "分析"],
        "match_score": 0.80
      },
      {
        "skill": "log-analysis-skill",
        "signals": ["分析"],
        "match_score": 0.30
      }
    ]
  },
  "l1_context_match": {
    "matches": [
      {
        "skill": "pdf-skill",
        "context_score": 0.90,
        "reasons": [
          "任务类型匹配（analysis）",
          "文件类型明确为 PDF",
          "专门处理 PDF 的工具"
        ]
      },
      {
        "skill": "document-agent",
        "context_score": 0.75,
        "reasons": [
          "任务类型匹配（analysis）",
          "可以处理多种文档类型"
        ]
      }
    ],
    "rejected": [
      {
        "skill": "log-analysis-skill",
        "reason": "任务不涉及日志分析"
      }
    ]
  },
  "l2_policy_decision": {
    "final_decision": {
      "skill": "pdf-skill",
      "priority": "high",
      "risk_level": "low",
      "requires_confirmation": false,
      "strategy": "direct_execute"
    },
    "policy_checks": [
      {
        "check": "success_rate",
        "value": 0.91,
        "threshold": 0.80,
        "passed": true
      },
      {
        "check": "recent_failures",
        "value": 1,
        "threshold": 3,
        "passed": true
      },
      {
        "check": "resource_available",
        "value": true,
        "passed": true
      },
      {
        "check": "risk_level",
        "value": "low",
        "threshold": "medium",
        "passed": true
      },
      {
        "check": "specialization",
        "value": "pdf-skill 专门处理 PDF",
        "passed": true
      }
    ],
    "alternatives": [
      {
        "skill": "document-agent",
        "reason": "通用文档处理工具",
        "rejected_because": "pdf-skill 更专业，优先级更高"
      }
    ]
  }
}
```

---

## MVP 1 验收标准

至少要满足这 5 条：

1. ✅ **能输出候选 skill，不是直接黑盒选一个**
   - `l0_signal_filter.candidates`

2. ✅ **能解释为什么选中**
   - `trigger_result.decision_reason`
   - `l1_context_match.reasons`
   - `l2_policy_decision.policy_checks`

3. ✅ **能解释为什么淘汰其他 skill**
   - `l1_context_match.rejected`
   - `l2_policy_decision.alternatives`

4. ✅ **遇到冲突时有明确优先级规则**
   - `l2_policy_decision.policy_checks.specialization`
   - `l2_policy_decision.alternatives.rejected_because`

5. ✅ **决策结果能写回日志/记忆供后续复盘**
   - 完整的 JSON 输出可直接写入 `skill_trigger_decisions.jsonl`

---

## 实现建议

### L0 Signal Filter（规则匹配）
```python
def l0_signal_filter(task_context):
    candidates = []
    for skill in all_skills:
        signals = skill.get_trigger_signals()
        match_score = calculate_match_score(task_context, signals)
        if match_score > 0.2:  # 阈值
            candidates.append({
                "skill": skill.name,
                "signals": signals,
                "match_score": match_score
            })
    return sorted(candidates, key=lambda x: x["match_score"], reverse=True)
```

### L1 Context Match（场景判断）
```python
def l1_context_match(candidates, task_context):
    matches = []
    rejected = []
    for candidate in candidates:
        context_score = calculate_context_score(candidate, task_context)
        if context_score > 0.5:  # 阈值
            matches.append({
                "skill": candidate["skill"],
                "context_score": context_score,
                "reasons": get_match_reasons(candidate, task_context)
            })
        else:
            rejected.append({
                "skill": candidate["skill"],
                "reason": get_rejection_reason(candidate, task_context)
            })
    return matches, rejected
```

### L2 Policy Decision（策略决策）
```python
def l2_policy_decision(matches, task_context):
    for match in matches:
        policy_checks = run_policy_checks(match, task_context)
        if all(check["passed"] for check in policy_checks):
            return {
                "final_decision": {
                    "skill": match["skill"],
                    "priority": determine_priority(match),
                    "risk_level": determine_risk(match),
                    "requires_confirmation": check_confirmation_needed(match),
                    "strategy": "direct_execute"
                },
                "policy_checks": policy_checks
            }
    return None  # 无匹配
```

---

## 下一步

1. ✅ 完成决策输出样例（本文档）
2. ⏭️ 实现 Skill 三层触发器
3. ⏭️ 集成到决策层
4. ⏭️ 记录决策日志供复盘

---

**版本：** v0.1  
**状态：** Draft  
**维护者：** 小九 + 珊瑚海
