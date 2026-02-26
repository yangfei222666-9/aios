# ReleaseManager Agent - 使用指南

## 概述

ReleaseManager 是 AIOS 的发布管理 Agent，负责 ARAM 项目的一键发布流程。

**核心功能：**
1. ✅ 版本管理 - 自动递增版本号（major/minor/patch）
2. ✅ 质量门禁 - 检查必需文件、Git 状态
3. ✅ 打包发布 - 生成 .zip 文件
4. ✅ GitHub 发布 - 创建 Release + 上传附件
5. ✅ 回滚机制 - 发布失败自动回滚

## 快速开始

### 1. 检查发布条件

```bash
python release_manager.py check
```

**检查项：**
- ✅ 必需文件存在（aram_helper.py, aram_data.json, README.md, 启动提示器.bat）
- ✅ Git 状态（如果项目有 Git）

### 2. 构建发布包

```bash
python release_manager.py build
```

**输出：**
- `data/releases/ARAM-Helper-vX.Y.Z.zip`
- 包含所有必需文件 + version.txt

### 3. 完整发布流程

```bash
# Patch 版本（默认）
python release_manager.py release

# Minor 版本
python release_manager.py release minor

# Major 版本
python release_manager.py release major
```

**流程：**
1. 检查质量门禁
2. 递增版本号
3. 构建发布包
4. 发布到 GitHub（创建 tag + Release）
5. 更新 version.json

### 4. 回滚

```bash
python release_manager.py rollback
```

**回滚到上一个 Git tag。**

## 版本号规则

遵循 [Semantic Versioning](https://semver.org/)：

- **Major (X.0.0)** - 不兼容的 API 变更
- **Minor (0.X.0)** - 向后兼容的功能新增
- **Patch (0.0.X)** - 向后兼容的 Bug 修复

**示例：**
- `v1.0.0` → `v1.0.1` (patch)
- `v1.0.1` → `v1.1.0` (minor)
- `v1.1.0` → `v2.0.0` (major)

## 配置

### 项目路径

编辑 `release_manager.py`：

```python
PROJECT_ROOT = Path(r"C:\Users\A\Desktop\ARAM-Helper")
```

### GitHub 仓库

```python
GITHUB_REPO = "yangfei222666-9/ARAM-Helper"  # 格式：owner/repo
```

### 质量门禁

```python
QUALITY_GATES = {
    "min_test_coverage": 0.0,  # 最低测试覆盖率
    "max_cost_per_release": 0.5,  # 每次发布最大成本（美元）
    "max_build_time": 60,  # 最大构建时间（秒）
    "required_files": [  # 必需文件
        "aram_helper.py",
        "aram_data.json",
        "README.md",
        "启动提示器.bat"
    ]
}
```

## 文件结构

```
aios/agent_system/
├── release_manager.py          # 主程序
├── test_release_manager.py     # 测试
├── data/
│   └── releases/
│       └── ARAM-Helper-vX.Y.Z.zip  # 发布包
└── version.json                # 版本信息（自动生成）
```

## version.json 格式

```json
{
  "major": 1,
  "minor": 0,
  "patch": 1,
  "build": 5,
  "tag": "v1.0.1",
  "released_at": "2026-02-26T12:00:00",
  "changelog": []
}
```

## GitHub 发布要求

### 1. 安装 GitHub CLI

```bash
# Windows (Scoop)
scoop install gh

# 或下载安装包
# https://cli.github.com/
```

### 2. 认证

```bash
gh auth login
```

### 3. 初始化 Git 仓库（如果还没有）

```bash
cd C:\Users\A\Desktop\ARAM-Helper
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yangfei222666-9/ARAM-Helper.git
git push -u origin main
```

## 集成到 AIOS

### 1. 通过 Orchestrator 调用

```python
from collaboration.orchestrator import Orchestrator

orchestrator = Orchestrator()

# 创建发布计划
plan = orchestrator.create_plan(
    task="发布 ARAM Helper v1.1.0",
    subtasks=[
        {
            "role": "release_manager",
            "goal": "检查质量门禁",
            "command": "python release_manager.py check"
        },
        {
            "role": "release_manager",
            "goal": "构建发布包",
            "command": "python release_manager.py build"
        },
        {
            "role": "release_manager",
            "goal": "发布到 GitHub",
            "command": "python release_manager.py release minor"
        }
    ]
)
```

### 2. 通过 Heartbeat 自动发布

编辑 `HEARTBEAT.md`：

```markdown
## 每周发布检查（周五）

if today.weekday() == 4:  # 周五
    check_release_conditions()
    if ready_to_release:
        trigger_release_manager()
```

## 数据收集

所有发布活动自动记录到 `data/events/events.jsonl`：

```json
{
  "timestamp": "2026-02-26T12:00:00",
  "event_type": "task",
  "task_id": "build_v1.0.1",
  "task_type": "build",
  "status": "success",
  "duration_ms": 1234,
  "metadata": {
    "version": "v1.0.1",
    "package_size": 20000,
    "files_count": 5
  }
}
```

## 故障排查

### 问题：质量门禁失败

**原因：** 缺少必需文件

**解决：**
1. 检查 `PROJECT_ROOT` 路径是否正确
2. 确认所有必需文件存在

### 问题：Git 检查失败

**原因：** 项目没有初始化 Git

**解决：**
- ReleaseManager 会自动跳过 Git 检查（如果 `.git` 目录不存在）
- 或者初始化 Git：`git init`

### 问题：GitHub 发布失败

**原因：** 未安装 `gh` CLI 或未认证

**解决：**
1. 安装 `gh`：`scoop install gh`
2. 认证：`gh auth login`
3. 确认仓库存在：`gh repo view yangfei222666-9/ARAM-Helper`

### 问题：构建时间过长

**原因：** 文件太多或网络慢

**解决：**
- 调整 `QUALITY_GATES["max_build_time"]`
- 排除不必要的文件

## 最佳实践

### 1. 发布前检查清单

- [ ] 所有测试通过
- [ ] 更新 CHANGELOG.md
- [ ] 更新 README.md（如果有新功能）
- [ ] 提交所有更改到 Git
- [ ] 运行 `python release_manager.py check`

### 2. 版本号选择

- **Bug 修复** → patch
- **新功能（向后兼容）** → minor
- **破坏性变更** → major

### 3. 发布频率

- **Patch** - 随时（Bug 修复）
- **Minor** - 每周或每两周（新功能）
- **Major** - 每季度或每半年（重大变更）

### 4. 回滚策略

- 发布后立即测试
- 如果发现问题，立即回滚：`python release_manager.py rollback`
- 修复问题后重新发布

## 未来改进

### Phase 1（已完成）
- ✅ 版本管理
- ✅ 质量门禁
- ✅ 打包发布
- ✅ GitHub 集成

### Phase 2（计划中）
- [ ] 自动生成 CHANGELOG
- [ ] 集成 CostGuardian（成本控制）
- [ ] 集成 Evaluator（回归测试）
- [ ] 自动通知（Telegram/Discord）

### Phase 3（未来）
- [ ] 多平台发布（PyPI, npm, Docker Hub）
- [ ] A/B 测试支持
- [ ] 灰度发布
- [ ] 自动回滚（基于监控指标）

## 相关文档

- [AIOS ROADMAP](../ROADMAP.md)
- [Orchestrator v2.0](../collaboration/orchestrator.py)
- [DataCollector](./data_collector.py)
- [CostGuardian](./cost_guardian.py)
- [Evaluator](./evaluator.py)

---

**版本：** v1.0  
**最后更新：** 2026-02-26  
**维护者：** 小九 + 珊瑚海
