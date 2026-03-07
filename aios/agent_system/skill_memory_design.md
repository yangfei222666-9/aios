# Skill Memory 设计文档

> 让技能成为有记忆、可演化的知识单元

**设计时间：** 2026-03-07  
**灵感来源：** MemOS Skill Memory for cross-task skill reuse and evolution

---

## 核心理念

**技能不只是代码，而是带有记忆的可演化实体。**

传统 Skill 系统：
```
Skill = 函数 + 文档
```

Skill Memory 系统：
```
Skill = 函数 + 文档 + 使用历史 + 成功模式 + 失败教训 + 演化轨迹
```

---

## 架构设计

### 1. 数据结构

**skill_memory.jsonl** - 每个 Skill 的记忆条目
```json
{
  "skill_id": "pdf-skill",
  "skill_name": "PDF 处理工具",
  "skill_path": "C:\\Users\\A\\.openclaw\\workspace\\skills\\pdf-skill",
  "version": "1.2.0",
  "created_at": "2026-02-15T10:30:00",
  "last_used": "2026-03-07T14:20:00",
  "usage_count": 47,
  "success_count": 43,
  "failure_count": 4,
  "success_rate": 0.915,
  "avg_execution_time_ms": 1250,
  "evolution_score": 87.5,
  "tags": ["pdf", "document", "extraction"],
  "dependencies": ["PyPDF2", "pdfplumber"],
  "common_patterns": [
    {
      "pattern": "extract_text",
      "usage_count": 28,
      "success_rate": 0.96
    },
    {
      "pattern": "merge_pdfs",
      "usage_count": 12,
      "success_rate": 0.83
    }
  ],
  "failure_lessons": [
    {
      "error_type": "encoding_error",
      "count": 3,
      "last_seen": "2026-03-05T09:15:00",
      "recovery_strategy": "try_multiple_encodings"
    }
  ],
  "related_skills": ["document-agent", "file-organizer-skill"],
  "user_feedback": [
    {
      "timestamp": "2026-03-01T16:00:00",
      "rating": 5,
      "comment": "PDF 合并功能很好用"
    }
  ]
}
```

**skill_executions.jsonl** - 每次 Skill 执行记录
```json
{
  "execution_id": "exec-20260307-142030-001",
  "skill_id": "pdf-skill",
  "task_id": "task-20260307-142030",
  "command": "python pdf_cli.py extract input.pdf",
  "started_at": "2026-03-07T14:20:30",
  "completed_at": "2026-03-07T14:20:31",
  "duration_ms": 1200,
  "status": "success",
  "input_params": {
    "file": "input.pdf",
    "action": "extract"
  },
  "output_summary": "Extracted 15 pages, 8500 words",
  "error": null,
  "context": {
    "agent": "document-agent",
    "user_intent": "提取 PDF 文本"
  }
}
```

### 2. 核心功能

#### 2.1 自动记录（Auto-Tracking）
- 每次 Skill 调用自动记录到 skill_executions.jsonl
- 每小时聚合更新 skill_memory.jsonl 统计
- 无需人工干预

#### 2.2 成功模式识别（Pattern Recognition）
- 分析 skill_executions.jsonl，识别高频成功模式
- 自动提取 common_patterns（如 "extract_text" 成功率 96%）
- 为未来任务推荐最佳实践

#### 2.3 失败教训积累（Failure Learning）
- 记录每次失败的 error_type 和 recovery_strategy
- 下次遇到同类错误自动应用历史恢复策略
- 与 LowSuccess_Agent 联动

#### 2.4 技能演化追踪（Evolution Tracking）
- 每个 Skill 有独立的 evolution_score（0-100）
- 基于成功率、使用频率、用户反馈计算
- 低分技能自动触发优化建议

#### 2.5 跨任务复用（Cross-Task Reuse）
- 识别相似任务场景，推荐历史成功的 Skill 组合
- 例如："PDF 提取 + 文本分析" 组合成功率 92%

---

## 实现计划

### Phase 1: 基础记录（2小时）
- [ ] 创建 skill_memory.py（核心模块）
- [ ] 实现 track_execution() - 记录每次执行
- [ ] 实现 update_skill_stats() - 聚合统计
- [ ] 集成到 task_executor.py（自动调用）

### Phase 2: 模式识别（3小时）
- [ ] 实现 analyze_patterns() - 识别成功模式
- [ ] 实现 extract_failure_lessons() - 提取失败教训
- [ ] 每日自动分析（集成到 daily_metrics.py）

### Phase 3: 智能推荐（4小时）
- [ ] 实现 recommend_skill() - 根据任务推荐最佳 Skill
- [ ] 实现 recommend_recovery() - 失败时推荐恢复策略
- [ ] 集成到 Router 和 LowSuccess_Agent

### Phase 4: 演化系统（5小时）
- [ ] 实现 calculate_skill_evolution_score() - 计算技能演化分数
- [ ] 实现 suggest_skill_improvements() - 自动生成优化建议
- [ ] 集成到 Self-Improving Loop

---

## 核心价值

1. **技能可观测性** - 每个 Skill 的使用情况一目了然
2. **自动优化** - 低分技能自动触发改进
3. **失败恢复** - 历史失败教训自动应用
4. **智能推荐** - 根据任务自动推荐最佳 Skill
5. **跨任务学习** - 从历史成功中学习最佳实践

---

## 与现有系统集成

### 与 LowSuccess_Agent 联动
```python
# LowSuccess_Agent 重生失败任务时
recovery_strategy = skill_memory.recommend_recovery(
    skill_id="pdf-skill",
    error_type="encoding_error"
)
# 返回：try_multiple_encodings（历史成功策略）
```

### 与 Router 联动
```python
# Router 路由任务时
best_skill = skill_memory.recommend_skill(
    task_description="提取 PDF 文本",
    context={"file_type": "pdf"}
)
# 返回：pdf-skill（成功率 91.5%，使用 47 次）
```

### 与 Evolution Score 联动
```python
# 计算全局 Evolution Score 时
skill_scores = skill_memory.get_all_evolution_scores()
global_evolution_score = weighted_average(skill_scores)
# 技能级别的演化分数融入全局评分
```

---

## 预期效果

- **技能成功率提升 10%+** - 通过历史模式推荐最佳实践
- **失败恢复时间减少 50%+** - 自动应用历史恢复策略
- **技能优化自动化** - 低分技能自动触发改进建议
- **完整可观测性** - 每个技能的生命周期全程追踪

---

*设计者：小九 + 珊瑚海*  
*版本：v1.0*
