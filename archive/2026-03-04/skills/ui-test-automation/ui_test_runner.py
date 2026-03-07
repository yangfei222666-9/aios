#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Test Runner - 测试执行器
"""
import yaml
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class UITestRunner:
    def __init__(self, skill_dir: Path = None):
        self.skill_dir = skill_dir or Path(__file__).parent
        self.ui_automation_dir = self.skill_dir.parent / "ui-automation"
        self.results = []
    
    def load_test(self, test_file: Path) -> Dict[str, Any]:
        """加载测试用例"""
        if test_file.suffix == ".yaml" or test_file.suffix == ".yml":
            with open(test_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        elif test_file.suffix == ".json":
            with open(test_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(f"不支持的文件格式: {test_file.suffix}")
    
    def execute_action(self, action: Dict[str, Any]) -> bool:
        """执行单个动作"""
        action_type = action.get("action")
        
        try:
            if action_type == "launch":
                # 启动应用
                app = action.get("app")
                args = action.get("args", "")
                subprocess.Popen(f"{app} {args}", shell=True)
                time.sleep(action.get("wait", 2))
                return True
            
            elif action_type == "click":
                # 点击
                x = action.get("x")
                y = action.get("y")
                window = action.get("window")
                
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File",
                       str(self.ui_automation_dir / "ui-click.ps1"),
                       "-X", str(x), "-Y", str(y)]
                
                if window:
                    cmd.extend(["-Window", window])
                
                result = subprocess.run(cmd, capture_output=True)
                time.sleep(action.get("wait", 0.5))
                return result.returncode == 0
            
            elif action_type == "type":
                # 输入文本
                text = action.get("text")
                press_enter = action.get("press_enter", False)
                
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File",
                       str(self.ui_automation_dir / "ui-type.ps1"),
                       "-Text", text]
                
                if press_enter:
                    cmd.append("-PressEnter")
                
                result = subprocess.run(cmd, capture_output=True)
                time.sleep(action.get("wait", 0.5))
                return result.returncode == 0
            
            elif action_type == "hotkey":
                # 组合键
                keys = action.get("keys")
                # TODO: 实现组合键
                time.sleep(action.get("wait", 0.5))
                return True
            
            elif action_type == "wait":
                # 等待
                time.sleep(action.get("seconds", 1))
                return True
            
            elif action_type == "screenshot":
                # 截图
                output = action.get("output", "screenshot.png")
                # TODO: 实现截图
                time.sleep(action.get("wait", 0.5))
                return True
            
            else:
                print(f"未知动作类型: {action_type}")
                return False
        
        except Exception as e:
            print(f"执行动作失败: {action_type}, 错误: {e}")
            return False
    
    def execute_assertion(self, assertion: Dict[str, Any]) -> bool:
        """执行断言"""
        assertion_type = assertion.get("type")
        
        try:
            if assertion_type == "file_exists":
                path = Path(assertion.get("path"))
                return path.exists()
            
            elif assertion_type == "file_contains":
                path = Path(assertion.get("path"))
                text = assertion.get("text")
                if path.exists():
                    content = path.read_text(encoding="utf-8")
                    return text in content
                return False
            
            elif assertion_type == "file_size":
                path = Path(assertion.get("path"))
                min_size = assertion.get("min", 0)
                if path.exists():
                    return path.stat().st_size >= min_size
                return False
            
            elif assertion_type == "window_exists":
                title = assertion.get("title")
                # TODO: 检查窗口是否存在
                return True
            
            else:
                print(f"未知断言类型: {assertion_type}")
                return False
        
        except Exception as e:
            print(f"执行断言失败: {assertion_type}, 错误: {e}")
            return False
    
    def run_test(self, test_file: Path, retry: int = 0) -> Dict[str, Any]:
        """运行单个测试"""
        print(f"\n{'='*60}")
        print(f"运行测试: {test_file.name}")
        print(f"{'='*60}")
        
        test = self.load_test(test_file)
        test_name = test.get("name", test_file.stem)
        
        start_time = time.time()
        passed = True
        failed_step = None
        
        # 执行 setup
        for step in test.get("setup", []):
            if not self.execute_action(step):
                print(f"⚠️  Setup 失败: {step}")
        
        # 执行测试步骤
        for i, step in enumerate(test.get("steps", []), 1):
            print(f"步骤 {i}: {step.get('action')}")
            if not self.execute_action(step):
                passed = False
                failed_step = i
                print(f"❌ 步骤 {i} 失败")
                break
            print(f"✅ 步骤 {i} 完成")
        
        # 执行断言
        if passed:
            for i, assertion in enumerate(test.get("assertions", []), 1):
                print(f"断言 {i}: {assertion.get('type')}")
                if not self.execute_assertion(assertion):
                    passed = False
                    print(f"❌ 断言 {i} 失败")
                    break
                print(f"✅ 断言 {i} 通过")
        
        # 执行 teardown
        for step in test.get("teardown", []):
            self.execute_action(step)
        
        duration = time.time() - start_time
        
        result = {
            "name": test_name,
            "file": str(test_file),
            "passed": passed,
            "failed_step": failed_step,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        if passed:
            print(f"\n✅ 测试通过: {test_name} ({duration:.2f}s)")
        else:
            print(f"\n❌ 测试失败: {test_name} ({duration:.2f}s)")
            if retry > 0:
                print(f"🔄 重试 ({retry} 次剩余)...")
                return self.run_test(test_file, retry - 1)
        
        return result
    
    def run_suite(self, suite_dir: Path, parallel: int = 1) -> List[Dict[str, Any]]:
        """运行测试套件"""
        test_files = list(suite_dir.glob("*.yaml")) + list(suite_dir.glob("*.yml")) + list(suite_dir.glob("*.json"))
        
        print(f"\n{'='*60}")
        print(f"运行测试套件: {suite_dir.name}")
        print(f"测试用例数: {len(test_files)}")
        print(f"{'='*60}")
        
        for test_file in test_files:
            self.run_test(test_file)
        
        return self.results
    
    def generate_report(self, output: Path = None):
        """生成测试报告"""
        if not output:
            output = Path("test_report.html")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>UI 测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
    </style>
</head>
<body>
    <h1>UI 测试报告</h1>
    <div class="summary">
        <p><strong>执行时间:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>总用例:</strong> {total}</p>
        <p><strong>通过:</strong> <span class="passed">{passed}</span></p>
        <p><strong>失败:</strong> <span class="failed">{failed}</span></p>
        <p><strong>成功率:</strong> {success_rate:.1f}%</p>
    </div>
    
    <h2>测试结果</h2>
    <table>
        <tr>
            <th>用例名称</th>
            <th>状态</th>
            <th>耗时</th>
            <th>时间戳</th>
        </tr>
"""
        
        for result in self.results:
            status = "✅ 通过" if result["passed"] else "❌ 失败"
            status_class = "passed" if result["passed"] else "failed"
            html += f"""
        <tr>
            <td>{result['name']}</td>
            <td class="{status_class}">{status}</td>
            <td>{result['duration']:.2f}s</td>
            <td>{result['timestamp']}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        
        output.write_text(html, encoding="utf-8")
        print(f"\n📊 报告已生成: {output}")

if __name__ == "__main__":
    import sys
    
    runner = UITestRunner()
    
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        if test_file.is_file():
            runner.run_test(test_file)
        elif test_file.is_dir():
            runner.run_suite(test_file)
        else:
            print(f"文件或目录不存在: {test_file}")
    else:
        print("用法: python ui_test_runner.py <test_file_or_dir>")
    
    if runner.results:
        runner.generate_report()
