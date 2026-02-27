# MCP Tutorial - LangChain + LangGraph + MCP Protocol
# 基于通义千问的智能 Agent 系统

## 项目结构
```
mcp-tutorial/
├── requirements.txt          # 依赖
├── .env                      # 环境变量（API Keys）
├── mcp_servers/              # MCP Server 实现
│   ├── weather_server.py     # 天气查询
│   ├── write_server.py       # 文件操作
│   └── amap_server.py        # 高德地图
├── agent/                    # Agent 实现
│   ├── react_agent.py        # ReAct Agent
│   └── memory.py             # 记忆管理
├── api/                      # FastAPI 服务
│   └── main.py               # API 入口
└── tests/                    # 测试
    └── test_agent.py
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
创建 `.env` 文件：
```
DASHSCOPE_API_KEY=your_tongyi_key
OPENWEATHER_API_KEY=your_weather_key
AMAP_API_KEY=your_amap_key
```

### 3. 启动 MCP Servers
```bash
python mcp_servers/weather_server.py
python mcp_servers/write_server.py
python mcp_servers/amap_server.py
```

### 4. 运行 Agent
```bash
python agent/react_agent.py
```

### 5. 启动 API 服务
```bash
uvicorn api.main:app --reload
```

## 核心概念

### MCP (Model Context Protocol)
- 统一的工具接口协议
- 工具即插即用
- 双向读写（vs RAG 单向只读）

### ReAct 工作流
1. 用户输入
2. LLM 推理（选工具）
3. 调用工具
4. 获取结果
5. 生成回复

### 三个 MCP Server
- **Weather Server**: OpenWeather API
- **Write Server**: 本地文件系统
- **AMap Server**: 高德地图（SSE 协议）

## 对比 AIOS

| 维度 | MCP Tutorial | AIOS |
|------|-------------|------|
| Agent 框架 | LangGraph ReAct | EventBus + Scheduler |
| 工具协议 | MCP 标准 | Skill 自定义 |
| 记忆 | InMemorySaver | DataCollector + Storage |
| 自我进化 | ❌ | ✅ Self-Improving Loop |
| 质量保障 | ❌ | ✅ Quality Gates |
| 监控 | ❌ | ✅ Heartbeat + Metrics |

## 下一步

- [ ] 跑通基础示例
- [ ] 对比性能和效果
- [ ] 评估是否给 AIOS 加 MCP 支持
