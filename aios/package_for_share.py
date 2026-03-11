#!/usr/bin/env python3
"""
太极OS 打包脚本 - 去敏感版本
用于分享给外部开发者，移除所有个人数据和敏感配置
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# 敏感文件/目录（完全排除）
EXCLUDE_PATHS = [
    'memory/',           # 个人记忆
    'backup/',           # 备份数据
    'drill/',            # 演练报告
    '.env',              # 环境变量
    '__pycache__',       # Python 缓存
    '.pytest_cache',     # 测试缓存
    '*.pyc',             # 编译文件
    '.DS_Store',         # macOS 文件
]

# 需要脱敏的文件（保留结构，清空内容）
SANITIZE_FILES = [
    'data/agents.json',
    'data/selflearn-state.json',
    'data/task_queue.jsonl',
    'data/spawn_pending.jsonl',
    'data/agent_execution_record.jsonl',
    'data/task_executions.jsonl',
    'data/spawn_results.jsonl',
]

# 替换为示例内容的文件
EXAMPLE_FILES = {
    'MEMORY.md': '''# MEMORY.md - 长期记忆（示例）

这是太极OS的长期记忆文件。

在实际使用中，这里会记录：
- 核心使命和目标
- 重要决策和原则
- 学习成果和经验
- 系统演化历史

请根据你的需求自定义此文件。
''',
    'USER.md': '''# USER.md - 用户信息（示例）

- **Name:** [你的名字]
- **Timezone:** Asia/Shanghai
- **Preferences:** [你的偏好]

请根据实际情况填写。
''',
    'IDENTITY.md': '''# IDENTITY.md - AI 身份（示例）

- **Name:** [AI 名字]
- **Creature:** AI 助手
- **Vibe:** [个性描述]

请自定义你的 AI 助手身份。
''',
}

def should_exclude(path: Path, base: Path) -> bool:
    """判断是否应该排除此路径"""
    rel = path.relative_to(base)
    rel_str = str(rel).replace('\\', '/')
    
    for pattern in EXCLUDE_PATHS:
        if pattern.endswith('/'):
            # 目录匹配
            if rel_str.startswith(pattern.rstrip('/')):
                return True
        elif '*' in pattern:
            # 通配符匹配
            import fnmatch
            if fnmatch.fnmatch(rel_str, pattern):
                return True
        else:
            # 精确匹配
            if pattern in rel_str:
                return True
    
    return False

def sanitize_json_file(src: Path, dst: Path):
    """脱敏 JSON 文件 - 保留结构，清空数据"""
    try:
        with open(src, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 根据文件类型处理
        if src.name == 'agents.json':
            # 保留 Agent 定义，清空统计数据
            if 'agents' in data:
                for agent in data['agents']:
                    if 'stats' in agent:
                        agent['stats'] = {
                            'tasks_completed': 0,
                            'tasks_failed': 0,
                            'last_run': None,
                            'total_runtime': 0
                        }
        elif src.name == 'selflearn-state.json':
            # 清空学习状态
            data = {
                'last_run': None,
                'activated_agents': [],
                'pending_lessons': 0,
                'rules_derived_count': 0
            }
        
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  ⚠️  脱敏失败 {src.name}: {e}")
        # 创建空文件
        dst.write_text('{}', encoding='utf-8')

def sanitize_jsonl_file(src: Path, dst: Path):
    """脱敏 JSONL 文件 - 创建空文件"""
    dst.write_text('', encoding='utf-8')

def package_taijios(output_dir: str = None):
    """打包太极OS"""
    
    base = Path(__file__).parent
    
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = base.parent / f'taijios_share_{timestamp}'
    else:
        output_dir = Path(output_dir)
    
    print(f"📦 开始打包太极OS...")
    print(f"   源目录: {base}")
    print(f"   目标目录: {output_dir}")
    print()
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 统计
    total_files = 0
    copied_files = 0
    excluded_files = 0
    sanitized_files = 0
    
    # 遍历所有文件
    for root, dirs, files in os.walk(base):
        root_path = Path(root)
        
        # 过滤目录
        dirs[:] = [d for d in dirs if not should_exclude(root_path / d, base)]
        
        for file in files:
            src = root_path / file
            total_files += 1
            
            # 检查是否排除
            if should_exclude(src, base):
                excluded_files += 1
                continue
            
            # 计算相对路径
            rel = src.relative_to(base)
            dst = output_dir / rel
            
            # 创建目标目录
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查是否需要脱敏
            rel_str = str(rel).replace('\\', '/')
            
            if rel_str in SANITIZE_FILES:
                if src.suffix == '.json':
                    sanitize_json_file(src, dst)
                elif src.suffix == '.jsonl':
                    sanitize_jsonl_file(src, dst)
                sanitized_files += 1
                copied_files += 1
            elif rel_str in EXAMPLE_FILES:
                dst.write_text(EXAMPLE_FILES[rel_str], encoding='utf-8')
                sanitized_files += 1
                copied_files += 1
            else:
                # 直接复制
                shutil.copy2(src, dst)
                copied_files += 1
    
    # 创建 README
    readme = output_dir / 'README_SHARE.md'
    readme.write_text('''# 太极OS - 分享版本

这是太极OS的去敏感版本，适合分享给外部开发者。

## 已移除内容

- 个人记忆文件（memory/）
- 备份数据（backup/）
- 演练报告（drill/）
- 环境配置（.env）
- 运行时数据（已脱敏）

## 已脱敏内容

- Agent 统计数据（保留定义）
- 学习状态（清空历史）
- 任务队列（清空记录）
- 执行记录（清空历史）

## 使用说明

1. 根据实际情况填写 USER.md、IDENTITY.md
2. 配置环境变量（参考 .env.example）
3. 安装依赖：`pip install -r requirements.txt`
4. 启动系统：`python aios.py`

## 核心文档

- `docs/TAIJIOS_PRINCIPLES.md` - 太极OS 五则
- `docs/ARCHITECTURE.md` - 系统架构
- `docs/AGENT_SYSTEM.md` - Agent 系统
- `docs/SKILL_SYSTEM.md` - Skill 系统

## 联系方式

如有问题，请联系原作者。

---

**版本：** 分享版
**打包时间：** ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''
''', encoding='utf-8')
    
    # 输出统计
    print()
    print("✅ 打包完成！")
    print()
    print(f"📊 统计：")
    print(f"   总文件数: {total_files}")
    print(f"   已复制: {copied_files}")
    print(f"   已排除: {excluded_files}")
    print(f"   已脱敏: {sanitized_files}")
    print()
    print(f"📁 输出目录: {output_dir}")
    print()
    print("💡 下一步：")
    print(f"   1. 检查输出目录: {output_dir}")
    print(f"   2. 压缩为 ZIP: Compress-Archive -Path '{output_dir}' -DestinationPath '{output_dir}.zip'")
    print(f"   3. 分享给朋友")
    
    return output_dir

if __name__ == '__main__':
    import sys
    
    output = sys.argv[1] if len(sys.argv) > 1 else None
    package_taijios(output)
