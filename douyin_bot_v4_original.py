# -*- coding: utf-8 -*-
"""
抖音评论自动化工具 V4 - 视觉Agent版
使用视觉模型理解界面 + Playwright执行操作
不需要GPU，使用云端API
"""

import os
import time
import random
import base64
import json

# 尝试导入loguru，如果失败则使用标准logging
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)

# 尝试导入Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("=" * 60)
    print("⚠️  Playwright未安装")
    print("=" * 60)
    print("请运行以下命令安装：")
    print("  pip install playwright")
    print("  python -m playwright install chromium")
    print("=" * 60)

# 导入配置
from config import (
    DEFAULT_COMMENT, WAIT_TIME, RANDOM_DELAY_MIN, RANDOM_DELAY_MAX,
    USE_PRESET_COMMENTS, PRESET_COMMENTS, API_ENDPOINTS, API_KEYS, MODEL_IDS
)


class VisionAgent:
    """
    视觉Agent - 使用视觉模型理解界面
    """
    
    def __init__(self, api_type="teacher"):
        """初始化视觉Agent"""
        self.api_type = api_type
        # 使用config.py中的配置
        self.api_url = API_ENDPOINTS.get(api_type, API_ENDPOINTS.get("teacher"))
        self.api_key = API_KEYS.get(api_type, API_KEYS.get("teacher"))
        self.model_id = MODEL_IDS.get(api_type, MODEL_IDS.get("teacher"))
        
        print(f"[视觉Agent] API URL: {self.api_url}")
        print(f"[视觉Agent] Model ID: {self.model_id}")
    
    def analyze_screenshot(self, screenshot_path, task_description):
        """
        分析截图，返回操作指令
        
        参数:
            screenshot_path: 截图路径
            task_description: 任务描述
        
        返回:
            dict: 操作指令
        """
        try:
            # 读取截图并转为base64
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # 构建请求
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""你是一个GUI自动化助手。请分析这张抖音视频页面的截图。

任务：{task_description}

请找出以下元素的位置（返回坐标百分比，0-1之间）：
1. 评论区按钮（如果评论区未打开）
2. 评论输入框
3. 发布按钮

请按以下JSON格式返回：
{{
    "comment_section_open": true/false,
    "comment_button": [x, y],
    "input_box": [x, y],
    "publish_button": [x, y],
    "action": "click_comment/click_input/type_comment/click_publish/done",
    "reasoning": "简要说明"
}}
"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            payload = {
                "model": self.model_id,  # 使用配置中的model_id
                "messages": messages,
                "max_tokens": 500
            }
            
            # 发送请求
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # 尝试解析JSON
                try:
                    # 提取JSON部分
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except:
                    pass
                
                return {"action": "done", "reasoning": content}
            
            return {"action": "error", "reasoning": f"API错误: {response.status_code}"}
            
        except Exception as e:
            logger.error(f"分析截图失败: {e}")
            return {"action": "error", "reasoning": str(e)}


