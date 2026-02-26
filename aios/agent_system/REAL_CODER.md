# Real Coder Agent - 使用说明

## 前置条件

需要设置 Anthropic API Key：

```powershell
# PowerShell
$env:ANTHROPIC_API_KEY = "your-api-key-here"

# 或者永久设置（系统环境变量）
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-api-key", "User")
```

## 使用方式

### 方式1：直接调用
```bash
python real_coder.py "写一个函数计算斐波那契数列"
```

### 方式2：集成到心跳
修改 `heartbeat_demo.py`，将模拟执行改为真实执行。

## 工作流程

```
任务描述 → Claude API 生成代码 → 保存到文件 → 沙盒执行 → 返回结果
```

## 输出目录

生成的代码保存在：
```
agent_system/workspace/generated_code/
```

## 安全机制

- ✅ 限制工作目录（只能访问 workspace/）
- ✅ 执行超时（默认 30 秒）
- ✅ 捕获所有输出和错误

## 下一步

1. 设置 API Key
2. 测试单个任务
3. 集成到心跳系统
