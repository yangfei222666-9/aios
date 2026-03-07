#!/usr/bin/env python3
"""
Web Monitor - 通用网页监控系统
支持多目标、多策略、分级通知
"""
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
import urllib.request
import urllib.error
import yaml

# 配置文件
CONFIG_FILE = Path(__file__).parent / "web_monitor_config.yaml"
STATE_FILE = Path(__file__).parent / "web_monitor_state.json"
NOTIFY_FILE = Path(__file__).parent / "web_monitor_notify.json"

def load_config():
    """加载配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_state():
    """加载监控状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存监控状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def fetch_content(url, timeout=10):
    """获取网页内容"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read()
            # 尝试解码
            try:
                return content.decode('utf-8')
            except:
                return content.decode('latin-1')
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None

def detect_change_json_field(content, field_path):
    """检测 JSON 字段变化"""
    try:
        data = json.loads(content)
        # 支持简单路径：[0] 或 n.champion
        if field_path.startswith('['):
            # 数组索引
            idx = int(field_path.strip('[]'))
            return str(data[idx]) if isinstance(data, list) and len(data) > idx else None
        elif '.' in field_path:
            # 嵌套字段
            keys = field_path.split('.')
            value = data
            for key in keys:
                value = value.get(key)
                if value is None:
                    return None
            return str(value)
        else:
            return str(data.get(field_path))
    except Exception as e:
        print(f"[ERROR] JSON parse failed: {e}")
        return None

def detect_change_first_item(content, selector=None):
    """检测列表页第一条标题变化"""
    # 简单正则提取（不依赖 BeautifulSoup）
    patterns = [
        r'<h1[^>]*>(.*?)</h1>',
        r'<h2[^>]*>(.*?)</h2>',
        r'<article[^>]*>.*?<h2[^>]*>(.*?)</h2>',
        r'class="article-title"[^>]*>(.*?)</(?:a|span|div)>',
        r'class="post-title"[^>]*>(.*?)</(?:a|span|div)>',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # 清理 HTML 标签
            title = re.sub(r'<[^>]+>', '', title)
            return title[:200]  # 限制长度
    
    return None

def detect_change_content_hash(content):
    """检测内容哈希变化"""
    # 移除动态内容（时间戳、随机ID等）
    cleaned = re.sub(r'\d{4}-\d{2}-\d{2}', '', content)
    cleaned = re.sub(r'id="[^"]*"', '', cleaned)
    return hashlib.md5(cleaned.encode()).hexdigest()[:16]

def check_monitor(monitor, state, config):
    """检查单个监控项"""
    name = monitor['name']
    url = monitor['url']
    purpose = monitor['purpose']
    
    print(f"\n[CHECK] {name}")
    print(f"   URL: {url}")
    print(f"   Purpose: {purpose}")
    
    # 获取内容
    content = fetch_content(url)
    if content is None:
        print(f"[SKIP] Failed to fetch content")
        return None
    
    # 根据 purpose 选择检测策略
    detection_config = config['detection'].get(purpose, {})
    method = detection_config.get('method', 'content_hash')
    
    current_value = None
    if method == 'json_field':
        field = detection_config.get('field', '[0]')
        current_value = detect_change_json_field(content, field)
    elif method == 'first_item_title':
        selector = detection_config.get('selector')
        current_value = detect_change_first_item(content, selector)
    elif method == 'content_hash':
        current_value = detect_change_content_hash(content)
    
    if current_value is None:
        print(f"[WARN] Failed to extract value")
        return None
    
    print(f"   Current: {current_value[:100]}")
    
    # 对比状态
    monitor_state = state.get(name, {})
    last_value = monitor_state.get('last_value')
    last_check = monitor_state.get('last_check')
    last_notify = monitor_state.get('last_notify')
    
    # 更新状态
    new_state = {
        'last_value': current_value,
        'last_check': datetime.now().isoformat(),
        'last_notify': last_notify
    }
    
    # 检测变化
    if last_value is None:
        print(f"[INFO] First check, baseline set")
        return new_state
    
    if current_value != last_value:
        print(f"[CHANGE] Detected!")
        print(f"   Old: {last_value[:100]}")
        print(f"   New: {current_value[:100]}")
        
        # 检查通知间隔
        min_interval = config['notification']['min_interval_hours']
        should_notify = True
        
        if last_notify:
            last_notify_time = datetime.fromisoformat(last_notify)
            if datetime.now() - last_notify_time < timedelta(hours=min_interval):
                print(f"[SKIP] Notified recently (within {min_interval}h)")
                should_notify = False
        
        if should_notify:
            # 生成通知
            notify_types = monitor.get('notify', ['heartbeat'])
            message = format_notification(monitor, current_value, last_value)
            
            if 'telegram' in notify_types or 'telegram_major' in notify_types:
                queue_notification(message, 'telegram', config)
                new_state['last_notify'] = datetime.now().isoformat()
            
            print(f"[NOTIFY] Queued: {message[:100]}")
    else:
        print(f"[OK] No change")
    
    return new_state

def format_notification(monitor, new_value, old_value):
    """格式化通知消息"""
    name = monitor['name']
    url = monitor['url']
    
    # 根据类型定制消息
    if 'version' in monitor['purpose'].lower():
        return f"🔔 {name} 版本更新\n\n旧版本: {old_value}\n新版本: {new_value}\n\n{url}"
    elif 'patch' in monitor['purpose'].lower():
        return f"📋 {name} 新补丁上线\n\n{new_value}\n\n{url}"
    elif 'api' in monitor['purpose'].lower():
        return f"⚠️ {name} API 变更\n\n{new_value}\n\n{url}"
    else:
        return f"🆕 {name} 更新\n\n{new_value}\n\n{url}"

def queue_notification(message, channel, config):
    """队列通知（写入文件，由 handler 处理）"""
    notify_data = {
        'timestamp': datetime.now().isoformat(),
        'channel': channel,
        'chat_id': config['notification']['telegram_chat_id'],
        'message': message
    }
    
    # 追加到通知队列
    notifications = []
    if NOTIFY_FILE.exists():
        with open(NOTIFY_FILE, 'r', encoding='utf-8') as f:
            try:
                notifications = json.load(f)
            except:
                notifications = []
    
    notifications.append(notify_data)
    
    with open(NOTIFY_FILE, 'w', encoding='utf-8') as f:
        json.dump(notifications, f, indent=2, ensure_ascii=False)

def main():
    """主函数"""
    import sys
    
    print(f"[START] Web Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载配置和状态
    config = load_config()
    state = load_state()
    
    # 检查所有启用的监控项
    monitors = [m for m in config['monitors'] if m.get('enabled', True)]
    
    # 支持按频率过滤
    if len(sys.argv) > 1 and sys.argv[1] == '--filter':
        frequency_filter = sys.argv[2] if len(sys.argv) > 2 else None
        if frequency_filter:
            monitors = [m for m in monitors if m.get('frequency') == frequency_filter]
            print(f"[FILTER] Frequency: {frequency_filter}")
    
    print(f"[INFO] Total monitors: {len(monitors)}")
    
    changes_detected = 0
    for monitor in monitors:
        new_state = check_monitor(monitor, state, config)
        if new_state:
            state[monitor['name']] = new_state
            if new_state.get('last_value') != state.get(monitor['name'], {}).get('last_value'):
                changes_detected += 1
    
    # 保存状态
    save_state(state)
    
    print(f"\n[DONE] Changes detected: {changes_detected}")
    print(f"[SAVE] State saved to {STATE_FILE}")

if __name__ == "__main__":
    main()
