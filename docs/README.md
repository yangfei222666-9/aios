# 太极OS Dashboard

> 在平衡中演化，在演化中归一

太极OS（TaijiOS）是一个以"阴阳平衡、动态演化、万物归一"为核心理念的个人 AI 操作系统。本项目是太极OS 的可视化监控和管理界面。

---

## 项目简介

太极OS Dashboard 提供了一个直观的 Web 界面，用于：
- 监控系统健康度和运行状态
- 管理 Agent 和查看执行历史
- 查看任务队列和执行结果
- 管理 Skill 和查看使用统计
- 查看系统日志和告警

**核心价值：** 让用户能看见系统在做什么、运行得如何、有什么问题。

---

## 快速开始

### 前置要求

- Node.js >= 16
- npm >= 8 或 yarn >= 1.22

### 安装依赖

```bash
npm install
# 或
yarn install
```

### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

访问 `http://localhost:3000` 查看应用。

### 连接后端 API

后端 API 默认运行在 `http://localhost:8888`。

如需修改，请编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8888
```

---

## 技术栈

### 推荐技术栈

- **框架：** React 18+ / Vue 3+ / Next.js
- **UI 库：** Ant Design / Material-UI / Tailwind CSS
- **图表库：** ECharts / Chart.js / Recharts
- **状态管理：** Redux / Zustand / Pinia
- **HTTP 客户端：** Axios / Fetch API
- **实时通信：** WebSocket / Socket.io

### 项目结构

```
frontend/
├── src/
│   ├── components/       # 通用组件
│   │   ├── Navbar/
│   │   ├── Sidebar/
│   │   ├── Table/
│   │   ├── Chart/
│   │   └── Badge/
│   ├── pages/           # 页面组件
│   │   ├── Dashboard/   # 总览页
│   │   ├── Agents/      # Agent 管理
│   │   ├── Tasks/       # 任务队列
│   │   ├── Skills/      # Skill 管理
│   │   ├── Logs/        # 系统日志
│   │   ├── Alerts/      # 告警管理
│   │   └── Settings/    # 设置
│   ├── services/        # API 服务
│   │   ├── api.js
│   │   ├── agents.js
│   │   ├── tasks.js
│   │   └── skills.js
│   ├── store/           # 状态管理
│   ├── utils/           # 工具函数
│   ├── hooks/           # 自定义 Hooks
│   └── App.jsx
├── public/
└── package.json
```

---

## 开发指南

### 核心页面

1. **总览页（Dashboard）** - `/`
   - 系统健康度
   - 关键指标卡片
   - 趋势图表
   - 最近告警

2. **Agent 管理** - `/agents`
   - Agent 列表
   - Agent 详情
   - 任务历史
   - 趋势图表

3. **任务队列** - `/tasks`
   - 任务列表
   - 任务详情
   - 执行日志

4. **Skill 管理** - `/skills`
   - Skill 列表
   - Skill 详情
   - 使用历史

5. **系统日志** - `/logs`
   - 日志列表
   - 搜索和筛选

6. **告警管理** - `/alerts`
   - 告警列表
   - 告警处理

### API 调用示例

```javascript
// 获取系统健康度
import { getSystemHealth } from '@/services/api';

const health = await getSystemHealth();
console.log(health.health_score); // 85.5

// 获取 Agent 列表
import { getAgents } from '@/services/agents';

const agents = await getAgents({ status: 'active', page: 1, limit: 20 });
console.log(agents.data.agents);
```

### 状态管理示例

```javascript
// Redux 示例
import { useSelector, useDispatch } from 'react-redux';
import { fetchAgents } from '@/store/agentsSlice';

const agents = useSelector(state => state.agents.list);
const dispatch = useDispatch();

useEffect(() => {
  dispatch(fetchAgents());
}, []);
```

### 图表示例

```javascript
// ECharts 示例
import ReactECharts from 'echarts-for-react';

const option = {
  xAxis: { type: 'category', data: ['Mon', 'Tue', 'Wed'] },
  yAxis: { type: 'value' },
  series: [{ data: [120, 200, 150], type: 'line' }]
};

<ReactECharts option={option} />
```

---

## 文档索引

- **[前端需求文档](./FRONTEND_REQUIREMENTS.md)** - 详细的页面和功能需求
- **[API 接口文档](./API_SPEC.md)** - 完整的 REST API 规范
- **[数据模型文档](./DATA_MODELS.md)** - TypeScript 接口定义
- **[UI 设计指南](./UI_DESIGN_GUIDE.md)** - 色彩、字体、组件、布局规范
- **[架构概览](./ARCHITECTURE.md)** - 系统架构和核心组件
- **[项目路线图](./ROADMAP.md)** - 开发计划和里程碑

---

## 开发流程

### 1. 阅读文档
- 先读 `FRONTEND_REQUIREMENTS.md` 了解需求
- 再读 `API_SPEC.md` 了解接口
- 最后读 `UI_DESIGN_GUIDE.md` 了解设计规范

### 2. 搭建项目
- 选择技术栈（推荐 React + Ant Design + ECharts）
- 初始化项目
- 配置路由和状态管理

### 3. 开发页面
- 按优先级开发（总览页 → Agent 管理 → 任务队列 → ...）
- 先做静态页面，再接入 API
- 先做桌面端，再做响应式

### 4. 测试和优化
- 功能测试
- 性能优化
- 响应式适配

---

## 常见问题

### Q: 后端 API 还没准备好怎么办？
A: 可以先用 Mock 数据开发，参考 `API_SPEC.md` 中的响应示例。

### Q: 需要实现所有页面吗？
A: 优先实现核心页面（总览、Agent、任务），其他页面可以后续迭代。

### Q: 设计稿在哪里？
A: 参考 `UI_DESIGN_GUIDE.md`，可以根据规范自由发挥，或使用 Ant Design 的默认样式。

### Q: 需要支持暗色模式吗？
A: 暂时不需要，可以作为后续优化项。

---

## 联系方式

如有问题或建议，欢迎联系。

---

**版本：** v1.0  
**最后更新：** 2026-03-10
