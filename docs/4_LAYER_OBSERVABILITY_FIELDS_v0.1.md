# 四层观测报告字段定义 v0.1

**创建时间：** 2026-03-09  
**状态：** Draft  
**目标：** 定义观测字段，指导采集逻辑

---

## 设计原则

报告最后必须能自动产出这 3 句话：
1. **当前最弱链路是什么**
2. **最该优先修什么**
3. **修完预期会改善什么**

只要做不到这 3 句，就说明还只是监控，不是诊断。

---

## 报告结构

```
health_report/
├── runtime.json          # L1 Runtime View
├── incidents.json        # L2 Incident View
├── trends.json           # L3 Trend View
├── diagnosis.json        # L4 Diagnosis View
└── summary.md            # 人类可读摘要
```

---

## L1 Runtime View（当前状态）

### 职责
看当前：队列长度、活跃 agent、执行耗时、资源占用

### 字段定义

```json
{
  "timestamp": "2026-03-09T21:00:00+08:00",
  "queue": {
    "length": 3,
    "pending_tasks": [
      {
        "task_id": "task-001",
        "type": "code",
        "priority": "high",
        "age_seconds": 120
      },
      {
        "task_id": "task-002",
        "type": "analysis",
        "priority": "normal",
        "age_seconds": 45
      },
      {
        "task_id": "task-003",
        "type": "monitor",
        "priority": "low",
        "age_seconds": 30
      }
    ]
  },
  "agents": {
    "active_count": 2,
    "active_agents": [
      {
        "name": "coder-dispatcher",
        "status": "running",
        "current_task": "task-004",
        "elapsed_seconds": 18
      },
      {
        "name": "analyst-dispatcher",
        "status": "running",
        "current_task": "task-005",
        "elapsed_seconds": 32
      }
    ],
    "idle_agents": ["monitor-dispatcher"]
  },
  "execution": {
    "avg_exec_ms": 18500,
    "p50_exec_ms": 15200,
    "p95_exec_ms": 32000,
    "max_exec_ms": 45000
  },
  "resources": {
    "cpu_percent": 45.2,
    "memory_mb": 1024,
    "disk_usage_percent": 68.5,
    "network_active": true
  }
}
```

### 采集方式

```python
def collect_runtime_view():
    return {
        "timestamp": datetime.now().isoformat(),
        "queue": get_queue_status(),
        "agents": get_agent_status(),
        "execution": get_execution_metrics(),
        "resources": get_resource_usage()
    }
```

---

## L2 Incident View（当前异常）

### 职责
看异常：失败、超时、卡死、重复重试、抑制告警

### 字段定义

```json
{
  "timestamp": "2026-03-09T21:00:00+08:00",
  "failures": {
    "count_24h": 5,
    "recent_failures": [
      {
        "task_id": "task-006",
        "agent": "coder-dispatcher",
        "error_type": "timeout",
        "timestamp": "2026-03-09T20:45:00+08:00",
        "details": "执行超时（60s）"
      },
      {
        "task_id": "task-007",
        "agent": "analyst-dispatcher",
        "error_type": "network_error",
        "timestamp": "2026-03-09T20:30:00+08:00",
        "details": "无法连接到外部 API"
      }
    ]
  },
  "timeouts": {
    "count_24h": 3,
    "timeout_agents": [
      {
        "agent": "coder-dispatcher",
        "count": 2,
        "avg_timeout_ms": 62000
      },
      {
        "agent": "analyst-dispatcher",
        "count": 1,
        "avg_timeout_ms": 65000
      }
    ]
  },
  "zombies": {
    "count": 0,
    "zombie_tasks": []
  },
  "retry_loops": {
    "count": 1,
    "looping_tasks": [
      {
        "task_id": "task-008",
        "agent": "monitor-dispatcher",
        "retry_count": 4,
        "last_error": "resource_exhausted"
      }
    ]
  },
  "alerts": {
    "suppressed_count": 3,
    "suppressed_alerts": [
      {
        "alert_id": "alert-001",
        "type": "skill_failure",
        "skill": "api-testing-skill",
        "first_seen": "2026-03-06T10:00:00+08:00",
        "last_seen": "2026-03-09T20:00:00+08:00",
        "count": 12
      }
    ],
    "new_count": 2,
    "new_alerts": [
      {
        "alert_id": "alert-004",
        "type": "agent_degradation",
        "agent": "coder-dispatcher",
        "severity": "warning",
        "message": "成功率下降 5%"
      },
      {
        "alert_id": "alert-005",
        "type": "resource_high",
        "resource": "disk",
        "severity": "info",
        "message": "磁盘使用率 68%"
      }
    ]
  }
}
```

