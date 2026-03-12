# Dashboard v3.4 vs v4.0 对比

## 快速对比

| 特性 | v3.4 | v4.0 |
|------|------|------|
| **设计系统** | Tailwind CSS 自定义 | Bootstrap 5 + AdminLTE v4 |
| **端口** | 8888 | 8889 |
| **主题** | 暗色（自定义） | AdminLTE 暗色主题 |
| **布局** | 自定义网格 | AdminLTE 标准布局 |
| **侧边栏** | 固定 | 可折叠（AdminLTE 风格） |
| **图表库** | 自定义 | Chart.js 4.4.1 |
| **响应式** | 基础 | 完整（Bootstrap 5） |
| **图标** | 自定义 | Bootstrap Icons |
| **文件大小** | 较小 | 较大（单文件包含所有样式） |

## v4.0 新特性

### 1. AdminLTE v4 设计语言
- 专业的企业级 UI 设计
- 左侧可折叠侧边栏（点击汉堡菜单切换）
- 顶部导航栏（搜索、通知、用户信息）
- 统一的卡片设计风格

### 2. 更丰富的交互
- 平滑的动画和过渡效果
- 悬停效果（卡片、按钮、导航）
- 响应式布局（完美适配手机、平板、桌面）

### 3. 更专业的数据可视化
- Chart.js 图表（Evolution Score + 成功率趋势）
- 实时更新（3 秒刷新）
- 系统资源监控（CPU、内存、磁盘、GPU）

### 4. 太极OS 品牌色
- 青色（#22d3ee）+ 翠绿（#34d399）
- 渐变效果
- 统一的视觉语言

## 使用建议

### 日常使用
- **v4.0**：推荐用于日常监控，界面更专业，交互更流畅

### 开发调试
- **v3.4**：轻量级，适合快速调试

### 演示展示
- **v4.0**：更适合对外展示，视觉效果更好

## 同时运行

两个版本可以同时运行（端口不冲突）：

```bash
# 终端 1：启动 v3.4
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4
python server.py
# 访问 http://127.0.0.1:8888

# 终端 2：启动 v4.0
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v4.0
python server.py
# 访问 http://127.0.0.1:8889
```

## API 兼容性

两个版本使用相同的 API 端点：
- `/api/metrics` - 系统指标
- `/api/skills` - Skills 列表
- `/api/hexagram_timeline` - 卦象时间线
- `/api/logs` - 实时日志

## 未来计划

v4.0 后续可能增加的功能：
- [ ] Agent 实时控制（启动/停止/重启）
- [ ] Skill 升级为 Agent（一键部署）
- [ ] 卦象时间线可视化
- [ ] 任务队列管理
- [ ] 实时性能分析
- [ ] 告警通知系统

---

© 2026 太极OS
