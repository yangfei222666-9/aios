import json

with open(r'C:\Users\A\.openclaw\workspace\aios\agent_system\data\evolution\reports\evolution_20260224_183823.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

learn = report['phases']['learn']
print('=== Learn 阶段 ===')
print('新策略数:', learn['new_strategies'])
print('最佳实践数:', learn['best_practices'])
print()

print('=== 策略详情 ===')
for i, strategy in enumerate(learn['strategy_details'], 1):
    print(f'\n策略 {i}:')
    print(json.dumps(strategy, ensure_ascii=False, indent=2))
