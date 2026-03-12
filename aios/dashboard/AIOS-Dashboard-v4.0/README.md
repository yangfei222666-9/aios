# 太极OS Dashboard v4.0

基于 AdminLTE v4 设计语言的全新仪表盘。

## 特性

- **AdminLTE v4 风格**：采用 Bootstrap 5 + AdminLTE 设计系统
- **暗色主题**：专业的暗色界面，太极OS 品牌色（青色 + 翠绿）
- **响应式布局**：完美适配桌面、平板、手机
- **实时数据**：3 秒自动刷新，实时监控系统状态
- **丰富组件**：
  - KPI 卡片（活跃 Agent、Evolution Score、今日改进、成功率）
  - Agent 状态表格
  - 系统健康度图表（Chart.js）
  - 任务队列面板
  - 实时日志滚动
  - Skills 列表卡片

## 快速开始

### 启动服务器

双击 `start.bat` 或运行：

```bash
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v4.0
python server.py
```

### 访问地址

http://127.0.0.1:8889

### 端口说明

- v3.4: 8888
- v4.0: 8889（避免冲突）

## API 端点

- `/api/metrics` - 系统指标（KPI、Agent 状态、趋势数据）
- `/api/skills` - Skills 列表
- `/api/hexagram_timeline` - 卦象时间线
- `/api/logs` - 实时日志

## 技术栈

- **前端**：Bootstrap 5.3.3 + Bootstrap Icons + Chart.js 4.4.1
- **后端**：Python 3.12 + http.server
- **设计**：AdminLTE v4 Design System

## 设计理念

参考 AdminLTE v4 的设计语言：
- 左侧可折叠侧边栏
- 顶部导航栏（搜索、通知、用户信息）
- 卡片式布局
- 平滑动画和过渡效果
- 专业的暗色主题

## 与 v3.4 的区别

| 特性 | v3.4 | v4.0 |
|------|------|------|
| 设计系统 | Tailwind CSS | Bootstrap 5 + AdminLTE |
| 端口 | 8888 | 8889 |
| 布局 | 自定义 | AdminLTE 标准布局 |
| 主题 | 暗色 | AdminLTE 暗色主题 |
| 图表 | 自定义 | Chart.js |

## 开发

修改 `index.html` 后刷新浏览器即可看到效果。

修改 `server.py` 后需要重启服务器。

## 许可

© 2026 太极OS. All rights reserved.
