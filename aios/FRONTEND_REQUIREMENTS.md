# 太极OS 前端需求文档 v1.0

## 1. 项目概述

### 1.1 项目定位

太极OS Dashboard 是一个实时监控和管理个人 AI 操作系统的 Web 应用。

**核心价值：**
- 可视化系统状态（健康度、进化分数）
- 实时监控 Agent 和任务
- 查看事件日志和指标
- 管理任务队列
- 查看经验库和改进历史

### 1.2 技术栈

**当前版本（v3.4）：**
- 后端：Python + FastAPI
- 前端：原生 HTML + CSS + JavaScript
- 实时通信：WebSocket
- 数据存储：JSONL 文件

**未来版本（v4.0）：**
- 前端框架：React / Vue / Svelte（待定）
- 状态管理：Redux / Vuex / Zustand
- UI 组件库：Ant Design / Element Plus / Shadcn UI
- 图表库：ECharts / Chart.js / Recharts
- 构建工具：Vite

---

## 2. 功能需求

### 2.1 首页（Dashboard）

**核心指标卡片：**
- 健康度（Health Score）- 0-100，颜色编码（绿/黄/红）
- 进化分数（Evolution Score）- 0-100
- 任务统计（待处理/执行中/已完成/失败）
- Agent 统计（总数/活跃/空闲）

**实时图表：**
- 任务完成趋势（过去 24 小时）
- Agent 利用率（过去 24 小时）
- 成功率趋势（过去 7 天）

**快速操作：**
- 提交新任务
- 查看待处理任务
- 查看最近事件

### 2.2 任务管理（Tasks）

**任务列表：**
- 表格展示（ID / 类型 / 描述 / 优先级 / 状态 / 创建时间）
- 筛选（按状态、类型、优先级）
- 搜索（按描述）
- 排序（按创建时间、优先级）

**任务详情：**
- 基本信息（ID、类型、描述、优先级、状态）
- 执行信息（分配的 Agent、开始时间、结束时间、耗时）
- 相关事件（任务生命周期中的所有事件）
- 执行日志（如果有）

**任务操作：**
- 提交新任务（表单：类型、描述、优先级）
- 取消任务（仅待处理状态）
- 重试任务（仅失败状态）

### 2.3 Agent 管理（Agents）

**Agent 列表：**
- 卡片展示（名称 / 状态 / 成功率 / 任务数）
- 筛选（按状态、类型）
- 搜索（按名称）

**Agent 详情：**
- 基本信息（ID、名称、类型、状态）
- 能力列表（capabilities）
- 配置信息（model、timeout、max_retries）
- 统计数据（任务完成数、失败数、成功率、平均耗时）
- 最近任务（最近 10 个任务）
- 活跃时间线（过去 24 小时）

**Agent 操作：**
- 启动 Agent（仅离线状态）
- 停止 Agent（仅活跃/空闲状态）
- 重启 Agent
- 编辑配置（高级功能）

### 2.4 事件日志（Events）

**事件列表：**
- 表格展示（时间 / 类型 / Agent / 数据）
- 筛选（按类型、Agent、时间范围）
- 搜索（按内容）
- 实时更新（WebSocket）

**事件详情：**
- 完整 JSON 数据（格式化展示）
- 相关任务（如果有）
- 相关 Agent

**事件类型标识：**
- 不同类型用不同颜色/图标
- task_completed - 绿色 ✓
- task_failed - 红色 ✗
- agent_started - 蓝色 ▶
- improvement_applied - 黄色 ⚡

### 2.5 指标监控（Metrics）

**系统指标：**
- 健康度趋势（过去 7 天）
- 进化分数趋势（过去 7 天）
- 任务吞吐量（每小时任务数）
- 成功率趋势

**Agent 指标：**
- 各 Agent 成功率对比（柱状图）
- 各 Agent 平均耗时对比（柱状图）
- Agent 利用率（饼图）

**任务指标：**
- 任务类型分布（饼图）
- 任务优先级分布（饼图）
- 任务状态分布（饼图）

**时间范围选择：**
- 过去 1 小时
- 过去 24 小时
- 过去 7 天
- 过去 30 天
- 自定义范围

### 2.6 经验库（Lessons）

**经验列表：**
- 卡片展示（标题 / 分类 / 严重程度 / 有效性）
- 筛选（按分类、严重程度）
- 搜索（按标题、问题、解决方案）
- 排序（按应用时间、有效性）

**经验详情：**
- 标题
- 分类和严重程度
- 问题描述
- 解决方案
- 衍生规则
- 有效性评分
- 应用时间
- 影响的 Agent
- 相关任务

### 2.7 系统设置（Settings）

**通用设置：**
- 主题（亮色/暗色）
- 语言（中文/英文）
- 时区
- 刷新频率

**通知设置：**
- 任务完成通知
- 任务失败通知
- Agent 错误通知
- 系统告警通知

**高级设置：**
- API 端点配置
- WebSocket 配置
- 数据保留策略
- 备份设置

---

## 3. 非功能需求

### 3.1 性能要求

- 首屏加载时间 < 2 秒
- 页面切换响应时间 < 500ms
- WebSocket 消息延迟 < 100ms
- 支持 1000+ 事件的流畅滚动
- 图表渲染时间 < 1 秒

### 3.2 兼容性要求

**浏览器支持：**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**屏幕分辨率：**
- 最小：1280x720
- 推荐：1920x1080
- 支持：4K

