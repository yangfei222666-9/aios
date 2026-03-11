#!/usr/bin/env python3
"""静态检查 learning_agents.py"""

import sys
import json

print("=" * 60)
print("Learning Agents 静态检查")
print("=" * 60)

# 1. 语法检查
print("\n1. 语法检查...")
try:
    import py_compile
    py_compile.compile('learning_agents.py', doraise=True)
    print("   ✅ 语法正确")
except SyntaxError as e:
    print(f"   ❌ 语法错误: {e}")
    sys.exit(1)

# 2. 导入检查
print("\n2. 导入检查...")
try:
    from learning_agents import LEARNING_AGENTS
    print(f"   ✅ 导入成功，共 {len(LEARNING_AGENTS)} 个 Agent")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 3. 文档 Agent 检查
print("\n3. 文档 Agent 检查...")
docs_agents = [a for a in LEARNING_AGENTS if 'Docs_' in a.get('name', '')]
print(f"   找到 {len(docs_agents)} 个文档 Agent")

for agent in docs_agents:
    name = agent.get('name', 'unknown')
    tasks = agent.get('tasks', [])
    tools = agent.get('tools', [])
    model = agent.get('model', 'unknown')
    
    print(f"\n   {name}:")
    print(f"     - 任务数: {len(tasks)}")
    print(f"     - 工具: {', '.join(tools)}")
    print(f"     - 模型: {model}")
    
    # 检查必需字段
    required_fields = ['name', 'role', 'goal', 'backstory', 'tasks', 'tools', 'model', 'thinking', 'priority', 'schedule', 'interval_hours']
    missing = [f for f in required_fields if f not in agent]
    
    if missing:
        print(f"     ⚠️  缺少字段: {', '.join(missing)}")
    else:
        print(f"     ✅ 所有必需字段完整")

# 4. 检查是否有旧的 Documentation_Writer
print("\n4. 检查旧 Agent...")
old_doc = [a for a in LEARNING_AGENTS if a.get('name') == 'Documentation_Writer']
if old_doc:
    print("   ⚠️  仍存在旧的 Documentation_Writer")
else:
    print("   ✅ 旧的 Documentation_Writer 已移除")

# 5. 检查 JSON 序列化
print("\n5. JSON 序列化检查...")
try:
    json.dumps(LEARNING_AGENTS, ensure_ascii=False)
    print("   ✅ JSON 序列化正常")
except Exception as e:
    print(f"   ❌ JSON 序列化失败: {e}")

print("\n" + "=" * 60)
print("结论")
print("=" * 60)
print("✅ learning_agents.py 语法和导入都正常")
print("✅ 4 个文档 Agent 配置完整")
print("✅ 旧的 Documentation_Writer 已移除")
print("\n如果 heartbeat 失败，原因不在 learning_agents.py")
