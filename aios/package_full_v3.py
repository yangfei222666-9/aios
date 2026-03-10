#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS v3.4 完整打包脚本
创建 AIOS-Full-v3.4-{date}.zip
"""
import sys
import os
import zipfile
from pathlib import Path
import json
from datetime import datetime

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

AIOS_ROOT = Path(__file__).parent

# 排除模式（不打包的内容）
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    "*.egg-info",
    "dist_exe",
    "dist_full",
    "build_full_tmp",
    "build_output",
    ".git",
    ".github",
    "archive",
    "backups",
    "logs/*.log",
    "*.zip",
    "*.spec",
    "aios.db",
    "AIOS-Friend-Edition",
    "aios-independent",
    "AIOS-Portable",
]

def should_include(path: Path, root: Path) -> bool:
    """判断是否应该包含该文件"""
    try:
        path_str = str(path.relative_to(root))
    except ValueError:
        return False
    
    # 检查排除模式
    for pattern in EXCLUDE_PATTERNS:
        if pattern.endswith("/"):
            if pattern[:-1] in path_str.split(os.sep):
                return False
        elif pattern.startswith("*."):
            if path.name.endswith(pattern[1:]):
                return False
        elif "*" in pattern:
            # 通配符匹配（简单实现）
            parts = pattern.split("*")
            if all(part in path_str for part in parts):
                return False
        elif pattern in path_str:
            return False
    
    return True

def create_package():
    """创建完整打包文件"""
    print("=" * 70)
    print("  📦 AIOS v3.4 完整打包工具")
    print("=" * 70)
    
    # 输出文件
    date_str = datetime.now().strftime("%Y%m%d-%H%M")
    output_file = AIOS_ROOT / f"AIOS-Full-v3.4-{date_str}.zip"
    
    if output_file.exists():
        print(f"\n⚠️  删除旧文件: {output_file.name}")
        output_file.unlink()
    
    print(f"\n📝 创建打包文件: {output_file.name}")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        file_count = 0
        
        print("\n📦 打包 AIOS 完整系统...")
        
        # 遍历所有文件
        for file_path in AIOS_ROOT.rglob("*"):
            if file_path.is_file() and should_include(file_path, AIOS_ROOT):
                arcname = f"aios/{file_path.relative_to(AIOS_ROOT)}"
                zf.write(file_path, arcname)
                file_count += 1
                
                if file_count % 100 == 0:
                    print(f"   已打包 {file_count} 个文件...")
        
        print(f"\n   ✅ 共打包 {file_count} 个文件")
        
        # ========== 创建安装说明 ==========
        print("\n📝 生成安装说明...")
        install_guide = """# AIOS v3.4 完整版安装指南

## 🎯 版本亮点

**v3.4 核心能力：**
- ✅ Evolution Score 99.5/100（置信度融合）
- ✅ 64卦智慧决策系统
- ✅ Bull vs Bear 对抗验证
- ✅ Skill Memory（技能记忆与演化）
- ✅ LowSuccess Agent（失败自动重生）
- ✅ LanceDB 经验学习
- ✅ 完整可观测性（Dashboard + 每日简报）
- ✅ 自动化心跳系统

## 📦 包含内容

- **核心系统** - agent_system/（调度、执行、学习）
- **Dashboard** - dashboard/（可视化监控）
- **64卦决策** - core/bigua/（智慧决策引擎）
- **学习系统** - learning/（经验积累与应用）
- **可观测性** - observability/（指标、告警、报告）
- **完整文档** - docs/（架构、API、教程）
- **测试套件** - tests/（单元测试、集成测试）

## 🚀 快速开始

### 1. 解压文件

```bash
unzip AIOS-Full-v3.4-*.zip
cd aios
```

### 2. 安装依赖

**Windows:**
```cmd
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
pip3 install -r requirements.txt
```

### 3. 运行演示

```bash
python aios.py demo
```

### 4. 启动 Dashboard

```bash
python aios.py dashboard
# 访问 http://127.0.0.1:8888
```

## 🔧 配置

### 基础配置

编辑 `config.yaml`：

```yaml
dashboard:
  port: 8888
  host: 127.0.0.1

agent_system:
  max_workers: 5
  timeout: 120

learning:
  enable_recommendation: true
  grayscale_ratio: 0.5
```

### 环境变量（可选）

```bash
# API 配置
export OPENAI_API_KEY=sk-xxxxx
export PERPLEXITY_API_KEY=pplx-xxxxx

# Telegram 通知（可选）
export TELEGRAM_BOT_TOKEN=xxxxx
export TELEGRAM_CHAT_ID=xxxxx
```

## 📊 核心功能

