# 太极OS 自我改进标准流程 (SOP v1.0)

**基于:** 2026-03-11 首次成功闭环  
**状态:** 生产就绪

---

## 流程概览

```
分析 → 执行 → 发现 → 更新 → 报告
```

## 详细步骤

### 1. 系统状态分析

**目标:** 识别改进点

**执行:**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'
& "C:\Program Files\Python312\python.exe" -X utf8 scripts/analyze_improvement.py
```

**输出:**
- `data/self_improvement_plan.json` - 改进计划
- 控制台输出 - 改进点列表

**验收标准:**
- 至少识别出 1 个 P0 或 P1 改进点
- 改进计划文件生成成功

---

### 2. 执行学习 Agent

**目标:** 运行学习 Agent，发现问题

**可用 Agent:**
- `Bug_Hunter` - 发现系统 Bug
- `Code_Reviewer` - 审查代码质量
- `Error_Analyzer` - 分析错误日志
- `GitHub_Researcher` - 研究 GitHub 项目

**执行示例:**
```bash
# Bug Hunter
& "C:\Program Files\Python312\python.exe" -X utf8 scripts/run_bug_hunter.py

# Code Reviewer
& "C:\Program Files\Python312\python.exe" -X utf8 scripts/run_code_reviewer.py
```

**输出:**
- 控制台报告
- `data/agent_execution_record.jsonl` - 执行记录（追加）

**验收标准:**
- Agent 执行成功（exit code 0）
- 执行记录写入成功
- 报告格式完整

---

### 3. 问题排查与修复

**目标:** 处理发现的问题

**流程:**

1. **问题分级**
   - HIGH - 立即处理
   - MEDIUM - 计划处理
   - LOW - 记录备案

2. **排查步骤**
   - 确认问题真实性
   - 定位根本原因
   - 评估影响范围
   - 制定修复方案

3. **修复验证**
   - 实施修复
   - 重新运行相关 Agent
   - 确认问题解决

**文档:**
- 为 HIGH 问题创建排查报告（`reports/xxx_investigation.md`）

---

### 4. 更新系统状态

**目标:** 同步改进结果到系统状态

**需要更新的文件:**

1. **agents.json** - Agent 验证状态
   ```python
   agent['validation_status'] = 'validated'
   agent['validation_date'] = datetime.now().isoformat()
   agent['execution_script'] = 'run_xxx.py'
   ```

2. **selflearn-state.json** - 学习系统状态
   ```python
   state['validated_learning_agents_count'] = X
   state['updated_at'] = datetime.now().isoformat()
   ```

**执行:**
```bash
# 使用辅助脚本
& "C:\Program Files\Python312\python.exe" -X utf8 scripts/update_selflearn_state.py
```

**验收标准:**
- 状态文件更新成功
- 数据一致性检查通过

---

### 5. 生成改进报告

**目标:** 记录改进过程和结果

**报告结构:**

```markdown
# 太极OS 自我改进报告

**生成时间:** YYYY-MM-DD HH:MM

## 改进概览
- 完成的工作
- 核心成果

## 改进前后对比
- 关键指标变化

## 发现的问题
- 按优先级分类

## 下一步行动
- 建议的后续改进

## 文件清单
- 新增/修改的文件
```

**输出位置:**
- `reports/self_improvement_YYYY-MM-DD.md` - 详细报告
- `memory/YYYY-MM-DD.md` - 简要记录

**验收标准:**
- 报告完整
- 数据准确
- 可读性强

---

## 质量检查清单

每次闭环完成后，检查以下项目：

- [ ] 改进计划已生成
- [ ] 至少 1 个 Agent 成功执行
- [ ] 发现的问题已分级
- [ ] HIGH 问题已排查
- [ ] 系统状态已更新
- [ ] 改进报告已生成
- [ ] 执行记录完整

---

## 常见问题

### Q: Agent 执行失败怎么办？
A: 检查执行日志，确认：
1. Python 环境正确
2. 编码设置正确（UTF-8）
3. 依赖文件存在
4. 权限充足

### Q: 发现的问题太多怎么办？
A: 优先处理 HIGH 问题，其他问题记录到 backlog。

### Q: 如何判断闭环成功？
A: 满足以下条件：
1. 至少 1 个 Agent 执行成功
2. 发现至少 1 个真实问题或改进点
3. 系统状态成功更新
4. 报告完整生成

---

## 版本历史

- **v1.0** (2026-03-11) - 基于首次成功闭环创建
  - 5 个标准步骤
  - 质量检查清单
  - 常见问题解答

---

**维护者:** 小九  
**最后更新:** 2026-03-11
