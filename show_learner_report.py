import json

# 读取学习报告
with open(r'C:\Users\A\.openclaw\workspace\aios\agent_system\data\knowledge\learning_20260224_190825.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print('=== AIOS Learner Agent 首次运行报告 ===')
print()

# 显示建议
suggestions = report.get('suggestions', [])
print(f'生成了 {len(suggestions)} 条改进建议：')
for i, sug in enumerate(suggestions, 1):
    priority = sug['priority']
    desc = sug['description']
    print(f'{i}. [{priority}] {desc}')

print()

# 显示学习成果
learning = report.get('learning', {})
print('学习成果：')
print(f'  - 分析了 {learning.get("agents", {}).get("total_agents", 0)} 个 Agent')
print(f'  - 识别了 {len(learning.get("error_patterns", {}).get("patterns", []))} 个错误模式')
print(f'  - 评估了 {learning.get("optimizations", {}).get("total_optimizations", 0)} 个优化')
