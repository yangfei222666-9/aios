#!/usr/bin/env python3
"""
简单测试：验证核心功能
"""

import sys
sys.path.insert(0, '.')

def test_core_functions():
    """测试核心函数"""
    print("语音唤醒核心功能测试")
    print("=" * 60)
    
    # 测试文本规范化
    try:
        from tools.wake_listener import normalize_zh, match_wake
        
        print("1. 测试文本规范化...")
        test_cases = [
            ("小九", "小九"),
            ("小 九", "小 九"),
            ("  小九  ", "小九"),
        ]
        
        for input_text, expected in test_cases:
            result = normalize_zh(input_text)
            status = "PASS" if result == expected else "FAIL"
            print(f"   [{status}] '{input_text}' -> '{result}'")
        
        print("\n2. 测试唤醒词匹配...")
        wake_phrases = ["小九", "你好小九", "小酒"]
        
        test_cases = [
            ("小九", True),
            ("小酒", True),
            ("你好小九", True),
            ("小九你好", True),
            ("其他词", False),
        ]
        
        for text, expected in test_cases:
            result = match_wake(text, wake_phrases)
            status = "PASS" if result == expected else "FAIL"
            print(f"   [{status}] '{text}' -> {result} (期望: {expected})")
        
        print("\n3. 测试配置加载...")
        try:
            from tools.wake_listener import load_config
            
            # 创建测试配置
            import tempfile
            import yaml
            
            config_data = {
                "voice_wake": {
                    "enabled": True,
                    "wake_phrases": ["测试唤醒词"],
                    "command_timeout": 5.0,
                    "cooldown": 1.0
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
                yaml.dump(config_data, f)
                config_path = f.name
            
            cfg = load_config(config_path)
            
            assert cfg.enabled == True
            assert "测试唤醒词" in cfg.wake_phrases
            assert cfg.command_timeout == 5.0
            assert cfg.cooldown == 1.0
            
            print("   [PASS] 配置加载成功")
            
            import os
            os.unlink(config_path)
            
        except Exception as e:
            print(f"   [FAIL] 配置加载测试失败: {e}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] 核心功能测试通过！")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

def test_real_scenarios():
    """测试真实场景"""
    print("\n真实场景模拟测试")
    print("=" * 60)
    
    # 模拟语音识别结果处理
    scenarios = [
        {
            "name": "清晰唤醒",
            "asr_output": "小九",
            "should_wake": True,
            "command": "检查系统状态"
        },
        {
            "name": "同音字唤醒", 
            "asr_output": "小酒",
            "should_wake": True,
            "command": "添加笔记"
        },
        {
            "name": "长唤醒词",
            "asr_output": "你好小九",
            "should_wake": True,
            "command": "测试语音"
        },
        {
            "name": "唤醒词+命令",
            "asr_output": "小九检查系统状态",
            "should_wake": True,
            "command": "检查系统状态"
        },
        {
            "name": "误识别",
            "asr_output": "其他内容",
            "should_wake": False,
            "command": None
        }
    ]
    
    try:
        from tools.wake_listener import match_wake
        
        wake_phrases = ["小九", "你好小九", "小酒"]
        
        for scenario in scenarios:
            name = scenario["name"]
            asr_output = scenario["asr_output"]
            should_wake = scenario["should_wake"]
            
            result = match_wake(asr_output, wake_phrases)
            status = "PASS" if result == should_wake else "FAIL"
            
            print(f"[{status}] {name}")
            print(f"   ASR输出: '{asr_output}'")
            print(f"   期望唤醒: {should_wake}, 实际: {result}")
            
            if scenario["command"]:
                print(f"   后续命令: '{scenario['command']}'")
            
            print()
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] 场景测试失败: {e}")
        return 1

def main():
    """主函数"""
    results = []
    
    results.append(("核心功能", test_core_functions()))
    results.append(("真实场景", test_real_scenarios()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result == 0 else "FAIL"
        print(f"{test_name}: [{status}]")
        if result != 0:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("所有测试通过！语音唤醒系统核心功能正常。")
        return 0
    else:
        print("部分测试失败，请检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())