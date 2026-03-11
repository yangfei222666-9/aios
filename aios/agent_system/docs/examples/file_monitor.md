# 文件监控场景

监控指定目录的文件变化（创建、修改、删除），自动记录事件并触发相应处理。
适用于配置文件热更新、日志文件分析、文档同步等场景。
支持过滤规则、事件回调和持久化日志。

## 核心代码

```python
import os
import time
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileMonitor(FileSystemEventHandler):
    def __init__(self, log_file="monitor.log", patterns=None):
        self.log_file = log_file
        self.patterns = patterns or ["*"]
        
    def _should_process(self, path):
        if self.patterns == ["*"]:
            return True
        return any(Path(path).match(p) for p in self.patterns)
    
    def _log_event(self, event_type, path):
        if not self._should_process(path):
            return
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "path": path
        }
        
        print(f"[{event['timestamp']}] {event_type}: {path}")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    def on_created(self, event):
        if not event.is_directory:
            self._log_event("CREATED", event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self._log_event("MODIFIED", event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._log_event("DELETED", event.src_path)

def start_monitor(watch_dir, patterns=None):
    """启动文件监控"""
    if not os.path.exists(watch_dir):
        os.makedirs(watch_dir)
    
    event_handler = FileMonitor(patterns=patterns)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=True)
    observer.start()
    
    print(f"开始监控目录: {watch_dir}")
    print(f"过滤规则: {patterns or ['*']}")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n监控已停止")
    
    observer.join()

if __name__ == "__main__":
    # 监控当前目录下的 test_dir，只关注 .txt 和 .json 文件
    start_monitor("./test_dir", patterns=["*.txt", "*.json"])
```

## 运行命令

```bash
pip install watchdog && python file_monitor.py
```

## 预期输出

```
开始监控目录: ./test_dir
过滤规则: ['*.txt', '*.json']
按 Ctrl+C 停止监控

[2024-01-15T10:23:45.123456] CREATED: ./test_dir/config.json
[2024-01-15T10:23:50.234567] MODIFIED: ./test_dir/config.json
[2024-01-15T10:24:01.345678] CREATED: ./test_dir/notes.txt
[2024-01-15T10:24:15.456789] DELETED: ./test_dir/notes.txt
```

## 扩展建议

- 添加邮件/消息通知
- 集成文件内容差异对比
- 支持远程目录监控（SMB/NFS）
- 实现事件聚合和去重
