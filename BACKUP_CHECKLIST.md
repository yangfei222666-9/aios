# 太极OS 备份清单 v1.0

**生成时间：** 2026-03-10 19:26  
**目标：** 手动备份到 MacBook（只读副本）

---

## 1. 必须备份（最高优先级）

这些丢了恢复成本最高，必须完整拷贝。

### 1.1 设计资产

**路径：** `docs/`

**为什么重要：**
- 正式规格书（SKILL_AUTO_CREATION_MVP_v1.1_SPEC.md 等）
- 观察期规则和实施计划
- 验收标准和设计冻结基线
- 这些是系统演进的"宪法"，丢了就失去了设计依据

**备份方式：** 完整拷贝整个 `docs/` 目录

---

### 1.2 记忆资产

**路径：** `memory/`

**为什么重要：**
- `MEMORY.md` - 长期记忆，核心决策和原则
- `memory/2026-03-09.md` - 最近几天的日志
- `memory/2026-03-10.md` - 今天的工作记录
- 各类研究报告（hermes-skill-research.md、rabbit-os-research.md 等）
- 这些是系统的"大脑"，记录了所有重要决策和学习成果

**备份方式：** 完整拷贝整个 `memory/` 目录

---

### 1.3 运行资产

**路径：** `aios/agent_system/data/`

**为什么重要：**
- `deduper_shadow_log.jsonl` - 观察期证据
- `task_queue.jsonl` - 待处理任务
- `spawn_pending.jsonl` - 待执行的 spawn 请求
- `lessons.json` - 系统学到的经验
- `agents.json` - Agent 注册和状态
- `selflearn-state.json` - 学习 Agent 状态
- 这些是系统运行的"黑匣子"，丢了就失去了运行历史

**备份方式：** 完整拷贝 `aios/agent_system/data/` 目录

---

### 1.4 系统资产

**路径：** `aios/agent_system/`

**为什么重要：**
- `agents.json` - Agent 注册表
- `lessons.json` - 经验库
- `heartbeat_v5.py` - 心跳主程序
- `learning_agents.py` - 学习 Agent 定义
- 这些是系统的"骨架"，定义了系统如何运行

**备份方式：** 完整拷贝 `aios/agent_system/` 目录（包括子目录）

---

### 1.5 Skill 自动创建项目

**路径：** `skill_auto_creation/`

**为什么重要：**
- 这是当前最重要的在建项目
- 包含模板、stubs、测试骨架、草案注册表
- 丢了就要重新搭建整个框架

**备份方式：** 完整拷贝 `skill_auto_creation/` 目录

---

### 1.6 项目源码本体

**路径：** `aios/`

**为什么重要：**
- 这是太极OS 的核心代码
- 包括所有模块、工具、测试
- 丢了就要从零重建

**备份方式：** 完整拷贝 `aios/` 目录

---

### 1.7 Git 历史（如果有）

**路径：** `.git/`

**为什么重要：**
- 保存了所有提交历史和分支
- 可以回溯到任何历史版本
- 丢了就失去了版本控制能力

**备份方式：** 如果存在 `.git/` 目录，完整拷贝

---

## 2. 建议备份（有价值但不是最核心）

这些不是最核心，但很值得一起带走。

### 2.1 Skills 目录

**路径：** `skills/`

**为什么重要：**
- 所有已安装的 Skill
- 包括自定义 Skill 和第三方 Skill
- 有些 Skill 可能已经做了本地修改

**备份方式：** 完整拷贝 `skills/` 目录

---

### 2.2 测试文件

**路径：** `tests/`

**为什么重要：**
- 测试用例和测试数据
- 可以用来验证系统功能

**备份方式：** 完整拷贝 `tests/` 目录

---

### 2.3 脚本工具

**路径：** `scripts/`

**为什么重要：**
- 各种自动化脚本
- 部署、备份、清理等工具

**备份方式：** 完整拷贝 `scripts/` 目录

---

### 2.4 配置文件

**路径：** 根目录下的配置文件

**为什么重要：**
- `AGENTS.md` - Agent 系统说明
- `SOUL.md` - 系统人格定义
- `USER.md` - 用户信息
- `IDENTITY.md` - 身份定义
- `TOOLS.md` - 工具配置
- `HEARTBEAT.md` - 心跳配置

**备份方式：** 拷贝这些文件

---

### 2.5 研究资料

**路径：** `research/`

**为什么重要：**
- GitHub 学习成果
- 差距分析
- 升级计划

**备份方式：** 完整拷贝 `research/` 目录

---

### 2.6 日常生成的报告

**路径：** `reports/`

