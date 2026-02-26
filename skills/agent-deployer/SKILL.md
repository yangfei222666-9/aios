---
name: agent-deployer
description: Deploy Skills as AIOS Agents. Automatically generates Agent configurations from SKILL.md and integrates them into the AIOS Agent System. Use when you want to turn a Skill into an executable Agent that can be scheduled and managed by AIOS.
---

# Agent Deployer

**将 Skill 配置转换为 AIOS Agent 的自动化工具。**

## 核心功能

1. **读取 Skill 配置** - 解析 `skill.yaml`
2. **生成 System Prompt** - 基于 description + parameters 自动生成
3. **注入 Agent 配置** - 写入 `agents.json`
4. **一键部署** - 立即可用

## 使用方法

### 1. 部署 Skill 为 Agent

```bash
python agent_deployer.py deploy <skill_dir>
```

**示例：**
```bash
# 部署 document-agent
python agent_deployer.py deploy document-agent

# 或使用绝对路径
python agent_deployer.py deploy C:\Users\A\.openclaw\workspace\skills\document-agent
```

### 2. 列出已部署的 Agents

```bash
python agent_deployer.py list
```

**输出示例：**
```
📋 已部署的 Skill-based Agents (3 个):

  • document_agent (v1.0.0)
    类型: analysis | 状态: active | 完成任务: 15

  • web_scraper (v1.0.0)
    类型: automation | 状态: active | 完成任务: 8
```

### 3. 移除 Agent

```bash
python agent_deployer.py remove <agent_name>
```

**示例：**
```bash
python agent_deployer.py remove document_agent
```

## Skill 配置格式

每个 Skill 目录需要包含 `skill.yaml` 配置文件：

```yaml
name: web_scraper
version: 1.0.0
category: automation

description: |
  抓取指定 URL 的网页内容，提取纯文本或 HTML。
  适用场景：监控网页变化、提取文章内容、数据采集。

parameters:
  - name: url
    type: string
    required: true
    description: 要抓取的网页 URL
  
  - name: format
    type: string
    required: false
    default: text
    enum: [text, html, markdown]
    description: 输出格式

execution:
  type: python
  entry: scraper.py
  command: "python scraper.py --url {url} --format {format}"
  
  sandbox:
    network: true
    filesystem: read-only
    timeout: 60

output:
  type: text
  success_pattern: "^SUCCESS:"
  error_pattern: "^ERROR:"

examples:
  - input:
      url: "https://example.com"
      format: "text"
    output: "SUCCESS: 抓取到 1234 字符"

metadata:
  author: 小九
  created: 2026-02-26
  tags: [web, scraping, automation]
```

## 生成的 Agent 配置

部署后，Agent 配置会自动注入到 `aios/agent_system/agents.json`：

```json
{
  "name": "web_scraper",
  "type": "automation",
  "role": "web_scraper Specialist",
  "goal": "抓取指定 URL 的网页内容，提取纯文本或 HTML。",
  "backstory": "专门负责 web_scraper 相关任务的 Agent，基于 Skill 自动生成。",
  "system_prompt": "...",
  "execution": {
    "type": "python",
    "entry": "C:\\Users\\A\\.openclaw\\workspace\\skills\\web_scraper\\scraper.py",
    "command": "python scraper.py --url {url} --format {format}",
    "sandbox": {
      "network": true,
      "filesystem": "read-only",
      "timeout": 60
    }
  },
  "metadata": {
    "source": "skill",
    "skill_dir": "C:\\Users\\A\\.openclaw\\workspace\\skills\\web_scraper",
    "created": "2026-02-26T15:56:00",
    "version": "1.0.0",
    "author": "小九",
    "tags": ["web", "scraping", "automation"]
  },
  "state": {
    "status": "active",
    "tasks_completed": 0,
    "tasks_failed": 0,
    "last_active": null
  }
}
```

## 工作流程

```
Skill 配置 (skill.yaml)
    ↓
agent_deployer.py
    ↓
生成 System Prompt
    ↓
注入 agents.json
    ↓
AIOS 自动加载
    ↓
Agent 可用！
```

## 优势

1. **降低创建门槛** - 写个脚本 + 配置文件 = Agent
2. **标准化** - 统一的配置格式和 Prompt 生成规则
3. **可复用** - Skill 可以独立分享，一键部署
4. **可追溯** - metadata 记录来源、版本、作者
5. **易维护** - 修改 Skill 配置后重新部署即可

## 注意事项

1. **配置文件必须存在** - `skill.yaml` 是必需的
2. **名称唯一性** - 同名 Agent 会被覆盖
3. **路径正确性** - `execution.entry` 必须指向有效文件
4. **沙盒配置** - 根据 Skill 需求合理配置权限

## 下一步

- [ ] 沙盒执行引擎（隔离运行，捕获输出）
- [ ] 依赖自动安装（检测 requirements.txt）
- [ ] 测试框架（自动验证 examples）
- [ ] 版本管理（支持多版本共存）
- [ ] 热重载（修改配置后自动重新部署）

## 文件结构

```
agent-deployer/
├── agent_deployer.py    # 核心脚本
├── SKILL.md             # 本文档
└── skill.yaml           # 示例配置（可选）
```

## 依赖

- Python 3.8+
- PyYAML

安装依赖：
```bash
pip install pyyaml
```

---

**版本：** v1.0.0  
**作者：** 小九  
**创建日期：** 2026-02-26
