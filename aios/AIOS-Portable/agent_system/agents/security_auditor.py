"""Security Auditor Agent - 安全审计"""
import json, re
from pathlib import Path
from datetime import datetime

class SecurityAuditor:
    def __init__(self):
        self.audit_log = Path("data/security/audit_log.jsonl")
        self.dangerous_patterns = [
            (r'eval\(', "危险函数 eval()"),
            (r'exec\(', "危险函数 exec()"),
            (r'os\.system\(', "系统命令执行"),
            (r'subprocess\.call\(', "子进程调用"),
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码 API Key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码 Secret"),
            (r'rm\s+-rf', "危险删除命令"),
            (r'DROP\s+TABLE', "危险 SQL 操作"),
        ]
    
    def audit(self, target_dir="."):
        print("=" * 80)
        print("Security Auditor - 安全审计")
        print("=" * 80)
        
        target = Path(target_dir)
        issues = []
        scanned = 0
        
        print(f"\n🔍 扫描目录: {target.absolute()}\n")
        
        for f in target.rglob("*.py"):
            if ".git" in str(f) or "__pycache__" in str(f):
                continue
            
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                scanned += 1
                
                for pattern, desc in self.dangerous_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        issues.append({
                            "file": str(f),
                            "issue": desc,
                            "severity": "high" if "密码" in desc or "Key" in desc else "medium",
                            "count": len(matches)
                        })
            except Exception:
                pass
        
        print(f"📊 扫描结果: {scanned} 个文件, {len(issues)} 个问题\n")
        
        if issues:
            for issue in issues[:10]:
                print(f"  ⚠️  [{issue['severity'].upper()}] {issue['file']}")
                print(f"      {issue['issue']} ({issue['count']} 处)")
        else:
            print("✓ 未发现安全问题")
        
        # 保存
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": datetime.now().isoformat(), "scanned": scanned, "issues": issues}, ensure_ascii=False) + "\n")
        
        print(f"\n{'=' * 80}")

if __name__ == "__main__":
    auditor = SecurityAuditor()
    auditor.audit("agents")