### 采集方式

```python
def collect_incident_view():
    return {
        "timestamp": datetime.now().isoformat(),
        "failures": get_recent_failures(),
        "timeouts": get_timeout_stats(),
        "zombies": get_zombie_tasks(),
        "retry_loops": get_retry_loops(),
        "alerts": get_alert_status()
    }
```

---

## L3 Trend View（趋势分析）

### 职责
看趋势：24h/7d 成功率、延迟变化、成本变化、热点技能

### 字段定义

```json
{
  "timestamp": "2026-03-09T21:00:00+08:00",
  "success_rate": {
    "current_24h": 0.85,
    "previous_24h": 0.90,
    "change_percent": -5.6,
    "current_7d": 0.88,
    "previous_7d": 0.89,
    "change_percent_7d": -1.1
  },
  "latency": {
    "p50_24h": 15200,
    "p50_previous_24h": 14800,
    "change_ms": 400,
    "p95_24h": 32000,
    "p95_previous_24h": 28000,
    "change_ms_p95": 4000
  },
  "cost": {
    "total_24h": 0.42,
    "total_previous_24h": 0.38,
    "change_percent": 10.5,
    "total_7d": 2.85,
    "avg_per_task": 0.015
  },
  "hot_skills": [
    {
      "skill": "git-skill",
      "usage_count_24h": 45,
      "success_rate": 0.98,
      "avg_latency_ms": 12000
    },
    {
      "skill": "log-analysis-skill",
      "usage_count_24h": 32,
      "success_rate": 0.95,
      "avg_latency_ms": 18000
    },
    {
      "skill": "pdf-skill",
      "usage_count_24h": 18,
      "success_rate": 0.91,
      "avg_latency_ms": 22000
    }
  ],
  "degrading_skills": [
    {
      "skill": "api-testing-skill",
      "success_rate_24h": 0.60,
      "success_rate_7d": 0.85,
      "change_percent": -29.4,
      "failure_reason": "network_error"
    },
    {
      "skill": "docker-skill",
      "success_rate_24h": 0.70,
      "success_rate_7d": 0.88,
      "change_percent": -20.5,
      "failure_reason": "resource_exhausted"
    }
  ],
  "agent_performance": [
    {
      "agent": "coder-dispatcher",
      "tasks_24h": 52,
      "success_rate_24h": 0.92,
      "success_rate_7d": 0.95,
      "change_percent": -3.2
    },
    {
      "agent": "analyst-dispatcher",
      "tasks_24h": 38,
      "success_rate_24h": 0.89,
      "success_rate_7d": 0.90,
      "change_percent": -1.1
    },
    {
      "agent": "monitor-dispatcher",
      "tasks_24h": 25,
      "success_rate_24h": 0.96,
      "success_rate_7d": 0.96,
      "change_percent": 0.0
    }
  ]
}
```

### 采集方式

```python
def collect_trend_view():
    return {
        "timestamp": datetime.now().isoformat(),
        "success_rate": get_success_rate_trends(),
        "latency": get_latency_trends(),
        "cost": get_cost_trends(),
        "hot_skills": get_hot_skills(),
        "degrading_skills": get_degrading_skills(),
        "agent_performance": get_agent_performance_trends()
    }
```

---

## L4 Diagnosis View（自动诊断）

### 职责
看原因：最弱链路、主要瓶颈、退化来源、优先改哪里

### 字段定义

