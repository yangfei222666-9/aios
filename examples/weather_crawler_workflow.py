"""
真实案例：多 Agent 协作开发一个 Web 爬虫

工作流：
1. researcher Agent: 研究目标网站结构
2. coder Agent: 编写爬虫代码
3. tester Agent: 测试爬虫功能
4. automation Agent: 设置定时任务
"""

# 任务定义
TASK = """
开发一个爬取天气数据的爬虫系统

要求：
- 爬取 wttr.in 的天气数据
- 保存为 JSON 格式
- 每天自动运行
- 有完整的测试
"""

# Step 1: Researcher 分析网站
researcher_task = """
你是信息研究专员。任务：分析 wttr.in 网站结构。

要求：
1. 访问 https://wttr.in/Beijing?format=j1
2. 分析 JSON 数据结构
3. 列出关键字段（温度、湿度、天气状况等）
4. 提供数据提取建议

输出：research_weather_api.md
"""

# Step 2: Coder 编写爬虫
coder_task = """
你是代码开发专员。任务：根据研究报告编写天气爬虫。

输入：research_weather_api.md

要求：
1. 使用 requests 库获取数据
2. 解析 JSON 并提取关键信息
3. 保存到 weather_data.json
4. 添加错误处理和日志
5. 代码要有注释

输出：weather_crawler.py
"""

# Step 3: Tester 编写测试
tester_task = """
你是测试工程师。任务：为天气爬虫编写测试。

输入：weather_crawler.py

要求：
1. 测试数据获取功能
2. 测试 JSON 解析
3. 测试错误处理
4. 测试文件保存
5. 使用 pytest 框架

输出：test_weather_crawler.py
"""

# Step 4: Automation 设置定时任务
automation_task = """
你是自动化专员。任务：设置天气爬虫定时任务。

输入：weather_crawler.py, test_weather_crawler.py

要求：
1. 创建 PowerShell 启动脚本
2. 设置 Windows 计划任务（每天 08:00）
3. 添加日志记录
4. 测试执行

输出：setup_weather_task.ps1
"""

# 执行流程
print("=== 多 Agent 协作：天气爬虫开发 ===\n")

print("Step 1: Researcher Agent 分析网站...")
print("→ 输出: research_weather_api.md\n")

print("Step 2: Coder Agent 编写爬虫...")
print("→ 输入: research_weather_api.md")
print("→ 输出: weather_crawler.py\n")

print("Step 3: Tester Agent 编写测试...")
print("→ 输入: weather_crawler.py")
print("→ 输出: test_weather_crawler.py\n")

print("Step 4: Automation Agent 设置定时任务...")
print("→ 输入: weather_crawler.py, test_weather_crawler.py")
print("→ 输出: setup_weather_task.ps1\n")

print("✅ 完整的天气爬虫系统开发完成！")
print("\n交付物：")
print("- research_weather_api.md (研究报告)")
print("- weather_crawler.py (爬虫代码)")
print("- test_weather_crawler.py (测试代码)")
print("- setup_weather_task.ps1 (部署脚本)")
print("- Windows 计划任务（每天 08:00 自动运行）")