**为什么重要：**
- 健康检查报告
- 周报等

**备份方式：** 完整拷贝 `reports/` 目录

---

## 3. 可不备份或最后备份（优先级最低）

这些优先级最低，可以不备份或最后备份。

### 3.1 临时缓存

**路径：**
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`

**原因：** 可再生成，占空间

---

### 3.2 大量可再生成的日志

**路径：** `logs/` 中的大量历史日志

**原因：** 可再生成，占空间

---

### 3.3 临时下载文件

**路径：** `temp/`

**原因：** 临时文件，可重新下载

---

### 3.4 明显过期的一次性输出

**路径：** 各种 `.bak`、`.tmp` 文件

**原因：** 过期或临时文件

---

### 3.5 HTML 覆盖率报告

**路径：** `htmlcov/`

**原因：** 可再生成，占空间很大

---

## 4. 备份操作步骤

### 第一步：创建备份目录

在 MacBook 上创建备份目录：

```bash
mkdir -p ~/TaijiOS-Backup-2026-03-10
cd ~/TaijiOS-Backup-2026-03-10
```

---

### 第二步：拷贝必须备份的内容

从 Windows 机器拷贝到 MacBook（可以用 U 盘、网络共享、或其他方式）：

**必须备份的目录：**
- `docs/`
- `memory/`
- `aios/agent_system/data/`
- `aios/agent_system/`
- `skill_auto_creation/`
- `aios/`
- `.git/`（如果有）

**必须备份的文件：**
- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `IDENTITY.md`
- `TOOLS.md`
- `HEARTBEAT.md`
- `MEMORY.md`

---

### 第三步：拷贝建议备份的内容

**建议备份的目录：**
- `skills/`
- `tests/`
- `scripts/`
- `research/`
- `reports/`

---

### 第四步：验证备份完整性

在 MacBook 上检查：

```bash
# 检查目录是否存在
ls -la ~/TaijiOS-Backup-2026-03-10/docs/
ls -la ~/TaijiOS-Backup-2026-03-10/memory/
ls -la ~/TaijiOS-Backup-2026-03-10/aios/agent_system/data/

# 检查关键文件是否存在
ls -la ~/TaijiOS-Backup-2026-03-10/MEMORY.md
ls -la ~/TaijiOS-Backup-2026-03-10/aios/agent_system/agents.json
ls -la ~/TaijiOS-Backup-2026-03-10/skill_auto_creation/PREPARATION_COMPLETE_REPORT.md
```

---

### 第五步：记录备份信息

在 MacBook 上创建备份说明文件：

```bash
cat > ~/TaijiOS-Backup-2026-03-10/BACKUP_INFO.txt << EOF
太极OS 备份信息

备份时间：2026-03-10 19:26
备份来源：Windows 11 开发机
备份目标：MacBook（只读副本）
备份类型：冷备份（归档保存）

备份内容：
- 设计资产（docs/）
- 记忆资产（memory/）
- 运行资产（aios/agent_system/data/）
- 系统资产（aios/agent_system/）
- Skill 自动创建项目（skill_auto_creation/）
- 项目源码（aios/）
- Git 历史（.git/）
- Skills 目录（skills/）
- 测试文件（tests/）
- 脚本工具（scripts/）
- 配置文件（AGENTS.md, SOUL.md 等）
- 研究资料（research/）

备份说明：
这是观察期内的第一次正式备份。
目的是保护设计资产、记忆资产、运行资产和系统资产。
不以双机开发为目标，仅作为安全备份点。

下一步：
观察期结束后，再决定是否做 Git 仓库同步、iCloud 归档或双机开发。
EOF
```

---

## 5. 备份完成后的检查清单

- [ ] `docs/` 目录完整
- [ ] `memory/` 目录完整
- [ ] `aios/agent_system/data/` 目录完整
- [ ] `aios/agent_system/` 目录完整
- [ ] `skill_auto_creation/` 目录完整
- [ ] `aios/` 目录完整
- [ ] `.git/` 目录完整（如果有）
- [ ] `skills/` 目录完整
- [ ] `tests/` 目录完整
- [ ] `scripts/` 目录完整
- [ ] 配置文件完整（AGENTS.md, SOUL.md 等）
- [ ] `research/` 目录完整
- [ ] `BACKUP_INFO.txt` 已创建

---

## 6. 一句话总结

**现在就值得做，先把 MacBook 当安全备份点，不要急着变成双主机开发环境。**

观察期结束后，再决定下一步。

---

**版本：** v1.0  
**生成时间：** 2026-03-10 19:26  
**维护者：** 小九 + 珊瑚海
