import re

with open('low_success_regeneration.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    # Check if a line has a comment followed by code (missing newline)
    # Pattern: spaces + # comment + spaces + if/for/while/return/etc
    match = re.match(r'^(\s+#[^\n]+?)(\s{4,}(?:if|for|while|return|real_lessons|continue)\s)', line)
    if match:
        comment_part = match.group(1) + '\n'
        code_part = match.group(2).lstrip() 
        # Preserve original indentation for code part
        indent = re.match(r'^(\s+)', match.group(2))
        if indent:
            code_part = indent.group(1) + line[match.start(2):].lstrip()
        else:
            code_part = line[match.start(2):]
        fixed_lines.append(comment_part)
        fixed_lines.append(code_part)
        print(f"Fixed: {repr(line[:80])}")
    else:
        fixed_lines.append(line)

with open('low_success_regeneration.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('Done, checking syntax...')
import py_compile
try:
    py_compile.compile('low_success_regeneration.py', doraise=True)
    print('Syntax OK')
except py_compile.PyCompileError as e:
    print(f'Still has error: {e}')
