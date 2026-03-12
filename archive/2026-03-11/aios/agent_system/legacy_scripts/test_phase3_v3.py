# test_phase3_v3.py - 端到端测试
from experience_learner_v3 import learner_v3

# 测试1：推荐历史策略（空库）
print("=== Test 1: Recommend from empty DB ===")
task = {
    'error_type': 'timeout',
    'prompt': 'Fix timeout issue in API call'
}
enhanced = learner_v3.recommend(task)
print(f"Enhanced prompt: {enhanced['enhanced_prompt'][:100]}...")

# 测试2：保存成功轨迹
print("\n=== Test 2: Save success trajectory ===")
result = {
    'id': 'task-001',
    'error_type': 'timeout',
    'strategy': 'increase_timeout_and_retry',
    'prompt': 'Fix timeout issue in API call',
    'duration': 15.5,
    'success_rate': 85
}
learner_v3.save_success(result)

# 测试3：再次推荐（应该从库中找到）
print("\n=== Test 3: Recommend from populated DB ===")
task2 = {
    'error_type': 'timeout',
    'prompt': 'Another timeout issue'
}
enhanced2 = learner_v3.recommend(task2)
print(f"Enhanced prompt: {enhanced2['enhanced_prompt'][:100]}...")

print("\n=== All tests passed! ===")
