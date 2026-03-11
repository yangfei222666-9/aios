import os, re

bypass_patterns = [
    r"agent\[.status.\]",
    r"agent\.get\(.status.",
    r"skill\[.status.\]",
    r"task\[.status.\]",
]

violations = []
scan_dirs = ['core', 'reports', '.']
for d in scan_dirs:
    full_dir = os.path.join('.', d)
    if not os.path.isdir(full_dir):
        continue
    for f in os.listdir(full_dir):
        if not f.endswith('.py'):
            continue
        if f in ('status_adapter.py', 'check_bypass.py'):
            continue
        fpath = os.path.join(full_dir, f)
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
                for i, line in enumerate(lines):
                    for pat in bypass_patterns:
                        if re.search(pat, line):
                            violations.append(f'{fpath}:{i+1}: {line.strip()}')
        except:
            pass

if violations:
    print(f'WARNING: {len(violations)} bypass(es) found:')
    for v in violations[:20]:
        print(f'  {v}')
else:
    print('OK: No bypass detected')
