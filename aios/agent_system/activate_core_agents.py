#!/usr/bin/env python3
"""
AIOS 核心 Agent 自动激活脚本
7 个核心 Agent 自动注册并开始工作
"""
import json
from pathlib import Path
from datetime import datetime

AGENTS_DATA_FILE = Path(__file__).parent / "agents_data.json"

# 7 个核心 Agent 配置
CORE_AGENTS = [
    {
        "id": "coder-agent",
        "template": "coder",
        "name": "代码开发专员",
        "description": "负责编写、调试、重构代码",
        "status": "active",
        "workspace": "~/.openclaw/agents/coder-agent",
        "skills": ["coding-agent", "github"],
        "tools": {
            "allow": ["exec", "read", "write", "edit", "web_search", "web_fetch"],
            "deny": ["message", "cron", "gateway"]
        },
        "system_prompt": "你是代码开发专员。职责：编写高质量代码、调试修复 bug、重构优化、遵循最佳实践。优先处理 code 类型任务。",
        "model": "claude-opus-4-6",
        "thinking": "medium",
        "priority": "high",
        "task_types": ["code", "debug", "refactor"]
    },
    {
        "id": "analyst-agent",
        "template": "analyst",
        "name": "数据分析专员",
        "description": "负责数据分析、根因分析、报告生成",
        "status": "active",
        "workspace": "~/.openclaw/agents/analyst-agent",
        "skills": [],
        "tools": {
            "allow": ["exec", "read", "write", "web_search"],
            "deny": ["message", "cron", "gateway", "edit"]
        },
        "system_prompt": "你是数据分析专员。职责：分析数据趋势、根因分析、生成报告、提供洞察。处理 analysis 类型任务。",
        "model": "claude-sonnet-4-6",
        "thinking": "low",
        "priority": "normal",
        "task_types": ["analysis", "report", "insight"]
    },
    {
        "id": "monitor-agent",
        "template": "monitor",
        "name": "系统监控专员",
        "description": "负责系统健康检查、性能监控、资源告警",
        "status": "active",
        "workspace": "~/.openclaw/agents/monitor-agent",
        "skills": ["system-resource-monitor"],
        "tools": {
            "allow": ["exec", "read", "web_fetch"],
            "deny": ["write", "edit", "message", "cron", "gateway"]
        },
        "system_prompt": "你是系统监控专员。职责：实时监控资源（CPU/内存/磁盘）、发现异常告警、提供优化建议。处理 monitor 类型任务。",
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "task_types": ["monitor", "health-check", "alert"]
    },
    {
        "id": "reactor-agent",
        "template": "reactor",
        "name": "自动修复专员",
        "description": "负责自动修复失败、执行 Playbook、熔断恢复",
        "status": "active",
        "workspace": "~/.openclaw/agents/reactor-agent",
        "skills": [],
        "tools": {
            "allow": ["exec", "read", "write", "edit"],
            "deny": ["message", "cron", "gateway"]
        },
        "system_prompt": "你是自动修复专员。职责：检测失败事件、执行 Playbook 自动修复、熔断器管理、验证修复效果。处理 fix 类型任务。",
        "model": "claude-sonnet-4-6",
        "thinking": "medium",
        "priority": "critical",
        "task_types": ["fix", "recover", "playbook"]
    },
    {
        "id": "evolution-agent",
        "template": "evolution",
        "name": "进化引擎",
        "description": "负责 Self-Improving Loop、策略优化、A/B 测试",
        "status": "active",
        "workspace": "~/.openclaw/agents/evolution-agent",
        "skills": [],
        "tools": {
            "allow": ["read", "write", "exec"],
            "deny": ["message", "cron", "gateway"]
        },
        "system_prompt": "你是进化引擎。职责：分析失败模式、生成改进策略、自动应用优化、A/B 测试验证、自动回滚。处理 evolution 类型任务。",
        "model": "claude-sonnet-4-6",
        "thinking": "high",
        "priority": "normal",
        "task_types": ["evolution", "optimize", "learn"]
    },
    {
        "id": "researcher-agent",
        "template": "researcher",
        "name": "信息研究专员",
        "description": "负责信息搜索、知识提取、技术调研",
        "status": "active",
        "workspace": "~/.openclaw/agents/researcher-agent",
        "skills": ["github"],
        "tools": {
            "allow": ["web_search", "web_fetch", "read", "write"],
            "deny": ["exec", "edit", "message", "cron", "gateway"]
        },
        "system_prompt": "你是信息研究专员。职责：搜索收集信息、整理归纳资料、技术调研、知识积累。处理 research 类型任务。",
        "model": "claude-sonnet-4-6",
        "thinking": "low",
        "priority": "normal",
        "task_types": ["research", "search", "knowledge"]
    },
    {
        "id": "designer-agent",
        "template": "designer",
        "name": "架构设计师",
        "description": "负责架构设计、系统优化、技术选型",
        "status": "active",
        "workspace": "~/.openclaw/agents/designer-agent",
        "skills": [],
        "tools": {
            "allow": ["read", "write", "web_search", "web_fetch"],
            "deny": ["exec", "edit", "message", "cron", "gateway"]
        },
        "system_prompt": "你是架构设计师。职责：架构设计、系统优化、技术选型、性能调优、可扩展性设计。处理 design 类型任务。",
        "model": "claude-opus-4-6",
        "thinking": "high",
        "priority": "normal",
        "task_types": ["design", "architecture", "optimization"]
    }
]

def activate_core_agents():
    """激活所有核心 Agent"""
    print("[START] AIOS 核心 Agent 激活开始...")
    
    # 读取现有数据
    if AGENTS_DATA_FILE.exists():
        with open(AGENTS_DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"summary": {"total_agents": 0, "active": 0, "archived": 0, "total_tasks_processed": 0}, "agents": []}
    
    existing_ids = {agent["id"] for agent in data["agents"]}
    
    # 添加核心 Agent
    activated = 0
    for agent in CORE_AGENTS:
        if agent["id"] in existing_ids:
            print(f"  ⏭️  {agent['name']} 已存在，跳过")
            continue
        
        # 添加时间戳和统计
        agent["created_at"] = datetime.now().isoformat()
        agent["updated_at"] = datetime.now().isoformat()
        agent["stats"] = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 0.0,
            "avg_duration_sec": 0,
            "total_duration_sec": 0,
            "last_active": None
        }
        agent["task_description"] = None
        
        data["agents"].append(agent)
        activated += 1
        print(f"  [OK] {agent['name']} 已激活")
    
    # 更新统计
    data["summary"]["total_agents"] = len(data["agents"])
    data["summary"]["active"] = sum(1 for a in data["agents"] if a["status"] == "active")
    data["summary"]["archived"] = sum(1 for a in data["agents"] if a["status"] == "archived")
    
    # 保存
    with open(AGENTS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] 激活完成！共激活 {activated} 个核心 Agent")
    print(f"[REPORT] 当前状态：总计 {data['summary']['total_agents']} 个 Agent，活跃 {data['summary']['active']} 个")
    print("\n[TARGET] Agent 分工：")
    print("  - coder-agent → 优先处理 code 任务")
    print("  - analyst-agent → 处理 analysis 任务")
    print("  - monitor-agent → 实时监控资源")
    print("  - reactor-agent → 自动修复失败")
    print("  - evolution-agent → Self-Improving Loop")
    print("  - researcher-agent → 知识积累")
    print("  - designer-agent → 架构优化")
    print("\n[IDEA] 下一步：运行 python heartbeat_runner.py 开始工作")

if __name__ == "__main__":
    activate_core_agents()