```json
{
  "timestamp": "2026-03-09T21:00:00+08:00",
  "weakest_link": {
    "component": "coder-dispatcher",
    "type": "agent",
    "issue": "超时次数增加",
    "impact": "导致整体成功率下降 5%",
    "severity": "warning"
  },
  "primary_bottleneck": {
    "component": "api-testing-skill",
    "type": "skill",
    "issue": "网络错误频繁",
    "impact": "成功率从 85% 降至 60%",
    "severity": "critical"
  },
  "degradation_sources": [
    {
      "source": "coder-dispatcher",
      "reason": "超时阈值过低（60s）",
      "evidence": "最近 3 次超时，平均耗时 62s",
      "confidence": 0.85
    },
    {
      "source": "api-testing-skill",
      "reason": "外部 API 不稳定",
      "evidence": "12 次网络错误，集中在 20:00-21:00",
      "confidence": 0.92
    }
  ],
  "top_fix_priority": {
    "rank": 1,
    "component": "api-testing-skill",
    "action": "隔离或降级",
    "reason": "成功率下降 29%，影响最大",
    "expected_improvement": "整体成功率预计提升 3-5%"
  },
  "recommended_actions": [
    {
      "priority": 1,
      "action": "隔离 api-testing-skill",
      "reason": "成功率过低（60%），频繁失败",
      "steps": [
        "将 api-testing-skill 标记为 degraded",
        "暂停新任务路由到该 skill",
        "调查网络错误根因"
      ],
      "expected_improvement": "整体成功率 +3-5%"
    },
    {
      "priority": 2,
      "action": "调整 coder-dispatcher 超时阈值",
      "reason": "当前阈值 60s，实际平均耗时 62s",
      "steps": [
        "将超时阈值从 60s 调整为 90s",
        "观察 24h 超时次数变化"
      ],
      "expected_improvement": "coder-dispatcher 成功率 +2-3%"
    },
    {
      "priority": 3,
      "action": "优化 git-skill 执行逻辑",
      "reason": "使用频率高（45 次/24h），优化收益大",
      "steps": [
        "分析 git-skill 执行日志",
        "识别可优化的步骤",
        "减少不必要的 git 操作"
      ],
      "expected_improvement": "平均延迟 -10-15%"
    }
  ],
  "health_score": {
    "current": 85,
    "previous_24h": 90,
    "change": -5,
    "status": "good",
    "breakdown": {
      "success_rate": 85,
      "latency": 88,
      "resource": 92,
      "stability": 80
    }
  }
}
```

### 采集方式

```python
def collect_diagnosis_view():
    runtime = collect_runtime_view()
    incidents = collect_incident_view()
    trends = collect_trend_view()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "weakest_link": diagnose_weakest_link(runtime, incidents, trends),
        "primary_bottleneck": diagnose_bottleneck(runtime, incidents, trends),
        "degradation_sources": identify_degradation_sources(trends),
        "top_fix_priority": determine_top_fix(incidents, trends),
        "recommended_actions": generate_recommendations(runtime, incidents, trends),
        "health_score": calculate_health_score(runtime, incidents, trends)
    }
```

---

## 完整报告样例

### summary.md

```markdown
# TaijiOS 健康报告

**生成时间：** 2026-03-09 21:00:00 +08:00  
**健康分数：** 85/100 (GOOD)

---

## 🔴 当前最弱链路

**api-testing-skill** - 成功率从 85% 降至 60%（-29%）

**原因：** 外部 API 不稳定，12 次网络错误集中在 20:00-21:00

---

## 🔧 最该优先修什么

**隔离 api-testing-skill**

**步骤：**
1. 将 api-testing-skill 标记为 degraded
2. 暂停新任务路由到该 skill
3. 调查网络错误根因

**预期改善：** 整体成功率 +3-5%

---

## 📊 系统状态

### 当前运行
- 队列长度：3
- 活跃 Agent：2（coder-dispatcher, analyst-dispatcher）
- 平均执行时间：18.5s

### 异常情况
- 失败次数（24h）：5
- 超时次数（24h）：3
- 僵尸任务：0
- 重试循环：1

### 趋势分析
- 成功率（24h）：85% ↓ 5.6%
- 延迟 P95（24h）：32s ↑ 4s
- 成本（24h）：$0.42 ↑ 10.5%

---

## 🎯 推荐行动

1. **隔离 api-testing-skill**（优先级：高）
   - 成功率过低（60%），频繁失败
   - 预期改善：整体成功率 +3-5%

2. **调整 coder-dispatcher 超时阈值**（优先级：中）
   - 当前阈值 60s，实际平均耗时 62s
   - 预期改善：coder-dispatcher 成功率 +2-3%

3. **优化 git-skill 执行逻辑**（优先级：低）
   - 使用频率高（45 次/24h），优化收益大
   - 预期改善：平均延迟 -10-15%

---

**下次报告：** 2026-03-09 22:00:00 +08:00
```