**响应式设计：**
- 桌面端优先
- 平板适配（可选）
- 移动端适配（未来版本）

### 3.3 可访问性要求

- 支持键盘导航
- 支持屏幕阅读器
- 颜色对比度符合 WCAG AA 标准
- 支持字体缩放

### 3.4 安全要求

- 仅本地访问（127.0.0.1）
- 未来支持 HTTPS
- 未来支持认证（API Key / JWT）
- 敏感数据脱敏

---

## 4. UI/UX 设计要求

### 4.1 设计原则

- **简洁明了** - 信息层级清晰，避免过度设计
- **实时反馈** - 操作立即响应，状态实时更新
- **一致性** - 统一的颜色、字体、间距、图标
- **易用性** - 常用功能易于访问，减少点击次数

### 4.2 颜色规范

**主色调：**
- 主色：#1890ff（蓝色）
- 成功：#52c41a（绿色）
- 警告：#faad14（黄色）
- 错误：#f5222d（红色）
- 信息：#1890ff（蓝色）

**中性色：**
- 文本主色：#262626
- 文本次色：#595959
- 文本辅助：#8c8c8c
- 边框：#d9d9d9
- 背景：#f0f2f5

**暗色模式：**
- 背景：#141414
- 卡片：#1f1f1f
- 文本：#e8e8e8

### 4.3 字体规范

**字体家族：**
- 中文：PingFang SC, Microsoft YaHei
- 英文：-apple-system, BlinkMacSystemFont, Segoe UI, Roboto
- 代码：Consolas, Monaco, Courier New

**字体大小：**
- 标题 1：24px
- 标题 2：20px
- 标题 3：16px
- 正文：14px
- 辅助文本：12px

### 4.4 间距规范

**基础间距单位：** 8px

**常用间距：**
- 极小：4px
- 小：8px
- 中：16px
- 大：24px
- 极大：32px

### 4.5 组件规范

**按钮：**
- 主按钮：蓝色背景，白色文字
- 次按钮：白色背景，蓝色边框
- 危险按钮：红色背景，白色文字
- 文字按钮：无背景，蓝色文字

**卡片：**
- 白色背景（暗色模式：#1f1f1f）
- 1px 边框（#d9d9d9）
- 8px 圆角
- 16px 内边距

**表格：**
- 斑马纹（奇数行浅灰背景）
- 悬停高亮
- 固定表头
- 支持排序

**图表：**
- 统一配色方案
- 支持交互（悬停、点击）
- 支持导出（PNG / SVG）

---

## 5. 数据交互

### 5.1 API 调用

**基础配置：**
```javascript
const API_BASE = 'http://127.0.0.1:8888/api';

async function fetchData(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}
```

**错误处理：**
- 网络错误：显示重试按钮
- 服务器错误：显示错误信息
- 超时：显示超时提示

### 5.2 WebSocket 连接

**连接管理：**
```javascript
const ws = new WebSocket('ws://127.0.0.1:8888/ws');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleRealtimeUpdate(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // 自动重连
  setTimeout(connectWebSocket, 5000);
};
```

**断线重连：**
- 自动重连（最多 5 次）
- 重连间隔：5 秒
- 显示连接状态

### 5.3 数据缓存

**缓存策略：**
- 静态数据（Agent 列表）：缓存 5 分钟
- 动态数据（任务列表）：缓存 30 秒
- 实时数据（事件日志）：不缓存

**缓存实现：**
```javascript
const cache = new Map();

async function getCachedData(key, fetcher, ttl = 60000) {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data;
  }
  
  const data = await fetcher();
  cache.set(key, { data, timestamp: Date.now() });
  return data;
}
```

---

## 6. 开发规范

### 6.1 代码规范

**命名规范：**
- 组件：PascalCase（TaskList, AgentCard）
- 函数：camelCase（fetchTasks, handleSubmit）
- 常量：UPPER_SNAKE_CASE（API_BASE, MAX_RETRIES）
- CSS 类：kebab-case（task-list, agent-card）

**文件结构：**
```
src/
├── components/       # 组件
│   ├── TaskList.jsx
│   ├── AgentCard.jsx
│   └── ...
├── pages/           # 页面
│   ├── Dashboard.jsx
│   ├── Tasks.jsx
│   └── ...
├── utils/           # 工具函数
│   ├── api.js
│   ├── websocket.js
│   └── ...
├── styles/          # 样式
│   ├── global.css
│   ├── variables.css
│   └── ...
└── App.jsx          # 入口
```

### 6.2 测试要求

**单元测试：**
- 覆盖率 > 80%
- 测试工具：Jest / Vitest

**集成测试：**
- 关键流程测试
- 测试工具：Cypress / Playwright

**E2E 测试：**
- 核心功能测试
- 测试工具：Playwright

### 6.3 文档要求

**组件文档：**
- Props 说明
- 使用示例
- 注意事项

**API 文档：**
- 接口说明
- 请求/响应示例
- 错误码说明

---

## 7. 交付物

### 7.1 开发阶段

**Phase 1（MVP）：**
- 首页（核心指标）
- 任务列表
- Agent 列表
- 事件日志

**Phase 2（完整功能）：**
- 任务详情和操作
- Agent 详情和操作
- 指标监控
- 经验库

**Phase 3（优化）：**
- 性能优化
- 响应式设计
- 暗色模式
- 国际化

### 7.2 文档交付

- 用户手册
- 开发文档
- API 文档
- 部署文档

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-10
