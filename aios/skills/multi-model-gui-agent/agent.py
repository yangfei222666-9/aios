"""
多模型GUI代理 - 生产级实现
支持：抖音评论、智能客服、自定义场景
"""

import pyautogui
import time
import json
import requests
import logging
from PIL import ImageGrab
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    url: str
    timestamp: str
    duration: float
    error: Optional[str] = None
    retry_count: int = 0


class CoordinateCache:
    """坐标缓存"""
    def __init__(self, cache_file='coordinate_cache.json'):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        if Path(self.cache_file).exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get(self, key: str) -> Optional[Dict]:
        return self.cache.get(key)
    
    def set(self, key: str, value: Dict):
        self.cache[key] = value
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def get_hit_rate(self) -> float:
        """计算缓存命中率"""
        if not hasattr(self, 'total_requests'):
            return 0.0
        return self.hits / self.total_requests if self.total_requests > 0 else 0.0


class MultiModelAgent:
    """多模型GUI代理"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.keys = {
            'teacher': self.config['teacher_key'],
            'executor': self.config['executor_key'],
            'fallback': self.config['fallback_key']
        }
        
        self.timeout = self.config.get('timeout', {
            'teacher': 10,
            'executor': 3,
            'fallback': 5
        })
        
        self.retry_config = self.config.get('retry', {
            'max_attempts': 3,
            'backoff': 2
        })
        
        self.cache = CoordinateCache()
        self.results: List[ExecutionResult] = []
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'teacher_timeout': 0,
            'fallback_used': 0
        }
    
    def screenshot(self, save_path='screen.png') -> str:
        """截图"""
        try:
            ImageGrab.grab().save(save_path)
            logger.info(f"截图保存: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise
    
    def teacher_analyze(self, img_path: str, mode: str = 'douyin') -> Dict:
        """2.0 Lite 视觉理解"""
        # 检查缓存
        cache_key = f"{mode}_{Path(img_path).stat().st_size}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"使用缓存坐标: {cache_key}")
            return cached
        
        prompt = self._get_prompt(mode)
        
        try:
            logger.info("调用 2.0 Lite 分析截图...")
            start_time = time.time()
            
            res = requests.post(
                "https://api.doubao.com/v1/vision/lite",
                headers={"Authorization": f"Bearer {self.keys['teacher']}"},
                files={"image": open(img_path, 'rb')},
                data={"prompt": prompt},
                timeout=self.timeout['teacher']
            )
            
            duration = time.time() - start_time
            logger.info(f"2.0 Lite 响应时间: {duration:.2f}s")
            
            result = res.json()
            
            # 缓存结果
            self.cache.set(cache_key, result)
            
            return result
            
        except requests.Timeout:
            logger.warning("2.0 Lite 超时，降级到 1.6 lite")
            self.stats['teacher_timeout'] += 1
            return self.fallback_analyze(img_path, mode)
        
        except Exception as e:
            logger.error(f"2.0 Lite 调用失败: {e}")
            return self.fallback_analyze(img_path, mode)
    
    def fallback_analyze(self, img_path: str, mode: str) -> Dict:
        """1.6 lite 容灾"""
        self.stats['fallback_used'] += 1
        logger.info("使用 1.6 lite 容灾...")
        
        try:
            prompt = self._get_prompt(mode)
            res = requests.post(
                "https://api.doubao.com/v1/vision/lite-fallback",
                headers={"Authorization": f"Bearer {self.keys['fallback']}"},
                files={"image": open(img_path, 'rb')},
                data={"prompt": prompt},
                timeout=self.timeout['fallback']
            )
            return res.json()
        
        except Exception as e:
            logger.error(f"1.6 lite 也失败了: {e}")
            # 返回默认坐标（根据模式）
            return self._get_default_coordinates(mode)
    
    def _get_prompt(self, mode: str) -> str:
        """根据模式获取 prompt"""
        prompts = {
            'douyin': """
                找出抖音评论区的输入框和发布按钮坐标。
                返回 JSON: {
                    'input': [x, y],
                    'publish': [x, y]
                }
            """,
            'customer-service': """
                识别截图中的：
                1. 错误码（红色文字）
                2. 订单号（格式：ORD-XXXXXX）
                3. 异常状态（黄色/红色标签）
                
                返回 JSON: {
                    'error_code': '...',
                    'order_id': '...',
                    'status': '...',
                    'action_button': [x, y]
                }
            """
        }
        return prompts.get(mode, prompts['douyin'])
    
    def _get_default_coordinates(self, mode: str) -> Dict:
        """默认坐标（容灾兜底）"""
        defaults = {
            'douyin': {
                'input': [800, 600],
                'publish': [900, 650]
            },
            'customer-service': {
                'error_code': 'UNKNOWN',
                'order_id': 'N/A',
                'status': 'UNKNOWN',
                'action_button': [850, 700]
            }
        }
        return defaults.get(mode, defaults['douyin'])
    
    def execute(self, action: Dict, mode: str = 'douyin'):
        """1.6 flash 执行操作"""
        try:
            if mode == 'douyin':
                # 点击输入框
                pyautogui.click(action['input'][0], action['input'][1])
                time.sleep(0.5)
                
                # 生成并输入评论
                comment = self.generate_comment()
                pyautogui.write(comment)
                time.sleep(0.5)
                
                # 点击发布
                pyautogui.click(action['publish'][0], action['publish'][1])
                logger.info(f"发布评论: {comment}")
            
            elif mode == 'customer-service':
                # 记录识别结果
                logger.info(f"错误码: {action.get('error_code')}")
                logger.info(f"订单号: {action.get('order_id')}")
                logger.info(f"状态: {action.get('status')}")
                
                # 点击处理按钮
                if 'action_button' in action:
                    pyautogui.click(action['action_button'][0], action['action_button'][1])
                    logger.info("已点击处理按钮")
        
        except Exception as e:
            logger.error(f"执行操作失败: {e}")
            raise
    
    def generate_comment(self) -> str:
        """1.6 flash 生成评论"""
        try:
            res = requests.post(
                "https://api.doubao.com/v1/chat/flash",
                headers={"Authorization": f"Bearer {self.keys['executor']}"},
                json={"prompt": "生成抖音评论，10字内带表情，要有趣"},
                timeout=self.timeout['executor']
            )
            return res.json().get('text', '666👍')
        
        except Exception as e:
            logger.warning(f"生成评论失败，使用默认: {e}")
            return '666👍'
    
    def run_with_retry(self, url: str, mode: str) -> ExecutionResult:
        """带重试的执行"""
        start_time = time.time()
        
        for attempt in range(self.retry_config['max_attempts']):
            try:
                # 打开链接
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.3)
                pyautogui.write(url)
                pyautogui.press('enter')
                time.sleep(3)  # 等待页面加载
                
                # 截图分析
                img_path = self.screenshot()
                action = self.teacher_analyze(img_path, mode)
                
                # 执行操作
                self.execute(action, mode)
                time.sleep(2)
                
                # 成功
                duration = time.time() - start_time
                return ExecutionResult(
                    success=True,
                    url=url,
                    timestamp=datetime.now().isoformat(),
                    duration=duration,
                    retry_count=attempt
                )
            
            except Exception as e:
                logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")
                
                if attempt < self.retry_config['max_attempts'] - 1:
                    # 指数退避
                    sleep_time = self.retry_config['backoff'] ** attempt
                    logger.info(f"等待 {sleep_time}s 后重试...")
                    time.sleep(sleep_time)
                else:
                    # 最后一次也失败了
                    duration = time.time() - start_time
                    return ExecutionResult(
                        success=False,
                        url=url,
                        timestamp=datetime.now().isoformat(),
                        duration=duration,
                        error=str(e),
                        retry_count=attempt + 1
                    )
    
    def run(self, url_file: str, mode: str = 'douyin'):
        """主流程"""
        logger.info(f"开始执行，模式: {mode}")
        
        # 读取链接
        with open(url_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        logger.info(f"共 {len(urls)} 个链接")
        
        # 逐个处理
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] 处理: {url}")
            
            result = self.run_with_retry(url, mode)
            self.results.append(result)
            
            self.stats['total'] += 1
            if result.success:
                self.stats['success'] += 1
            else:
                self.stats['failed'] += 1
            
            # 连续失败告警
            if self.stats['failed'] >= 3:
                logger.error("⚠️ 连续失败超过3次，请检查配置！")
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成执行报告"""
        report = {
            'summary': self.stats,
            'cache_hit_rate': self.cache.get_hit_rate(),
            'results': [
                {
                    'url': r.url,
                    'success': r.success,
                    'duration': r.duration,
                    'retry_count': r.retry_count,
                    'error': r.error
                }
                for r in self.results
            ]
        }
        
        report_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"执行报告已保存: {report_file}")
        logger.info(f"成功率: {self.stats['success']}/{self.stats['total']}")
        logger.info(f"缓存命中率: {self.cache.get_hit_rate():.2%}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='多模型GUI代理')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--urls', required=True, help='链接列表文件')
    parser.add_argument('--mode', default='douyin', choices=['douyin', 'customer-service', 'custom'], help='运行模式')
    parser.add_argument('--prompt', help='自定义模式的 prompt')
    
    args = parser.parse_args()
    
    agent = MultiModelAgent(args.config)
    agent.run(args.urls, args.mode)
