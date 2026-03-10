import re

with open('low_success_regeneration.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.rstrip()
    
    # Fix: docstring closing """ merged with content on same line
    # Pattern: content + spaces + """
    if '"""' in stripped:
        # Check if """ appears after non-whitespace content (not at start)
        idx = stripped.find('"""')
        before = stripped[:idx].strip()
        if before and not before.startswith('#') and not before.startswith('def ') and not before.startswith('class '):
            # Split: content line + """ line
            indent = len(line) - len(line.lstrip())
            content_part = ' ' * indent + before + '\n'
            docstring_part = ' ' * indent + '"""' + stripped[idx+3:] + '\n'
            fixed_lines.append(content_part)
            fixed_lines.append(docstring_part)
            print(f"Line {i+1}: Split docstring from content")
            i += 1
            continue
    
    # Fix: comment merged with code (comment + spaces + code)
    # Pattern: spaces + # comment + spaces + identifier/keyword
    match = re.match(r'^(\s+)(#[^\n]+?)(\s{4,})([a-zA-Z_])', stripped + '    x')
    if match and not stripped.startswith('    #') == False:
        # More careful check: line has # then later has code
        comment_match = re.match(r'^(\s+#[^\'"\n]+?)(\s{4,})((?:if |for |while |return |[a-zA-Z_]\w*\s*[=({]))', line)
        if comment_match:
            indent_spaces = re.match(r'^(\s+)', line).group(1)
            comment_end = comment_match.end(1)
            code_start = comment_match.start(3)
            comment_line = line[:comment_end].rstrip() + '\n'
            code_line = indent_spaces + line[code_start:].lstrip()
            fixed_lines.append(comment_line)
            fixed_lines.append(code_line)
            print(f"Line {i+1}: Split comment from code")
            i += 1
            continue
    
    # Fix unterminated strings (odd number of single quotes)
    sq = stripped.count("'")
    if sq % 2 == 1:
        if stripped.endswith(','):
            fixed = stripped[:-1] + "',"
        elif stripped.endswith(':'):
            fixed = stripped[:-1] + "':"
        else:
            fixed = stripped + "'"
        if line.endswith('\n'):
            fixed += '\n'
        fixed_lines.append(fixed)
        print(f"Line {i+1}: Fixed unterminated string")
        i += 1
        continue
    
    fixed_lines.append(line)
    i += 1

with open('low_success_regeneration.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('Done, checking syntax...')
import py_compile
try:
    py_compile.compile('low_success_regeneration.py', doraise=True)
    print('Syntax OK')
except py_compile.PyCompileError as e:
    print(f'Still has error: {e}')