### 1. 任务提交

```bash
python aios.py submit --desc "重构 scheduler.py" --type code --priority high
```

### 2. 查看任务

```bash
python aios.py tasks
```

### 3. 心跳执行

```bash
python aios.py heartbeat
```

### 4. 系统健康检查

```bash
python aios.py health
```

### 5. 查看 Evolution Score

```bash
python aios.py evolution
```

## 🧠 学习系统

AIOS 会自动从失败中学习：

1. **失败记录** - 自动记录到 `lessons.json`
2. **经验推荐** - LanceDB 向量检索历史成功策略
3. **自动重生** - LowSuccess Agent 自动重试失败任务
4. **策略优化** - 根据成功率自动调整策略

## 📈 可观测性

### Dashboard

访问 http://127.0.0.1:8888 查看：
- 实时任务状态
- Evolution Score 趋势
- Agent 性能统计
- 错误分布分析
- SLO 健康度

### 每日简报

自动生成并推送到 Telegram（如果配置）：
- 任务统计
- 成功率趋势
- Top 错误
- 改进建议

## 🔍 故障排查

### Q: Dashboard 打不开？

```bash
# 检查端口占用
netstat -ano | findstr :8888  # Windows
lsof -i :8888  # Linux/Mac

# 修改端口
# 编辑 config.yaml，修改 dashboard.port
```

### Q: 任务不执行？

```bash
# 查看日志
cat agent_system/dispatcher.log

# 检查队列
python aios.py tasks
```

### Q: Evolution Score 不更新？

```bash
# 手动触发计算
cd agent_system
python evolution_fusion.py
```

### Q: LanceDB 推荐失败？

```bash
# 检查向量库
cd agent_system
python -c "from experience_learner_v4 import ExperienceLearner; learner = ExperienceLearner(); print(f'Trajectories: {learner.count_trajectories()}')"
```

## 📚 文档

- **架构文档** - `docs/ARCHITECTURE.md`
- **API 文档** - `docs/API.md`
- **开发指南** - `docs/CONTRIBUTING.md`
- **更新日志** - `CHANGELOG.md`

## 💡 系统要求

- Python 3.8+
- 8GB+ RAM（推荐 16GB）
- 2GB+ 磁盘空间
- Windows / Linux / macOS

## 🆘 获取帮助

- GitHub Issues: https://github.com/yangfei222666-9/aios/issues
- Telegram: @shh7799
- 文档: `docs/`

## 📝 版本历史

### v3.4 (2026-03-07)
- Evolution Score 融合（99.5/100）
- Skill Memory Phase 2
- Bull vs Bear 对抗验证
- 错误分类优化
- Dashboard SLO 可视化

### v3.3 (2026-03-05)
- LowSuccess Agent Phase 3
- Agent 市场 MVP
- 统计同步系统

### v3.2 (2026-03-04)
- LanceDB 向量检索
- 自动监控系统
- Phase 3 观察脚本

---

**版本：** v3.4  
**发布日期：** 2026-03-07  
**作者：** 小九 + 珊瑚海  
**许可证：** MIT
"""
        
        zf.writestr("INSTALL.md", install_guide)
        file_count += 1
        
        # ========== 创建版本信息 ==========
        version_info = {
            "version": "3.4.0",
            "release_date": datetime.now().isoformat(),
            "evolution_score": 99.5,
            "confidence": 99.5,
            "features": [
                "Evolution Score 融合（99.5/100）",
                "64卦智慧决策系统",
                "Bull vs Bear 对抗验证",
                "Skill Memory（技能记忆与演化）",
                "LowSuccess Agent（失败自动重生）",
                "LanceDB 经验学习",
                "完整可观测性",
                "自动化心跳系统",
                "Dashboard SLO 可视化",
                "每日/周报自动推送"
            ],
            "stats": {
                "agents": 64,
                "skills": 44,
                "tests": 200,
                "files": file_count
            }
        }
        
        zf.writestr("VERSION.json", json.dumps(version_info, indent=2, ensure_ascii=False))
        file_count += 1
        
        print(f"\n✅ 打包完成！共 {file_count} 个文件")
    
    # 显示文件大小
    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"📊 文件大小: {size_mb:.2f} MB")
    print(f"📁 输出路径: {output_file}")
    
    print("\n" + "=" * 70)
    print("  ✅ 打包成功！")
    print("=" * 70)
    
    print("\n💡 分享给朋友:")
    print(f"   文件: {output_file.name}")
    print(f"   大小: {size_mb:.2f} MB")
    print("   解压后阅读 INSTALL.md 开始使用")

if __name__ == "__main__":
    try:
        create_package()
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