---

## MVP 2 验收标准

报告最后必须能自动产出这 3 句话：

1. ✅ **当前最弱链路是什么**
   - `diagnosis.weakest_link`
   - `summary.md` 第一部分

2. ✅ **最该优先修什么**
   - `diagnosis.top_fix_priority`
   - `summary.md` 第二部分

3. ✅ **修完预期会改善什么**
   - `diagnosis.recommended_actions[0].expected_improvement`
   - `summary.md` 第二部分

---

## 实现建议

### 诊断逻辑

```python
def diagnose_weakest_link(runtime, incidents, trends):
    """识别最弱链路"""
    candidates = []
    
    # 检查 Agent 性能下降
    for agent in trends["agent_performance"]:
        if agent["change_percent"] < -5:
            candidates.append({
                "component": agent["agent"],
                "type": "agent",
                "issue": f"成功率下降 {abs(agent['change_percent'])}%",
                "impact": f"影响 {agent['tasks_24h']} 个任务",
                "severity": "warning" if agent["change_percent"] > -10 else "critical"
            })
    
    # 检查 Skill 退化
    for skill in trends["degrading_skills"]:
        if skill["change_percent"] < -20:
            candidates.append({
                "component": skill["skill"],
                "type": "skill",
                "issue": f"成功率下降 {abs(skill['change_percent'])}%",
                "impact": f"失败原因：{skill['failure_reason']}",
                "severity": "critical"
            })
    
    # 返回影响最大的
    return max(candidates, key=lambda x: abs(x["change_percent"]))
```

### 推荐行动生成

```python
def generate_recommendations(runtime, incidents, trends):
    """生成推荐行动"""
    actions = []
    
    # 检查退化的 Skill
    for skill in trends["degrading_skills"]:
        if skill["success_rate_24h"] < 0.70:
            actions.append({
                "priority": 1,
                "action": f"隔离 {skill['skill']}",
                "reason": f"成功率过低（{skill['success_rate_24h']*100:.0f}%）",
                "steps": [
                    f"将 {skill['skill']} 标记为 degraded",
                    "暂停新任务路由到该 skill",
                    f"调查 {skill['failure_reason']} 根因"
                ],
                "expected_improvement": "整体成功率 +3-5%"
            })
    
    # 检查超时问题
    for agent in incidents["timeouts"]["timeout_agents"]:
        if agent["count"] >= 3:
            actions.append({
                "priority": 2,
                "action": f"调整 {agent['agent']} 超时阈值",
                "reason": f"超时次数 {agent['count']}，平均耗时 {agent['avg_timeout_ms']/1000:.0f}s",
                "steps": [
                    f"将超时阈值从 60s 调整为 90s",
                    "观察 24h 超时次数变化"
                ],
                "expected_improvement": f"{agent['agent']} 成功率 +2-3%"
            })
    
    return sorted(actions, key=lambda x: x["priority"])
```

---

## 采集频率

- **L1 Runtime View** - 每 30 秒（心跳）
- **L2 Incident View** - 每 5 分钟
- **L3 Trend View** - 每 1 小时
- **L4 Diagnosis View** - 每 1 小时

---

## 存储位置

```
C:\Users\A\.openclaw\workspace\aios\agent_system\health_report\
├── runtime.json
├── incidents.json
├── trends.json
├── diagnosis.json
└── summary.md
```

---

## 下一步

1. ✅ 完成字段定义（本文档）
2. ⏭️ 实现采集逻辑
3. ⏭️ 实现诊断逻辑
4. ⏭️ 生成 summary.md

---

**版本：** v0.1  
**状态：** Draft  
**维护者：** 小九 + 珊瑚海
