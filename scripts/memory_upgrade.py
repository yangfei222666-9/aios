"""
记忆系统升级 - 自动整理 daily logs → MEMORY.md
从最近的 daily logs 中提取重要信息，更新到 MEMORY.md
"""
import re
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_FILE = WORKSPACE / "MEMORY.md"

def extract_key_info(content, date):
    """从 daily log 中提取关键信息"""
    key_info = []
    
    # 提取标题（## 开头的）
    sections = re.findall(r'^## (.+)$', content, re.MULTILINE)
    
    # 提取完整的列表项（保留完整内容）
    decisions = []
    lessons = []
    progress = []
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line.startswith(('- ', '* ')):
            continue
        
        # 项目进展
        if any(kw in line for kw in ['v0.', 'v1.', 'v2.', 'v3.', '版本', '发布', '完成了', '实现了', '✅']):
            progress.append(line.strip('*- '))
        # 重要决策
        elif any(kw in line for kw in ['决定', '改为', '优化', '修复', '新增', '删除', '调整']):
            decisions.append(line.strip('*- '))
        # 经验教训
        elif any(kw in line for kw in ['教训', '问题', '错误', '失败', '短板', '不足', '需要改进']):
            lessons.append(line.strip('*- '))
    
    return {
        'date': date,
        'sections': sections[:3],
        'decisions': decisions[:5],
        'lessons': lessons[:3],
        'progress': progress[:3]
    }

def read_recent_logs(days=7):
    """读取最近 N 天的 daily logs"""
    logs = []
    today = datetime.now()
    
    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        log_file = MEMORY_DIR / f"{date_str}.md"
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 100:  # 忽略太短的文件
                        info = extract_key_info(content, date_str)
                        logs.append(info)
            except:
                pass
    
    return logs

def generate_summary(logs):
    """生成摘要"""
    if not logs:
        return None
    
    summary = f"## 最近更新（{datetime.now().strftime('%Y-%m-%d')}）\n\n"
    
    # 按日期分组
    for log in logs[:3]:  # 最近3天
        if not (log['progress'] or log['decisions'] or log['lessons']):
            continue
        
        summary += f"### {log['date']}\n\n"
        
        if log['progress']:
            summary += "**项目进展：**\n"
            for item in log['progress']:
                summary += f"- {item}\n"
            summary += "\n"
        
        if log['decisions']:
            summary += "**重要决策：**\n"
            for item in log['decisions'][:3]:
                summary += f"- {item}\n"
            summary += "\n"
        
        if log['lessons']:
            summary += "**经验教训：**\n"
            for item in log['lessons']:
                summary += f"- {item}\n"
            summary += "\n"
    
    return summary if len(summary) > 100 else None

def update_memory_md(summary):
    """更新 MEMORY.md"""
    if not summary:
        print("❌ 没有新内容需要更新")
        return False
    
    # 读取现有 MEMORY.md
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# MEMORY.md - 小九的长期记忆\n\n"
    
    # 检查是否已有"最近更新"章节
    if "## 最近更新" in content:
        # 替换旧的"最近更新"章节
        pattern = r'## 最近更新.*?(?=\n## |\Z)'
        content = re.sub(pattern, summary.rstrip() + '\n\n', content, flags=re.DOTALL)
    else:
        # 在文件开头插入（在标题后）
        lines = content.split('\n')
        if lines[0].startswith('# '):
            content = lines[0] + '\n\n' + summary + '\n'.join(lines[1:])
        else:
            content = summary + content
    
    # 写回文件
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ MEMORY.md 已更新")
    print(f"📝 添加了最近 {len(summary.split('###')) - 1} 天的摘要")
    
    return True

def update_state_file():
    """更新 selflearn-state.json 的时间戳"""
    state_file = MEMORY_DIR / "selflearn-state.json"
    
    if state_file.exists():
        try:
            import json
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            state['last_memory_upgrade'] = datetime.now().isoformat()
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 更新了 selflearn-state.json")
        except:
            pass

def main():
    print("=" * 60)
    print("🧠 记忆系统升级 - 自动整理 daily logs")
    print("=" * 60)
    print()
    
    # 读取最近7天的日志
    print("📖 读取最近 7 天的 daily logs...")
    logs = read_recent_logs(days=7)
    print(f"  ✓ 找到 {len(logs)} 个有效日志")
    print()
    
    # 生成摘要
    print("📝 生成摘要...")
    summary = generate_summary(logs)
    
    if summary:
        print("  ✓ 摘要生成完成")
        print()
        print("预览：")
        print("-" * 60)
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        print("-" * 60)
        print()
        
        # 更新 MEMORY.md
        print("💾 更新 MEMORY.md...")
        success = update_memory_md(summary)
        
        if success:
            # 更新状态文件
            update_state_file()
    else:
        print("  ⚠️  没有足够的内容生成摘要")
    
    print()
    print("=" * 60)
    print("✅ 完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
