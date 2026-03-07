# Agent Market Design Document

## 概述

Agent 市场是一个让用户可以分享、发现和下载 Agent 的平台。

## 核心功能

### 1. Agent 打包（Export）
- 将 Agent 配置导出为标准格式（.agent.json）
- 包含：配置、脚本、依赖、文档
- 自动生成 README

### 2. Agent 发布（Publish）
- 上传到本地市场目录
- 生成唯一 ID（agent-name-version）
- 自动验证（语法、依赖、安全）

### 3. Agent 发现（Browse）
- 按类型分类（core/learning/analysis/monitor）
- 按优先级排序（high/normal/low）
- 搜索功能（名称、描述、标签）

### 4. Agent 安装（Install）
- 从市场下载 Agent
- 自动安装依赖
- 集成到 agents.json

### 5. Agent 更新（Update）
- 检查版本更新
- 一键升级
- 保留用户配置

## 文件结构

```
aios/
├── agent_system/
│   ├── agents.json          # 已安装的 Agent
│   ├── agent_market.py      # 市场 CLI
│   └── market/              # 本地市场
│       ├── index.json       # 市场索引
│       └── packages/        # Agent 包
│           ├── coder-v1.0.0/
│           │   ├── agent.json
│           │   ├── script.py
│           │   ├── README.md
│           │   └── requirements.txt
│           └── analyst-v1.0.0/
│               └── ...
```

## 数据格式

### Agent 包格式（.agent.json）

```json
{
  "id": "coder-dispatcher",
  "name": "Coder Dispatcher",
  "version": "1.0.0",
  "author": "小九",
  "description": "Write clean, maintainable Python code",
  "type": "core",
  "role": "Senior Python Developer",
  "goal": "Write clean, maintainable, and well-tested Python code",
  "backstory": "You are an experienced Python developer...",
  "config": {
    "enabled": true,
    "schedule": "on_demand",
    "priority": "high",
    "model": "claude-opus-4-5",
    "thinking": "on",
    "timeout": 120,
    "max_retries": 5
  },
  "script": {
    "path": "coder_dispatcher.py",
    "entry": "main"
  },
  "dependencies": [
    "requests>=2.28.0",
    "python-dotenv>=0.19.0"
  ],
  "tags": ["code", "python", "development"],
  "created_at": "2026-03-04T13:00:00",
  "downloads": 0,
  "rating": 0.0
}
```

### 市场索引格式（index.json）

```json
{
  "agents": [
    {
      "id": "coder-dispatcher",
      "name": "Coder Dispatcher",
      "version": "1.0.0",
      "author": "小九",
      "description": "Write clean, maintainable Python code",
      "type": "core",
      "priority": "high",
      "tags": ["code", "python"],
      "downloads": 0,
      "rating": 0.0,
      "package_path": "packages/coder-v1.0.0"
    }
  ],
  "last_updated": "2026-03-04T13:00:00"
}
```

## CLI 命令

```bash
# 浏览市场
python agent_market.py list

# 搜索 Agent
python agent_market.py search "code"

# 查看详情
python agent_market.py info coder-dispatcher

# 安装 Agent
python agent_market.py install coder-dispatcher

# 导出 Agent
python agent_market.py export coder-dispatcher

# 发布 Agent
python agent_market.py publish ./coder-dispatcher.agent.json

# 更新 Agent
python agent_market.py update coder-dispatcher

# 卸载 Agent
python agent_market.py uninstall coder-dispatcher
```

## 安全机制

1. **代码审查** - 自动扫描恶意代码
2. **沙箱测试** - 安装前测试运行
3. **依赖检查** - 验证依赖安全性
4. **版本控制** - 防止降级攻击
5. **签名验证** - 验证作者身份（未来）

## 实现优先级

### Phase 1（1小时）- MVP
- [x] agent_market.py CLI
- [x] export 命令（导出 Agent）
- [x] list 命令（浏览市场）
- [x] install 命令（安装 Agent）

### Phase 2（30分钟）- 增强
- [ ] search 命令（搜索）
- [ ] info 命令（详情）
- [ ] update 命令（更新）

### Phase 3（30分钟）- 安全
- [ ] 代码扫描
- [ ] 沙箱测试
- [ ] 依赖检查

## 未来扩展

1. **远程市场** - 连接到中心化市场（GitHub/ClawdHub）
2. **评分系统** - 用户评分和评论
3. **自动更新** - 定期检查更新
4. **依赖管理** - 自动解决依赖冲突
5. **版本回滚** - 一键回滚到旧版本
