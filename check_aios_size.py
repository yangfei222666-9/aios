import os
from pathlib import Path

# 检查 AIOS 相关文件大小
aios_dir = Path(r'C:\Users\A\.openclaw\workspace\aios')

total_size = 0
file_counts = {}
large_files = []

for root, dirs, files in os.walk(aios_dir):
    for file in files:
        fp = os.path.join(root, file)
        try:
            size = os.path.getsize(fp)
            total_size += size
            
            ext = os.path.splitext(file)[1]
            file_counts[ext] = file_counts.get(ext, 0) + 1
            
            if size > 1024 * 1024:  # >1MB
                large_files.append((fp, size))
        except:
            pass

print('=== AIOS 目录统计 ===')
print(f'总大小: {total_size / 1024 / 1024:.2f} MB')
print()

print('=== 文件类型分布 ===')
for ext, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    ext_name = ext if ext else '(无扩展名)'
    print(f'  {ext_name}: {count} 个')

print()

print('=== 大文件（>1MB）===')
large_files.sort(key=lambda x: x[1], reverse=True)
for fp, size in large_files[:10]:
    rel = os.path.relpath(fp, aios_dir)
    print(f'  {size / 1024 / 1024:.2f} MB - {rel}')

# 检查可清理的文件
print()
print('=== 可清理的文件 ===')

# .pyc 文件
pyc_files = []
for root, dirs, files in os.walk(aios_dir):
    for file in files:
        if file.endswith('.pyc'):
            pyc_files.append(os.path.join(root, file))

if pyc_files:
    print(f'  __pycache__: {len(pyc_files)} 个 .pyc 文件')
else:
    print('  __pycache__: 无')

# .bak 文件
bak_files = []
for root, dirs, files in os.walk(aios_dir):
    for file in files:
        if file.endswith('.bak'):
            bak_files.append(os.path.join(root, file))

if bak_files:
    print(f'  备份文件: {len(bak_files)} 个 .bak 文件')
else:
    print('  备份文件: 无')

# 临时文件
temp_files = []
for root, dirs, files in os.walk(aios_dir):
    for file in files:
        if file.startswith('~') or file.endswith('.tmp'):
            temp_files.append(os.path.join(root, file))

if temp_files:
    print(f'  临时文件: {len(temp_files)} 个')
else:
    print('  临时文件: 无')
