# 太极OS 文档索引

> 统一文档入口 - 快速找到你需要的内容

本文档提供太极OS（TaijiOS）项目的完整文档索引，包含安装部署、API 接口、使用教程三大核心部分。

---

## 📦 安装与部署

### 快速开始
太极OS Dashboard 是一个基于 Web 的可视化监控和管理界面。支持本地开发和生产部署。

**前置要求：** Node.js >= 16, npm >= 8 或 yarn >= 1.22

**快速安装：**
```bash
npm install
npm run dev
```

访问 `http://localhost:3000` 查看应用。后端 API 默认运行在 `http://localhost:8888`。

**详细文档：**
- [README.md](./README.md) - 项目简介、快速开始、开发指南
- [MACOS_DEPLOYMENT_README.md](./MACOS_DEPLOYMENT_README.md) - MacBook 部署资源包索引
- [MACOS_DEPLOYMENT.md](./MACOS_DEPLOYMENT.md) - macOS 完整部署指南（系统要求、安装步骤、配置、故障排查）
- [MACOS_DEPLOYMENT_CHECKLIST.md](./MACOS_DEPLOYMENT_CHECKLIST.md) - 部署检查清单（部署前检查、步骤清单、功能测试）
- [MACOS_QUICK_REFERENCE.md](./MACOS_QUICK_REFERENCE.md) - macOS 快速参考手册

---

## 🔌 API 接口文档

### API 概览
太极OS 提供 RESTful API 接口，用于系统状态查询、Agent 管理、任务调度、Skill 管理等核心功能。

**Base URL：** `http://localhost:8888/api`

**认证方式：** 当前版本暂不需要认证（本地开发环境）

**通用响应格式：**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-03-10T19:00:00Z"
}
```

**核心 API 模块：**
- 系统状态 API - 健康度、运行时信息、资源使用
- Agent 管理 API - 列表查询、详情、历史记录
- 任务队列 API - 任务列表、创建、取消、重试
- Skill 管理 API - Skill 列表、详情、使用统计
- 日志与告警 API - 日志查询、告警列表、告警确认

**详细文档：**
- [API_SPEC.md](./API_SPEC.md) - 完整 API 接口规范（包含所有端点、请求/响应格式、错误码）

---

## 📚 使用教程与设计指南

### 架构与设计
太极OS 以"阴阳平衡、动态演化、万物归一"为核心理念，提供模块化、可扩展的 AI 操作系统架构。

**核心概念：**
- Agent - 智能代理，执行具体任务
- Skill - 可复用的能力模块
- Task - 任务单元，由 Agent 执行
- Memory - 记忆系统，支持长期学习

**教程与指南：**
- [UI_DESIGN_GUIDE.md](./UI_DESIGN_GUIDE.md) - UI 设计指南（色彩方案、组件规范、布局原则、响应式设计）
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构文档
- [DATA_MODELS.md](./DATA_MODELS.md) - 数据模型定义
- [ROADMAP.md](./ROADMAP.md) - 项目路线图
- [PUBLIC_INTRO.md](./PUBLIC_INTRO.md) - 公开介绍文档

### 高级主题
- [AIOS_VS_STANDARD_AGENT.md](./AIOS_VS_STANDARD_AGENT.md) - AIOS 与标准 Agent 对比
- [TAIJIOS_5_LAYER_ARCHITECTURE_v0.1.md](./TAIJIOS_5_LAYER_ARCHITECTURE_v0.1.md) - 五层架构设计
- [tai_ji_os_architecture.md](./tai_ji_os_architecture.md) - 太极OS 架构详解
- [Taiji_OS_Learning_System_v1.md](./Taiji_OS_Learning_System_v1.md) - 学习系统设计

### Skill 系统
- [SKILL_TRIGGER_DESIGN.md](./SKILL_TRIGGER_DESIGN.md) - Skill 触发机制设计
- [SKILL_AUTO_CREATION_MVP.md](./SKILL_AUTO_CREATION_MVP.md) - Skill 自动创建 MVP
- [SKILL_ROUTER_ACCEPTANCE.md](./SKILL_ROUTER_ACCEPTANCE.md) - Skill 路由验收标准
- [TASK_REPLAY_SKILL_SPEC.md](./TASK_REPLAY_SKILL_SPEC.md) - 任务回放 Skill 规范

### 内容生产与运营
- [CONTENT_PRODUCTION_SOP.md](./CONTENT_PRODUCTION_SOP.md) - 内容生产标准操作流程
- [xiaohongshu_aios_intro.md](./xiaohongshu_aios_intro.md) - 小红书 AIOS 介绍

---

## 📋 完成报告与验收文档

项目各模块的完成报告和验收标准：

- [FINAL_COMPLETION_REPORT.md](./FINAL_COMPLETION_REPORT.md) - 最终完成报告
- [MEMORY_MODULE_COMPLETION_REPORT.md](./MEMORY_MODULE_COMPLETION_REPORT.md) - 记忆模块完成报告
- [PLANNING_MODULE_COMPLETION_REPORT.md](./PLANNING_MODULE_COMPLETION_REPORT.md) - 规划模块完成报告
- [PLANNING_INTEGRATION_COMPLETION_REPORT.md](./PLANNING_INTEGRATION_COMPLETION_REPORT.md) - 规划集成完成报告
- [DECIDE_AND_DISPATCH_ACCEPTANCE.md](./DECIDE_AND_DISPATCH_ACCEPTANCE.md) - 决策与调度验收
- [POLICY_DECISION_ACCEPTANCE.md](./POLICY_DECISION_ACCEPTANCE.md) - 策略决策验收

---

## 🔍 其他文档

### 可观测性与监控
- [4_LAYER_OBSERVABILITY_FIELDS_v0.1.md](./4_LAYER_OBSERVABILITY_FIELDS_v0.1.md) - 四层可观测性字段设计
- [design-alert-fsm.md](./design-alert-fsm.md) - 告警状态机设计

### Agent 生命周期
- [agent_first_life_signals_checklist.md](./agent_first_life_signals_checklist.md) - Agent 首次生命信号检查清单
- [SPAWN_CONTRACT_DESIGN.md](./SPAWN_CONTRACT_DESIGN.md) - Spawn 契约设计
- [SPAWN_LOCK_48H_REVIEW.md](./SPAWN_LOCK_48H_REVIEW.md) - Spawn 锁定 48 小时回顾

### 前端开发
- [FRONTEND_REQUIREMENTS.md](./FRONTEND_REQUIREMENTS.md) - 前端需求文档

### 知识库
- [LLM_AGENT_KNOWLEDGE.md](./LLM_AGENT_KNOWLEDGE.md) - LLM Agent 知识库
- [INTEL_GITHUB_2026-03-06.md](./INTEL_GITHUB_2026-03-06.md) - GitHub 情报（2026-03-06）

---

## 📞 获取帮助

- **项目主页：** [太极OS Dashboard](./README.md)
- **问题反馈：** 请在项目 Issue 中提交
- **贡献指南：** 参见 README.md 中的贡献部分

---

**最后更新：** 2026-03-10  
**文档版本：** v1.0
