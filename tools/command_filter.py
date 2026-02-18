#!/usr/bin/env python3
"""
命令过滤器
过滤无意义的语音命令
"""

# 忽略的命令列表（纯问候/寒暄）
IGNORE_CMDS = {"你好", "在吗", "喂", "哈喽", "hello", "hi", "hey", "嗨"}

def normalize_command(cmd: str) -> str:
    """规范化命令文本"""
    if not cmd:
        return ""
    # 移除空格并转换为小写（用于英文匹配）
    return cmd.replace(" ", "").strip()

def is_meaningful_command(cmd: str, wake_phrases: list[str]) -> bool:
    """
    判断命令是否有意义
    
    参数:
        cmd: 原始命令文本
        wake_phrases: 唤醒词列表
    
    返回:
        bool: True 表示有意义，False 表示应忽略
    """
    # 规范化命令
    t = normalize_command(cmd)
    if not t:
        return False
    
    # 规范化唤醒词
    normalized_wake_phrases = [wp.replace(" ", "") for wp in wake_phrases]
    
    # 规则1: 只包含唤醒词 -> 忽略
    if any(t == wp for wp in normalized_wake_phrases):
        return False
    
    # 规则2: 只包含寒暄词 -> 忽略
    if t in IGNORE_CMDS:
        return False
    
    # 规则3: 太短 -> 忽略（可调整阈值）
    if len(t) <= 2:
        return False
    
    # 规则4: 检查是否只是唤醒词+寒暄的组合
    # 例如："小九你好" -> 应该忽略
    for wp in normalized_wake_phrases:
        if t.startswith(wp):
            remaining = t[len(wp):]
            if not remaining or remaining in IGNORE_CMDS or len(remaining) <= 1:
                return False
    
    # 规则5: 检查是否只是寒暄+唤醒词的组合
    # 例如："你好小九" -> 应该忽略
    for greeting in IGNORE_CMDS:
        if t.startswith(greeting):
            remaining = t[len(greeting):]
            if not remaining or remaining in normalized_wake_phrases:
                return False
    
    # 规则6: 检查是否包含有效的中文内容
    # 简单检查：是否包含常见的中文动词或名词
    meaningful_keywords = {
        # 动作/命令
        "检查", "查看", "打开", "关闭", "播放", "停止",
        "添加", "删除", "搜索", "查找", "设置", "调整",
        "告诉", "说", "读", "写", "记", "录",
        
        # 对象/主题
        "状态", "系统", "笔记", "音乐", "天气", "时间",
        "新闻", "邮件", "消息", "文件", "照片", "视频",
        
        # 疑问词
        "什么", "怎么", "为什么", "何时", "哪里", "谁",
        
        # 具体命令
        "今天", "明天", "现在", "刚才", "最近",
    }
    
    # 如果包含有意义的关键词，则认为是有效命令
    for keyword in meaningful_keywords:
        if keyword in t:
            return True
    
    # 规则7: 长度适中且不是纯重复字符
    if 3 <= len(t) <= 50:
        # 检查是否纯重复字符
        if len(set(t)) <= 2 and len(t) > 3:
            return False
        return True
    
    return False

def filter_command(cmd: str, wake_phrases: list[str]) -> tuple[bool, str]:
    """
    过滤命令并返回结果和原因
    
    返回:
        tuple: (是否有效, 原因说明)
    """
    t = normalize_command(cmd)
    
    if not t:
        return False, "命令为空"
    
    normalized_wake_phrases = [wp.replace(" ", "") for wp in wake_phrases]
    
    # 检查各种情况
    if any(t == wp for wp in normalized_wake_phrases):
        return False, "只包含唤醒词"
    
    if t in IGNORE_CMDS:
        return False, "只包含寒暄词"
    
    if len(t) <= 2:
        return False, f"命令太短 ({len(t)}个字符)"
    
    # 检查唤醒词+寒暄的组合
    for wp in normalized_wake_phrases:
        if t.startswith(wp):
            remaining = t[len(wp):]
            if not remaining:
                return False, "只包含唤醒词"
            if remaining in IGNORE_CMDS:
                return False, "唤醒词+寒暄"
            if len(remaining) <= 1:
                return False, "唤醒词+单字"
    
    # 检查寒暄+唤醒词的组合
    for greeting in IGNORE_CMDS:
        if t.startswith(greeting):
            remaining = t[len(greeting):]
            if not remaining:
                return False, "只包含寒暄词"
            if remaining in normalized_wake_phrases:
                return False, "寒暄+唤醒词"
    
    # 默认认为有效
    return True, "有效命令"

def test_filter():
    """测试过滤器"""
    wake_phrases = ["小九", "你好小九", "小酒", "hi 小九", "hey 小九"]
    
    test_cases = [
        # 应该忽略的
        ("小九", False, "只包含唤醒词"),
        ("小酒", False, "只包含唤醒词（同音字）"),
        ("你好", False, "只包含寒暄"),
        ("hi", False, "英文寒暄"),
        ("喂", False, "单字寒暄"),
        ("小九你好", False, "唤醒词+寒暄"),
        ("你好小九", False, "寒暄+唤醒词"),
        ("小九好", False, "唤醒词+单字"),
        ("嗯", False, "单字语气词"),
        ("啊", False, "单字语气词"),
        
        # 应该接受的
        ("检查系统状态", True, "有效命令"),
        ("小九检查状态", True, "唤醒词+命令"),
        ("添加笔记测试", True, "有效命令"),
        ("今天天气怎么样", True, "疑问句"),
        ("播放音乐", True, "动作命令"),
        ("打开灯光", True, "动作命令"),
        ("小九告诉我时间", True, "唤醒词+完整命令"),
        ("搜索人工智能", True, "搜索命令"),
        ("设置闹钟明天八点", True, "设置命令"),
        ("删除昨天的笔记", True, "删除命令"),
    ]
    
    print("命令过滤器测试")
    print("=" * 60)
    print(f"唤醒词: {wake_phrases}")
    print(f"忽略词: {IGNORE_CMDS}")
    print()
    
    all_passed = True
    
    for cmd, expected, description in test_cases:
        result, reason = filter_command(cmd, wake_phrases)
        passed = result == expected
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {description}")
        print(f"  命令: '{cmd}'")
        print(f"  期望: {expected}, 实际: {result}")
        if not passed:
            print(f"  原因: {reason}")
        print()
        
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] 所有测试通过")
    else:
        print("[WARNING] 有测试失败")
    
    return all_passed

if __name__ == "__main__":
    test_filter()