# Pattern Detection Report

**检测时间：** 2026-03-11 07:39
**时间窗口：** 30d
**数据源：** C:\Users\A\.openclaw\workspace\aios\agent_system\data
**发现模式：** 4 个

## Top 3 模式

### #1 resource_exhausted (频次: 63, 影响: critical)

**影响 Agent：** analyst, coder, monitor
**影响 Skill：** analysis, code, monitor, stress, tool
**首次出现：** 2026-03-03T05:07:58.909483+00:00
**最近出现：** 2026-03-07T01:31:21.843458+00:00

**证据样本：**
- task=task-1772432675004-77f0560c, agent=monitor, status=completed
- task=task-1772436675081-89f03360, agent=monitor, status=completed
- task=task-1772436942140-5c231e6e, agent=monitor, status=completed

**建议修复方向：** 清理磁盘空间、增加内存限制、优化资源使用

---

### #2 timeout (频次: 16, 影响: critical)

**影响 Agent：** analyst, coder
**影响 Skill：** analysis, code, tool
**首次出现：** 2026-03-05T12:13:53.753578+00:00
**最近出现：** 2026-03-06T04:36:13.387802+00:00

**证据样本：**
- task=gen-20260305180810-2022, agent=coder, status=completed
- task=gen-20260305180810-1391, agent=coder, status=completed
- task=gen-20260305180810-2351, agent=coder, status=completed

**建议修复方向：** 增加超时时间、拆分大任务、检查外部依赖响应速度

---

### #3 network_error (频次: 9, 影响: high)

**影响 Agent：** analyst, coder, monitor
**影响 Skill：** analysis, code, monitor, stress, tool
**首次出现：** 2026-03-05T12:20:08.544385+00:00
**最近出现：** 2026-03-05T23:27:17.730233+00:00

**证据样本：**
- task=gen-20260305180810-6597, agent=coder, status=completed
- task=gen-20260305180810-5743, agent=coder, status=completed
- task=gen-20260305180810-9481, agent=coder, status=completed

**建议修复方向：** 检查网络连接、验证 API endpoint、添加重试机制

---

