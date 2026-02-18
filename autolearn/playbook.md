# Autolearn Playbook
# 自主学习系统操作手册

## 流程概览
```
错误发生 → inbox.md 记录 → triage 分类 → 生成 lesson → 写入 playbook → 复测验证 → 归档
```

## 1. 错误捕获 (Capture)
当我犯错或被用户纠正时：
1. 立即在 `autolearn/inbox.md` 添加一条记录
2. 包含：场景、原因、正确做法、严重度
3. 状态标记为 `pending`

## 2. 分类处理 (Triage)
运行 `autolearn/scripts/triage.py` 或手动处理：
1. 读取 inbox.md 中 status=pending 的条目
2. 判断类别：powershell | path | encoding | permission | data | ui | tool_limitation
3. 生成结构化 lesson 写入 `memory/lessons.json`
4. 如果是用户纠正，同步更新 `memory/corrections.json`
5. 将 inbox.md 中的状态改为 `processed`

## 3. 规则提炼 (Derive)
从 lessons 中提炼通用规则：
1. 同类错误出现 2 次以上 → 提炼为 `rules_derived`
2. 规则写入 `memory/lessons.json` 的 `rules_derived` 数组
3. 高严重度的单次错误也可直接提炼规则

## 4. 复测验证 (Verify)
对每条新 lesson 生成一个复测命令：
1. 构造一个会触发同类错误的场景
2. 用正确做法执行
3. 验证通过 → lesson 标记 `verified: true`
4. 验证失败 → 回到 triage 重新分析

## 5. 会话启动检查 (Session Boot)
每次新会话开始时：
1. 读 `memory/lessons.json` → `rules_derived`
2. 读 `memory/corrections.json` → `user_preferences`
3. 当前任务涉及相关 category 时，主动回顾对应教训

## 6. 定期维护 (Maintenance)
通过 HEARTBEAT.md 每 3 天触发：
1. 清理已 verified 的 inbox 条目
2. 合并重复 lessons
3. 更新 MEMORY.md 中的教训摘要
