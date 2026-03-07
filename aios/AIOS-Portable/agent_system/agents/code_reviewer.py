"""Code Reviewer Agent - 自动代码审查"""
import json, re
from pathlib import Path
from datetime import datetime

class CodeReviewer:
    def __init__(self):
        self.review_log = Path("data/reviews/code_reviews.jsonl")
        
    def review(self, code, language="python"):
        print("=" * 80)
        print("Code Reviewer - 代码审查")
        print("=" * 80)
        
        issues = []
        
        # 1. 语法检查
        issues.extend(self._check_syntax(code, language))
        
        # 2. 安全检查
        issues.extend(self._check_security(code))
        
        # 3. 性能检查
        issues.extend(self._check_performance(code))
        
        # 4. 最佳实践
        issues.extend(self._check_best_practices(code))
        
        # 5. 生成报告
        self._generate_report(issues, code)
        
        return issues
    
    def _check_syntax(self, code, language):
        issues = []
        if language == "python":
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                issues.append({"type": "syntax", "severity": "high", "message": str(e)})
        return issues
    
    def _check_security(self, code):
        issues = []
        dangerous = [r'eval\(', r'exec\(', r'__import__', r'os\.system', r'subprocess\.call']
        for pattern in dangerous:
            if re.search(pattern, code):
                issues.append({"type": "security", "severity": "high", "message": f"发现危险函数: {pattern}"})
        return issues
    
    def _check_performance(self, code):
        issues = []
        if code.count('for') > 3:
            issues.append({"type": "performance", "severity": "medium", "message": "嵌套循环过多"})
        return issues
    
    def _check_best_practices(self, code):
        issues = []
        if 'TODO' in code or 'FIXME' in code:
            issues.append({"type": "best_practice", "severity": "low", "message": "存在未完成的 TODO"})
        return issues
    
    def _generate_report(self, issues, code):
        print(f"\n📊 审查结果: {len(issues)} 个问题\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. [{issue['severity'].upper()}] {issue['type']}: {issue['message']}")
        
        if not issues:
            print("✓ 代码质量良好")
        
        # 保存
        self.review_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.review_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": datetime.now().isoformat(), "issues": issues}, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    reviewer = CodeReviewer()
    test_code = "print('hello')\neval('1+1')"
    reviewer.review(test_code)
