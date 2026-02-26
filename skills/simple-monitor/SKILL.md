---
name: simple-monitor
description: Simple server monitoring tool
---

# Simple Monitor

## 功能

Simple server monitoring tool

## 使用方式

### 命令行

```bash
python test_monitor.py [参数]
```

### 在 OpenClaw 中使用

当用户询问相关需求时，运行：

```bash
cd C:\Users\A\.openclaw\workspace\skills\simple-monitor
python test_monitor.py
```

## 核心功能

### 主要函数

- `get_cpu_usage()` - Get Cpu Usage
- `get_memory_usage()` - Get Memory Usage
- `get_disk_usage()` - Get Disk Usage
- `get_system_info()` - Get System Info
- `monitor()` - Monitor

## 依赖

- platform
- psutil

## 元数据

- **分类:** monitoring
- **关键词:** system, disk, get, cpu, memory, server, monitor
- **创建时间:** 2026-02-26

## 维护

如需修改此 skill，编辑 `test_monitor.py` 并更新本文档。

---

**版本:** 1.0  
**创建者:** skill-creator  
**最后更新:** 2026-02-26
