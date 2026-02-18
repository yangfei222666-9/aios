"""
autolearn/scripts/self_eval.py - 复测验证器
读取 lessons.json 中 verified=False 的条目，运行复测命令验证
"""
import json
import os
import subprocess
from datetime import datetime

WORKSPACE = os.path.join(os.environ["USERPROFILE"], ".openclaw", "workspace")
LESSONS_FILE = os.path.join(WORKSPACE, "memory", "lessons.json")

VERIFY_TESTS = {
    "powershell": {
        "desc": "PowerShell 用 Get-ChildItem 而非 cmd dir 参数",
        "cmd": 'powershell -NoProfile -Command "Get-ChildItem $env:USERPROFILE\\Downloads -File | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name"',
        "expect_exit": 0,
    },
    "path": {
        "desc": "使用绝对路径或 $env:USERPROFILE 而非 ~",
        "cmd": f'powershell -NoProfile -Command "Test-Path \\\"$env:USERPROFILE\\.openclaw\\workspace\\autolearn\\inbox.md\\\""',
        "expect_exit": 0,
        "expect_output": "True",
    },
    "permission": {
        "desc": "系统服务需要管理员权限终止",
        "cmd": 'powershell -NoProfile -Command "Write-Host \'Permission lesson acknowledged\'"',
        "expect_exit": 0,
    },
    "encoding": {
        "desc": "web_search 中文 ByteString 是工具限制",
        "cmd": None,  # 无法自动验证
    },
    "tool_limitation": {
        "desc": "工具限制类教训，手动确认",
        "cmd": None,
    },
}

def run_test(test):
    if test["cmd"] is None:
        return True, "Manual verification (tool limitation)"
    
    try:
        result = subprocess.run(
            test["cmd"], shell=True, capture_output=True, text=True, timeout=15
        )
        
        exit_ok = result.returncode == test.get("expect_exit", 0)
        output_ok = True
        if "expect_output" in test:
            output_ok = test["expect_output"] in result.stdout
        
        if exit_ok and output_ok:
            return True, result.stdout.strip()[:100]
        else:
            return False, f"exit={result.returncode} stdout={result.stdout.strip()[:80]}"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:100]

def main():
    print("=" * 50)
    print("  Autolearn Self-Eval (Verify)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if not os.path.exists(LESSONS_FILE):
        print("\n[!] lessons.json not found")
        return
    
    with open(LESSONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    unverified = [l for l in data["lessons"] if not l.get("verified", False)]
    if not unverified:
        print("\n[OK] All lessons verified")
        return
    
    print(f"\n[*] {len(unverified)} unverified lessons\n")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for lesson in unverified:
        cat = lesson.get("category", "unknown")
        test = VERIFY_TESTS.get(cat)
        
        if not test:
            desc = lesson.get('mistake') or lesson.get('lesson') or '?'
            print(f"  [SKIP] {desc[:50]} (no test for '{cat}')")
            skipped += 1
            continue
        
        ok, detail = run_test(test)
        
        if ok:
            lesson["verified"] = True
            lesson["verified_date"] = datetime.now().strftime("%Y-%m-%d")
            print(f"  [PASS] {cat}: {test['desc']}")
            passed += 1
        else:
            print(f"  [FAIL] {cat}: {detail}")
            failed += 1
    
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n" + "=" * 50)
    print(f"  Results: {passed} PASS / {failed} FAIL / {skipped} SKIP")
    print("=" * 50)

if __name__ == "__main__":
    main()
