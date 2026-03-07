#!/usr/bin/env python3
"""
Real Coder Agent - 真实代码生成执行
直接调用 Claude API，生成并执行代码
集成 CostGuardian 成本控制
集成 Fast/Slow Router 智能模型选择
"""
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import anthropic
import os
import time
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cost_guardian import CostGuardian
from agents.router.agent_router import route_task, TaskIndicators

# Claude API 配置
def load_api_key():
    """加载 API Key（优先从配置文件，其次从环境变量）"""
    # 1. 尝试从配置文件读取
    config_file = Path(__file__).parent / "config.json"
    if config_file.exists():
        try:
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)
                api_key = config.get("anthropic_api_key")
                if api_key and api_key != "your-api-key-here":
                    return api_key
        except:
            pass
    
    # 2. 尝试从环境变量读取
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key
    
    print("[WARN] 警告：未设置 ANTHROPIC_API_KEY")
    print("请在 config.json 中设置或使用环境变量：$env:ANTHROPIC_API_KEY='your-api-key'")
    return None

ANTHROPIC_API_KEY = load_api_key()

# 输出目录
OUTPUT_DIR = Path(__file__).parent / "workspace" / "generated_code"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def call_claude_api(prompt: str, model: str = None, task_description: str = None) -> str:
    """调用 Claude API 生成代码（集成 Fast/Slow Router）"""
    if not ANTHROPIC_API_KEY:
        return "# Error: ANTHROPIC_API_KEY not set"
    
    # === Fast/Slow Router 集成 ===
    if model is None and task_description:
        # 分析任务指标
        indicators: TaskIndicators = {
            "needs_code": True,
            "high_risk": any(word in task_description.lower() for word in ["修复", "critical", "重构", "优化"]),
            "est_lines": len(task_description.split()) * 3,  # 粗略估算
            "dependencies": task_description.count("import") + task_description.count("库"),
            "requires_reasoning": any(word in task_description.lower() for word in ["算法", "优化", "设计", "架构"]),
            "task_description": task_description
        }
        
        # 路由决策
        model_choice = route_task(
            task_id=f"coder-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            task_description=task_description,
            indicators=indicators
        )
        
        # 映射到实际模型名称
        model = "claude-opus-4-6" if model_choice == "slow" else "claude-sonnet-4-6"
        print(f"🚦 Router 决策: {model_choice} → {model}")
    elif model is None:
        model = "claude-sonnet-4-6"  # 默认快模型
    
    # 读取 base_url（如果有）
    config_file = Path(__file__).parent / "config.json"
    base_url = None
    if config_file.exists():
        try:
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)
                base_url = config.get("anthropic_base_url")
        except:
            pass
    
    # 创建客户端
    if base_url:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, base_url=base_url)
    else:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    system_prompt = """你是一个专业的 Python 开发工程师。
    
要求：
1. 只输出可执行的 Python 代码，不要有任何解释
2. 代码要完整、可运行
3. 包含必要的错误处理
4. 添加简洁的注释
5. 如果需要第三方库，在代码开头注释说明

输出格式：纯 Python 代码，不要用 markdown 代码块包裹。"""
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        code = message.content[0].text
        
        # 清理可能的 markdown 代码块标记
        if code.startswith("```python"):
            code = code.replace("```python", "").replace("```", "").strip()
        elif code.startswith("```"):
            code = code.replace("```", "").strip()
        
        return code
    
    except Exception as e:
        return f"# Error calling Claude API: {e}"

def save_code(code: str, filename: str = None) -> Path:
    """保存代码到文件"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{timestamp}.py"
    
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    
    return filepath

def run_in_sandbox(filepath: Path, timeout: int = 30) -> dict:
    """在沙盒中执行代码（简化版：受限的 subprocess）"""
    try:
        # 使用 subprocess 执行，设置超时
        result = subprocess.run(
            ["python", str(filepath)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=OUTPUT_DIR  # 限制工作目录
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timeout: 执行超过 {timeout} 秒",
            "returncode": -1
        }
    
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def execute_code_task(description: str) -> dict:
    """执行代码任务（完整流程）"""
    print(f"[NOTE] 任务描述: {description}")
    
    # 1. 成本检查
    guardian = CostGuardian()
    estimated_cost = 0.01  # 估算成本（可以根据描述长度调整）
    
    check = guardian.should_allow_task(estimated_cost)
    if not check["allowed"]:
        print(f"[FAIL] 任务被拒绝: {check['message']}")
        return {
            "success": False,
            "error": check["message"],
            "code": None,
            "filepath": None,
            "execution": None
        }
    
    print(f"🤖 调用 Claude API 生成代码...")
    start_time = time.time()
    
    # 1. 生成代码（传入 task_description 触发 Router）
    code = call_claude_api(f"请写一个 Python 代码：{description}", task_description=description)
    
    if code.startswith("# Error"):
        return {
            "success": False,
            "error": code,
            "code": None,
            "filepath": None,
            "execution": None
        }
    
    print(f"[OK] 代码生成完成 ({len(code)} 字符)")
    
    # 2. 保存代码
    filepath = save_code(code)
    print(f"💾 代码已保存: {filepath}")
    
    # 3. 执行代码
    print(f"[ZAP] 执行代码...")
    execution_result = run_in_sandbox(filepath)
    
    if execution_result["success"]:
        print(f"[OK] 执行成功")
        if execution_result["stdout"]:
            print(f"📤 输出:\n{execution_result['stdout']}")
    else:
        print(f"[FAIL] 执行失败")
        if execution_result["stderr"]:
            print(f"📤 错误:\n{execution_result['stderr']}")
    
    return {
        "success": execution_result["success"],
        "code": code,
        "filepath": str(filepath),
        "execution": execution_result
    }

def main():
    """命令行接口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python real_coder.py '任务描述'")
        print("\n示例:")
        print("  python real_coder.py '写一个函数计算斐波那契数列'")
        print("  python real_coder.py '写一个爬虫抓取 Hacker News 首页标题'")
        sys.exit(1)
    
    description = " ".join(sys.argv[1:])
    result = execute_code_task(description)
    
    # 输出结果摘要
    print("\n" + "="*80)
    if result["success"]:
        print("[OK] 任务完成")
        print(f"📁 代码文件: {result['filepath']}")
    else:
        print("[FAIL] 任务失败")
        if result.get("error"):
            print(f"错误: {result['error']}")

if __name__ == "__main__":
    main()
