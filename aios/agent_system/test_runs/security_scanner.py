#!/usr/bin/env python3
"""
安全审计扫描器
扫描 Python 文件中的安全问题
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

class SecurityScanner:
    def __init__(self):
        self.issues = []
        
    def scan_file(self, filepath: str) -> List[Dict]:
        """扫描单个文件"""
        file_issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            # 检查1: 硬编码的密钥/token/password
            file_issues.extend(self._check_hardcoded_secrets(filepath, lines))
            
            # 检查2: 不安全的 eval/exec 调用
            file_issues.extend(self._check_dangerous_eval(filepath, lines))
            
            # 检查3: 危险的 os.system/subprocess 调用
            file_issues.extend(self._check_dangerous_subprocess(filepath, lines))
            
        except Exception as e:
            file_issues.append({
                'file': filepath,
                'line': 0,
                'type': 'ERROR',
                'severity': 'INFO',
                'message': f'无法读取文件: {str(e)}'
            })
            
        return file_issues
    
    def _check_hardcoded_secrets(self, filepath: str, lines: List[str]) -> List[Dict]:
        """检查硬编码的密钥"""
        issues = []
        
        # 敏感关键词模式
        patterns = [
            (r'password\s*=\s*["\'](?!.*\{.*\})([^"\']{3,})["\']', 'PASSWORD', 'HIGH'),
            (r'token\s*=\s*["\'](?!.*\{.*\})([^"\']{10,})["\']', 'TOKEN', 'HIGH'),
            (r'api[_-]?key\s*=\s*["\'](?!.*\{.*\})([^"\']{10,})["\']', 'API_KEY', 'HIGH'),
            (r'secret\s*=\s*["\'](?!.*\{.*\})([^"\']{10,})["\']', 'SECRET', 'HIGH'),
            (r'aws[_-]?access[_-]?key\s*=\s*["\']([^"\']+)["\']', 'AWS_KEY', 'CRITICAL'),
            (r'private[_-]?key\s*=\s*["\']([^"\']+)["\']', 'PRIVATE_KEY', 'CRITICAL'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('#'):
                continue
                
            for pattern, secret_type, severity in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    # 排除明显的占位符
                    value = match.group(1) if match.lastindex >= 1 else ''
                    if value and not any(placeholder in value.lower() for placeholder in 
                                       ['xxx', 'your', 'example', 'test', 'dummy', 'placeholder', 'changeme']):
                        issues.append({
                            'file': filepath,
                            'line': line_num,
                            'type': f'HARDCODED_{secret_type}',
                            'severity': severity,
                            'message': f'发现硬编码的 {secret_type}: {line.strip()[:80]}'
                        })
        
        return issues
    
    def _check_dangerous_eval(self, filepath: str, lines: List[str]) -> List[Dict]:
        """检查不安全的 eval/exec 调用"""
        issues = []
        
        patterns = [
            (r'\beval\s*\(', 'eval()', 'HIGH'),
            (r'\bexec\s*\(', 'exec()', 'HIGH'),
            (r'\b__import__\s*\(', '__import__()', 'MEDIUM'),
            (r'\bcompile\s*\(', 'compile()', 'MEDIUM'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('#'):
                continue
                
            for pattern, func_name, severity in patterns:
                if re.search(pattern, line):
                    # 检查是否有输入验证的迹象
                    has_validation = any(keyword in line.lower() for keyword in 
                                       ['sanitize', 'validate', 'check', 'safe', 'whitelist'])
                    
                    if not has_validation:
                        issues.append({
                            'file': filepath,
                            'line': line_num,
                            'type': f'DANGEROUS_{func_name.upper().replace("()", "")}',
                            'severity': severity,
                            'message': f'发现不安全的 {func_name} 调用: {line.strip()[:80]}'
                        })
        
        return issues
    
    def _check_dangerous_subprocess(self, filepath: str, lines: List[str]) -> List[Dict]:
        """检查危险的 subprocess/os.system 调用"""
        issues = []
        
        patterns = [
            (r'\bos\.system\s*\(', 'os.system()', 'HIGH'),
            (r'\bsubprocess\.call\s*\(', 'subprocess.call()', 'MEDIUM'),
            (r'\bsubprocess\.Popen\s*\(', 'subprocess.Popen()', 'MEDIUM'),
            (r'\bsubprocess\.run\s*\(', 'subprocess.run()', 'MEDIUM'),
            (r'\bos\.popen\s*\(', 'os.popen()', 'HIGH'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('#'):
                continue
                
            for pattern, func_name, severity in patterns:
                if re.search(pattern, line):
                    # 检查是否使用了 shell=True（更危险）
                    has_shell_true = 'shell=True' in line or 'shell = True' in line
                    
                    # 检查是否有输入验证
                    has_validation = any(keyword in line.lower() for keyword in 
                                       ['sanitize', 'validate', 'check', 'escape', 'quote', 'shlex'])
                    
                    # 检查是否使用了字符串格式化（可能导致注入）
                    has_formatting = any(op in line for op in ['%', '.format(', 'f"', "f'"])
                    
                    if has_shell_true and not has_validation:
                        issues.append({
                            'file': filepath,
                            'line': line_num,
                            'type': 'SHELL_INJECTION_RISK',
                            'severity': 'CRITICAL',
                            'message': f'发现 shell=True 且无输入验证: {line.strip()[:80]}'
                        })
                    elif has_formatting and not has_validation:
                        issues.append({
                            'file': filepath,
                            'line': line_num,
                            'type': 'COMMAND_INJECTION_RISK',
                            'severity': 'HIGH',
                            'message': f'发现命令拼接且无输入验证: {line.strip()[:80]}'
                        })
                    elif not has_validation:
                        issues.append({
                            'file': filepath,
                            'line': line_num,
                            'type': f'UNSAFE_{func_name.upper().replace("()", "").replace(".", "_")}',
                            'severity': severity,
                            'message': f'发现 {func_name} 调用缺少输入验证: {line.strip()[:80]}'
                        })
        
        return issues
    
    def scan_directory(self, directory: str) -> List[Dict]:
        """扫描整个目录"""
        all_issues = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    file_issues = self.scan_file(filepath)
                    all_issues.extend(file_issues)
        
        return all_issues
    
    def generate_report(self, issues: List[Dict], output_file: str):
        """生成审计报告"""
        # 按严重程度分组
        critical = [i for i in issues if i['severity'] == 'CRITICAL']
        high = [i for i in issues if i['severity'] == 'HIGH']
        medium = [i for i in issues if i['severity'] == 'MEDIUM']
        info = [i for i in issues if i['severity'] == 'INFO']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# AIOS Agent System 安全审计报告\n\n')
            f.write(f'**审计时间:** {Path(__file__).stat().st_mtime}\n\n')
            f.write(f'**扫描目录:** C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\n\n')
            
            f.write('## 执行摘要\n\n')
            f.write(f'- **严重 (CRITICAL):** {len(critical)} 个问题\n')
            f.write(f'- **高危 (HIGH):** {len(high)} 个问题\n')
            f.write(f'- **中危 (MEDIUM):** {len(medium)} 个问题\n')
            f.write(f'- **信息 (INFO):** {len(info)} 个问题\n')
            f.write(f'- **总计:** {len(issues)} 个问题\n\n')
            
            if len(critical) > 0:
                f.write('## 🔴 严重问题 (CRITICAL)\n\n')
                for issue in critical:
                    rel_path = issue['file'].replace('C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\', '')
                    f.write(f'### {issue["type"]}\n')
                    f.write(f'- **文件:** `{rel_path}`\n')
                    f.write(f'- **行号:** {issue["line"]}\n')
                    f.write(f'- **描述:** {issue["message"]}\n\n')
            
            if len(high) > 0:
                f.write('## 🟠 高危问题 (HIGH)\n\n')
                for issue in high:
                    rel_path = issue['file'].replace('C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\', '')
                    f.write(f'### {issue["type"]}\n')
                    f.write(f'- **文件:** `{rel_path}`\n')
                    f.write(f'- **行号:** {issue["line"]}\n')
                    f.write(f'- **描述:** {issue["message"]}\n\n')
            
            if len(medium) > 0:
                f.write('## 🟡 中危问题 (MEDIUM)\n\n')
                for issue in medium:
                    rel_path = issue['file'].replace('C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\', '')
                    f.write(f'### {issue["type"]}\n')
                    f.write(f'- **文件:** `{rel_path}`\n')
                    f.write(f'- **行号:** {issue["line"]}\n')
                    f.write(f'- **描述:** {issue["message"]}\n\n')
            
            f.write('## 建议\n\n')
            f.write('1. **立即修复所有 CRITICAL 级别的问题**\n')
            f.write('2. **对于硬编码的密钥:**\n')
            f.write('   - 使用环境变量或配置文件\n')
            f.write('   - 使用密钥管理服务（如 AWS Secrets Manager）\n')
            f.write('3. **对于 eval/exec 调用:**\n')
            f.write('   - 避免使用，寻找替代方案\n')
            f.write('   - 如果必须使用，严格验证和清理输入\n')
            f.write('   - 使用 ast.literal_eval() 代替 eval()\n')
            f.write('4. **对于 subprocess 调用:**\n')
            f.write('   - 避免使用 shell=True\n')
            f.write('   - 使用参数列表而不是字符串拼接\n')
            f.write('   - 使用 shlex.quote() 清理输入\n')
            f.write('   - 实施白名单验证\n\n')
            
            f.write('## 审计完成\n\n')
            f.write('此报告由 AIOS 安全审计员自动生成。\n')

if __name__ == '__main__':
    scanner = SecurityScanner()
    target_dir = r'C:\Users\A\.openclaw\workspace\aios\agent_system'
    output_file = r'C:\Users\A\.openclaw\workspace\aios\agent_system\test_runs\security_audit.md'
    
    print(f'开始扫描 {target_dir}...')
    issues = scanner.scan_directory(target_dir)
    
    print(f'发现 {len(issues)} 个问题')
    print(f'生成报告到 {output_file}...')
    
    scanner.generate_report(issues, output_file)
    print('审计完成！')
