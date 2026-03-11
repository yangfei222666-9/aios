"""验证 GitHub_Researcher 4 项预检"""

import json
from pathlib import Path

print('=== 4 项预检验证 ===\n')

# 1. registered
agents_file = Path('data/agents.json')
if agents_file.exists():
    data = json.load(open(agents_file, encoding='utf-8'))
    gr = next((a for a in data['agents'] if a['name'] == 'GitHub_Researcher'), None)
    print(f'1. registered: {"✅" if gr else "❌"} {"(已注册)" if gr else "(未注册)"}')
    registered = bool(gr)
else:
    print('1. registered: ❌ (agents.json 不存在)')
    registered = False

# 2. executable
exec_script = Path('run_github_researcher.py')
executable = exec_script.exists()
print(f'2. executable: {"✅" if executable else "❌"} {"(有可执行入口)" if executable else "(无可执行入口)"}')

# 3. writeback-ready
memory_dir = Path('../memory')
writeback_ready = memory_dir.exists()
print(f'3. writeback-ready: {"✅" if writeback_ready else "❌"} {"(有可写回路径)" if writeback_ready else "(无可写回路径)"}')

# 4. traceable
exec_record = Path('data/agent_execution_record.jsonl')
traceable = exec_record.exists()
print(f'4. traceable: {"✅" if traceable else "❌"} {"(有可追溯执行记录)" if traceable else "(无可追溯执行记录)"}')

print('\n=== 预检结果 ===')
all_pass = all([registered, executable, writeback_ready, traceable])
print(f'状态: {"✅ 全部通过" if all_pass else "❌ 未全部通过"}')

if all_pass:
    print('\nGitHub_Researcher 已满足首次验收前置条件，可以进入正式验收。')
else:
    print('\nGitHub_Researcher 未满足全部前置条件，需要补齐后再验收。')
