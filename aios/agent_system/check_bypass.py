import os, re, glob

bypass_patterns = [
    r"agent\['status'\]",
    r'agent\["status"\]',
    r"agent\.get\('status'",
    r'agent\.get\("status"',
    r"skill\['status'\]",
    r'skill\["status"\]',
    r"skill\.get\('status'",
    r'skill\.get\("status"',
    r"task\['status'\]",
    r'task\["status"\]',
    r"task\.get\('status'",
    r'task\.get\("status"',
]

exclude_files = [
    'status_adapter.py',
    'test_status_regression.py',
    'check_bypass.py',
]

violations = []
checked_files = 0

for py_file in glob.glob('**/*.py', recursive=True):
    filename = os.path.basename(py_file)
    if filename in exclude_files:
        continue
    try:
        content = open(py_file, encoding='utf-8').read()
        for pattern in bypass_patterns:
            matches = re.findall(pattern, content)
            if matches:
                violations.append((py_file, pattern, len(matches)))
        checked_files += 1
    except:
        pass

print(f'检查文件数: {checked_files}')
if violations:
    print(f'FAIL: 发现 {len(violations)} 处绕过:')
    for f, p, n in violations:
        print(f'  {f}: {p} ({n}次)')
else:
    print('PASS: 无适配层绕过')
    print('PASS: 无旧字段偷读')
