# AIOS Restore Drill v1.1 Report

**日期：** 2026-03-11 06:47-07:05 GMT+8
**执行者：** 小九
**目标：** 验证"恢复后的系统，能不能按原样工作"

---

## 最终结论

### 生产等价恢复：通过

---

## 5 项等价验证结果

| # | 验证项 | 结果 | 详情 |
|---|--------|------|------|
| 1 | Agent 等价 | ✅ 通过 | 30/30 Agent，13/13 routable，group 分布一致，核心状态零差异 |
| 2 | Memory 等价 | ✅ 通过 | MEMORY.md 完全一致（20,192 bytes），selflearn-state 可加载，daily logs 14/20（备份窗口 14 天） |
| 3 | Heartbeat 等价 | ✅ 通过 | heartbeat_v5.py 内容完全一致（40,681 bytes） |
| 4 | 配置等价 | ✅ 通过 | 6 个配置文件全部 byte-level 一致，learning_agents.py 可加载（27 agents） |
| 5 | 运行时数据等价 | ✅ 通过 | 8 个数据文件全部 byte-level 一致 |

---

## 执行过程

### Phase 1：采集生产基线

采集了生产环境的完整状态快照：
- Agent：30 个（dispatcher:3, learning:27），13 个 routable
- Memory：MEMORY.md 20,192 bytes，20 个 daily logs，22 个 state 文件
- Config：6 个核心脚本全部存在

### Phase 2：发现 backup.py v2.0 的 3 个 bug

在首次恢复验证中发现 backup.py 存在 3 个关键 bug：

**Bug 1：agents.json 路径错误**
- MRS 定义写的是 `agents.json`（根目录旧文件，18,175 bytes）
- 生产实际用的是 `data/agents.json`（新版，20,709 bytes，含 routable 字段）
- 旧文件缺少 routable、lifecycle_state、cooldown_until、timeout 字段
- 导致恢复后 30 个 Agent 全部状态不一致

**Bug 2：MEMORY.md 备份路径逃逸**
- 源路径 `../../MEMORY.md` 能正确解析（MRS 检查通过）
- 但 `dst = backup_dir / "../../MEMORY.md"` 导致文件写到备份目录外
- 结果：备份声称成功，实际文件未落入备份目录

**Bug 3：daily logs 备份源错误**
- `get_recent_memory_files()` 只扫描 `agent_system/memory/`
- 实际 daily logs 在 `workspace/memory/`
- 结果：0 个 daily log 被备份

### Phase 3：修复 backup.py

修复内容：
1. `agents.json` → `data/agents.json`
2. 新增 `WORKSPACE_DIR` 变量和 `workspace_files`/`workspace_patterns` 支持
3. workspace 级别文件备份到 `backup_dir/workspace/` 子目录
4. daily logs 从 workspace/memory 备份，最近 14 天

### Phase 4：修复后重新备份 + 恢复验证

修复后备份文件数从 20 → 34：
- 新增 MEMORY.md（20,192 bytes）
- 新增 14 个 daily logs
- data/agents.json 替代旧 agents.json

在全新隔离环境中恢复并做 byte-level 对比，5 项全部通过。

---

## 差异清单

### 首次验证（修复前）

| 项目 | 生产 | 恢复 | 差异 |
|------|------|------|------|
| agents.json | data/agents.json (20,709B) | agents.json (18,175B) | 旧版本，缺少 routable 等字段 |
| MEMORY.md | 存在 (20,192B) | 不存在 | 备份路径逃逸 bug |
| daily logs | 20 个 | 0 个 | 备份源目录错误 |
| routable agents | 13 | 0 | agents.json 版本不一致导致 |
| core agent diffs | - | - | 30/30 全部不一致 |

### 最终验证（修复后）

| 项目 | 生产 | 恢复 | 差异 |
|------|------|------|------|
| agents.json | 20,709B | 20,709B | ✅ 一致 |
| MEMORY.md | 20,192B | 20,192B | ✅ 一致 |
| daily logs | 20 个 | 14 个 | 6 个超出 14 天备份窗口（预期行为） |
| 6 个配置文件 | - | - | ✅ 全部 byte-level 一致 |
| 8 个数据文件 | - | - | ✅ 全部 byte-level 一致 |

### 已知差距（非缺陷）

- daily logs 只备份最近 14 天（20 个中恢复了 14 个），超出窗口的 6 个文件不在备份范围内
- workspace/memory 下的非日期文件（INDEX.md、模板等）未纳入 MRS

---

## 执行纪律检查

- ✅ 只在隔离环境跑（drill/restore_env_v2）
- ✅ 不借用生产现成文件（从备份目录恢复）
- ✅ 不回写生产状态
- ✅ 对比使用 byte-level 比较，不是 size-only

---

## 关键收获

1. **backup.py v2.0 有 3 个 bug**，全部在本次 Drill 中发现并修复
2. **MRS 检查通过 ≠ 备份正确** — `../../MEMORY.md` 能被 Path 解析但备份时路径逃逸
3. **agents.json 存在新旧两个版本** — 根目录的是旧版，data/ 下的是生产版
4. **修复后 5 项全部通过** — 生产等价恢复验证成功

---

## 恢复能力评估（更新）

- ✅ 数据恢复：通过
- ✅ 状态恢复：通过
- ✅ 最小运行恢复：通过
- ✅ 完整配置恢复：通过
- ✅ 生产等价恢复：通过

**正式定性：**

AIOS 已从"具备 MRS 完整恢复能力，待验证生产等价恢复"升级为"生产等价恢复验证通过"。
