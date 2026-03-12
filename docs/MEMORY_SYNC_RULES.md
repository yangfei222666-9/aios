# 双机记忆同步规则

## 同步范围

### ✅ 同步这些（文档型记忆）
- `MEMORY.md` - 长期记忆
- `memory/*.md` - 每日记录和专题记忆
- `docs/*.md` - 设计文档和指南
- `SOUL.md`, `USER.md`, `TOOLS.md`, `AGENTS.md` - 配置文档
- `skills/` - Skill 定义

### ❌ 不同步这些（运行态账本）
- `data/` - 运行时数据
- `logs/` - 日志文件
- `*.jsonl` - 事件、任务、告警等账本
- `reports/runtime/` - 运行时报告
- `cache/` - 缓存文件

---

## 双机分工

### Windows（主运行机）
- 产生真实运行数据
- 记录每日执行结果
- 更新 `memory/YYYY-MM-DD.md`

### Mac（开发机）
- 整理和归纳长期记忆
- 重构文档和设计
- 更新 `MEMORY.md` 和 `docs/`

---

## 同步频率

- **推荐：** 每天 1-2 次
- **避免：** 高频自动推送（容易冲突）

---

## 同步命令

### Windows 推送
```powershell
cd C:\Users\A\.openclaw\workspace
git add MEMORY.md memory/ docs/ SOUL.md USER.md TOOLS.md AGENTS.md
git commit -m "Update memory: $(Get-Date -Format 'yyyy-MM-dd')"
git push
```

### Mac 拉取
```bash
cd /Users/weiwei/taijios
git pull
```

---

## 冲突处理

1. **同一文件不要两边同时改**
2. **如果冲突：** 手动合并，保留两边的有价值内容
3. **重要修改前：** 先 `git pull` 拉取最新版本

---

## 版本：v1.0
**最后更新：** 2026-03-12