class DouyinBotV4:
    """
    抖音评论机器人V4 - 视觉Agent版
    使用视觉模型理解界面 + Playwright执行操作
    """
    
    def __init__(self):
        """初始化"""
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.vision_agent = None
        self.stats = {
            "total": 0,
            "success": 0,
            "fail": 0
        }
        
        # 创建日志目录
        os.makedirs("logs", exist_ok=True)
        os.makedirs("screenshots", exist_ok=True)
        os.makedirs("browser_data", exist_ok=True)
        
        logger.info("=" * 60)
        logger.info("抖音评论自动化工具 V4 (视觉Agent版)")
        logger.info("=" * 60)
    
    def init_browser(self):
        """初始化浏览器"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright未安装")
            return False
        
        try:
            logger.info("正在启动Playwright浏览器...")
            print("[步骤0] 正在启动Playwright浏览器...")
            
            self.playwright = sync_playwright().start()
            
            # 用户数据目录
            user_data_dir = os.path.join(os.getcwd(), "browser_data")
            os.makedirs(user_data_dir, exist_ok=True)
            
            # 尝试使用系统Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ]
            
            browser_launched = False
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    print(f"[尝试] 使用系统Chrome: {chrome_path}")
                    try:
                        self.context = self.playwright.chromium.launch_persistent_context(
                            user_data_dir,
                            executable_path=chrome_path,
                            headless=False,
                            viewport={"width": 1280, "height": 720},
                            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
                        )
                        browser_launched = True
                        print("[OK] 使用系统Chrome启动成功")
                        break
                    except Exception as e:
                        print(f"[警告] 使用系统Chrome失败: {e}")
                        continue
            
            if not browser_launched:
                print("[尝试] 使用Playwright自带浏览器...")
                try:
                    self.context = self.playwright.chromium.launch_persistent_context(
                        user_data_dir,
                        headless=False,
                        viewport={"width": 1280, "height": 720},
                        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
                    )
                    browser_launched = True
                    print("[OK] 使用Playwright自带浏览器启动成功")
                except Exception as e:
                    print(f"[错误] 启动浏览器失败: {e}")
                    return False
            
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
            # 初始化视觉Agent
            self.vision_agent = VisionAgent()
            
            print("[OK] 浏览器和视觉Agent已初始化")
            return True
            
        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            print(f"[错误] 初始化浏览器失败: {e}")
            return False
    
    def take_screenshot(self, filename=None):
        """截图"""
        try:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshots/screen_{timestamp}.png"
            
            self.page.screenshot(path=filename)
            return filename
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def click_at_percent(self, x_percent, y_percent):
        """点击百分比位置"""
        viewport = self.page.viewport_size
        x = int(viewport["width"] * x_percent)
        y = int(viewport["height"] * y_percent)
        print(f"[点击] 位置: ({x}, {y})")
        self.page.mouse.click(x, y)
    
    def generate_comment(self):
        """生成评论内容"""
        if USE_PRESET_COMMENTS and PRESET_COMMENTS:
            return random.choice(PRESET_COMMENTS)
        return DEFAULT_COMMENT
    
    def process_single_url(self, url, index, total):
        """处理单个链接"""
        print(f"\n{'='*60}")
        print(f"[处理] 第 {index}/{total} 个链接")
        print(f"[链接] {url}")
        print(f"{'='*60}")
        
        self.stats["total"] += 1
        
        try:
            # 1. 打开链接
            print("[步骤1] 打开链接...")
            self.page.goto(url, wait_until="commit", timeout=60000)
            self.page.wait_for_timeout(5000)
            
            # 2. 截图分析
            print("[步骤2] 截图分析...")
            screenshot_path = self.take_screenshot()
            if not screenshot_path:
                print("[错误] 截图失败")
                self.stats["fail"] += 1
                return False
            
            # 3. 使用视觉Agent分析
            print("[步骤3] 视觉Agent分析界面...")
            comment = self.generate_comment()
            result = self.vision_agent.analyze_screenshot(
                screenshot_path,
                f"在抖音视频页面发表评论：{comment}"
            )
            
            print(f"[分析结果] {result}")
            
            # 4. 根据分析结果执行操作
            action = result.get("action", "done")
            
            if action == "click_comment":
                # 点击评论区按钮
                btn = result.get("comment_button", [0.9, 0.5])
                self.click_at_percent(btn[0], btn[1])
                self.page.wait_for_timeout(2000)
                
                # 重新截图分析
                screenshot_path = self.take_screenshot()
                result = self.vision_agent.analyze_screenshot(
                    screenshot_path,
                    f"在评论输入框输入评论：{comment}"
                )
                action = result.get("action", "done")
            
            if action in ["click_input", "type_comment"]:
                # 点击输入框
                input_box = result.get("input_box", [0.5, 0.9])
                self.click_at_percent(input_box[0], input_box[1])
                self.page.wait_for_timeout(500)
                
                # 输入评论
                self.page.keyboard.type(comment, delay=50)
                self.page.wait_for_timeout(500)
                
                # 重新截图分析
                screenshot_path = self.take_screenshot()
                result = self.vision_agent.analyze_screenshot(
                    screenshot_path,
                    "点击发布按钮发送评论"
                )
                action = result.get("action", "done")
            
            if action == "click_publish":
                # 点击发布按钮
                publish_btn = result.get("publish_button", [0.95, 0.9])
                self.click_at_percent(publish_btn[0], publish_btn[1])
                self.page.wait_for_timeout(1000)
            
            self.stats["success"] += 1
            print(f"[成功] ✅ 评论成功")
            
            # 随机延迟
            if index < total:
                delay = random.uniform(RANDOM_DELAY_MIN, RANDOM_DELAY_MAX)
                print(f"[等待] {delay:.1f} 秒后继续...")
                time.sleep(delay)
            
            return True
            
        except Exception as e:
            print(f"[错误] 处理链接时出错: {e}")
            logger.error(f"处理链接时出错: {e}")
            self.stats["fail"] += 1
            return False
    
    def run_batch(self, url_file="urls.txt"):
        """批量处理"""
        # 读取链接
        try:
            with open(url_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not urls:
                print("[错误] urls.txt 中没有有效链接")
                return
            
            print(f"\n[OK] 共读取到 {len(urls)} 个链接")
            
        except Exception as e:
            print(f"[错误] 读取文件失败: {e}")
            return
        
        # 初始化浏览器
        print("\n" + "=" * 60)
        print("🚀 初始化浏览器和视觉Agent...")
        print("=" * 60)
        
        if not self.init_browser():
            print("[错误] 初始化失败")
            return
        
        # 打开抖音首页登录
        print("\n" + "=" * 60)
        print("📋 步骤1: 打开抖音首页")
        print("=" * 60)
        self.page.goto("https://www.douyin.com", wait_until="commit", timeout=60000)
        self.page.wait_for_timeout(5000)
        print("[OK] 抖音首页已打开")
        
        # 等待用户登录
        print("\n" + "=" * 60)
        print("📋 步骤2: 请登录抖音")
        print("=" * 60)
        print("请在浏览器中完成登录（扫码或手机号）")
        print("登录完成后，按回车键继续...")
        input()
        
        # 处理链接
        for i, url in enumerate(urls, 1):
            self.process_single_url(url, i, len(urls))
        
        # 关闭浏览器
        print("\n[提示] 正在保存登录状态...")
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("[OK] 登录状态已保存")
        
        # 打印统计
        print("\n" + "=" * 60)
        print("📊 运行统计")
        print("=" * 60)
        print(f"总处理: {self.stats['total']}")
        print(f"成功: {self.stats['success']}")
        print(f"失败: {self.stats['fail']}")
        print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("抖音评论自动化工具 V4 (视觉Agent版)")
    print("=" * 60)
    print("\n📋 特点：")
    print("✅ 使用视觉模型理解界面")
    print("✅ 不需要GPU，使用云端API")
    print("✅ 登录状态自动保存")
    print("=" * 60)
    
    if not PLAYWRIGHT_AVAILABLE:
        print("\n❌ 错误: Playwright未安装")
        print("\n请运行:")
        print("  pip install playwright")
        print("  python -m playwright install chromium")
        input("\n按回车键退出...")
        return
    
    bot = DouyinBotV4()
    bot.run_batch("urls.txt")
    
    print("\n处理完成！")
    input("按回车键退出...")


if __name__ == "__main__":
    main()
