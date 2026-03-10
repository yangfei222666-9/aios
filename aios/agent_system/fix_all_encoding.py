#!/usr/bin/env python3
"""
Fix encoding issues in Python files by removing corrupted Chinese comments
"""
import re
from pathlib import Path

def fix_file(filepath: Path) -> bool:
    """
    Fix encoding issues in a Python file
    Returns True if file was modified
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        fixed_lines = []
        modified = False
        
        for line in lines:
            # Remove corrupted Chinese characters in comments
            if '#' in line:
                # Split at first #
                code_part, comment_part = line.split('#', 1)
                # Remove non-ASCII characters from comment
                clean_comment = ''.join(c if ord(c) < 128 else '' for c in comment_part)
                # If comment is now empty or just whitespace, remove it
                if clean_comment.strip():
                    fixed_line = code_part + '#' + clean_comment
                else:
                    fixed_line = code_part.rstrip() + '\n'
                
                if fixed_line != line:
                    modified = True
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        if modified:
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.writelines(fixed_lines)
            print(f"[OK] Fixed: {filepath.name}")
            return True
        else:
            print(f"[SKIP] {filepath.name} (no changes needed)")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error fixing {filepath.name}: {e}")
        return False


def main():
    files_to_fix = [
        'agent_lifecycle_engine.py',
        'daily_metrics.py',
        'experience_engine.py',
        'learnings_extractor.py',
    ]
    
    base_dir = Path(__file__).parent
    
    print("=" * 60)
    print("Fixing encoding issues in Python files")
    print("=" * 60)
    
    fixed_count = 0
    for filename in files_to_fix:
        filepath = base_dir / filename
        if filepath.exists():
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"[NOT FOUND] {filename}")
    
    print("=" * 60)
    print(f"Fixed {fixed_count}/{len(files_to_fix)} files")
    print("=" * 60)


if __name__ == '__main__':
    main()
