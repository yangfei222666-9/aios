"""
Agent Lifecycle Engine 娴嬭瘯濂椾欢

娴嬭瘯鍦烘櫙锛?1. 婊戝姩绐楀彛璁＄畻锛堝け璐ョ巼銆佽繛缁け璐ワ級
2. 鐘舵€佽浆鎹㈤€昏緫锛坅ctive 鈫?shadow 鈫?disabled锛?3. 鍗﹁薄鏄犲皠锛坱imeout銆乸riority锛?4. 鎵归噺鍐欏洖锛堝師瀛愭搷浣滐級

浣滆€咃細灏忎節 + 鐝婄憵娴?鐗堟湰锛歷1.0
鏃ユ湡锛?026-03-08
"""

import json
import tempfile
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta

# 瀵煎叆琚祴妯″潡
import sys
sys.path.insert(0, str(Path(__file__).parent))
from agent_lifecycle_engine import (
    calculate_failure_rate,
    calculate_failure_streak,
    determine_lifecycle_state,
    calculate_lifecycle_score,
    FAILURE_THRESHOLD,
)

# ============================================================================
# 娴嬭瘯鏁版嵁
# ============================================================================

def create_test_executions(pattern: str) -> deque:
    """
    鍒涘缓娴嬭瘯鎵ц璁板綍
    
    Args:
        pattern: 鎴愬姛/澶辫触妯″紡锛圫=鎴愬姛锛孎=澶辫触锛?                 渚嬪锛?SSSSSFFFFF" = 鍓?娆℃垚鍔燂紝鍚?娆″け璐?    
    Returns:
        deque: 鎵ц璁板綍闃熷垪
    """
    executions = deque(maxlen=10)
    for i, char in enumerate(pattern):
        executions.append({
            "success": char == "S",
            "timestamp": (datetime.now() - timedelta(hours=10-i)).isoformat(),
            "error_type": "timeout" if char == "F" else None,
        })
    return executions


# ============================================================================
# 娴嬭瘯鐢ㄤ緥
# ============================================================================

def test_failure_rate():
    """娴嬭瘯澶辫触鐜囪绠?""
    print("\n[TEST] 澶辫触鐜囪绠?)
    
    # Case 1: 鍏ㄩ儴鎴愬姛
    executions = create_test_executions("SSSSSSSSSS")
    rate = calculate_failure_rate(executions)
    assert rate == 0.0, f"Expected 0.0, got {rate}"
    print(f"  鉁?鍏ㄩ儴鎴愬姛: {rate:.1%}")
    
    # Case 2: 鍏ㄩ儴澶辫触
    executions = create_test_executions("FFFFFFFFFF")
    rate = calculate_failure_rate(executions)
    assert rate == 1.0, f"Expected 1.0, got {rate}"
    print(f"  鉁?鍏ㄩ儴澶辫触: {rate:.1%}")
    
    # Case 3: 70% 澶辫触锛堣Е鍙戦槇鍊硷級
    executions = create_test_executions("SSSFFFFFFF")
    rate = calculate_failure_rate(executions)
    assert rate == 0.7, f"Expected 0.7, got {rate}"
    print(f"  鉁?70% 澶辫触: {rate:.1%}")
    
    # Case 4: 绌洪槦鍒?    executions = deque(maxlen=10)
    rate = calculate_failure_rate(executions)
    assert rate == 0.0, f"Expected 0.0, got {rate}"
    print(f"  鉁?绌洪槦鍒? {rate:.1%}")


def test_failure_streak():
    """娴嬭瘯杩炵画澶辫触娆℃暟"""
    print("\n[TEST] 杩炵画澶辫触娆℃暟")
    
    # Case 1: 杩炵画 5 娆″け璐?    executions = create_test_executions("SSSSSFFFFF")
    streak = calculate_failure_streak(executions)
    assert streak == 5, f"Expected 5, got {streak}"
    print(f"  鉁?杩炵画 5 娆″け璐? {streak}")
    
    # Case 2: 鏈€杩戜竴娆℃垚鍔燂紙杩炵画澶辫触涓柇锛?    executions = create_test_executions("FFFFFFFSSS")
    streak = calculate_failure_streak(executions)
    assert streak == 0, f"Expected 0, got {streak}"
    print(f"  鉁?鏈€杩戜竴娆℃垚鍔? {streak}")
    
    # Case 3: 鍏ㄩ儴澶辫触
    executions = create_test_executions("FFFFFFFFFF")
    streak = calculate_failure_streak(executions)
    assert streak == 10, f"Expected 10, got {streak}"
    print(f"  鉁?鍏ㄩ儴澶辫触: {streak}")
    
    # Case 4: 绌洪槦鍒?    executions = deque(maxlen=10)
    streak = calculate_failure_streak(executions)
    assert streak == 0, f"Expected 0, got {streak}"
    print(f"  鉁?绌洪槦鍒? {streak}")


def test_state_transitions():
    """娴嬭瘯鐘舵€佽浆鎹㈤€昏緫"""
    print("\n[TEST] 鐘舵€佽浆鎹㈤€昏緫")
    
    # Case 1: active 鈫?shadow锛堝け璐ョ巼瑙﹀彂锛?    new_state, cooldown = determine_lifecycle_state(
        current_state="active",
        failure_rate=0.7,
        failure_streak=3,
        cooldown_until=None,
    )
    assert new_state == "shadow", f"Expected shadow, got {new_state}"
    assert cooldown is not None, "Expected cooldown timestamp"
    print(f"  鉁?active 鈫?shadow锛堝け璐ョ巼 70%锛?)
    
    # Case 2: active 鈫?shadow锛堣繛缁け璐ヨЕ鍙戯級
    new_state, cooldown = determine_lifecycle_state(
        current_state="active",
        failure_rate=0.4,
        failure_streak=5,
        cooldown_until=None,
    )
    assert new_state == "shadow", f"Expected shadow, got {new_state}"
    print(f"  鉁?active 鈫?shadow锛堣繛缁け璐?5 娆★級")
    
    # Case 3: shadow 鈫?active锛堟仮澶嶆甯革級
    past_cooldown = (datetime.now() - timedelta(hours=1)).isoformat()
    new_state, cooldown = determine_lifecycle_state(
        current_state="shadow",
        failure_rate=0.3,
        failure_streak=0,
        cooldown_until=past_cooldown,
    )
    assert new_state == "active", f"Expected active, got {new_state}"
    print(f"  鉁?shadow 鈫?active锛堝け璐ョ巼 30%锛屽喎鍗存湡缁撴潫锛?)
    
    # Case 4: shadow 鈫?disabled锛堝喎鍗存湡缁撴潫浠嶅け璐ワ級
    new_state, cooldown = determine_lifecycle_state(
        current_state="shadow",
        failure_rate=0.8,
        failure_streak=7,
        cooldown_until=past_cooldown,
    )
    assert new_state == "disabled", f"Expected disabled, got {new_state}"
    print(f"  鉁?shadow 鈫?disabled锛堝け璐ョ巼 80%锛屽喎鍗存湡缁撴潫锛?)
    
    # Case 5: shadow 鍐峰嵈鏈熶腑锛堜繚鎸佺姸鎬侊級
    future_cooldown = (datetime.now() + timedelta(hours=12)).isoformat()
    new_state, cooldown = determine_lifecycle_state(
        current_state="shadow",
        failure_rate=0.6,
        failure_streak=4,
        cooldown_until=future_cooldown,
    )
    assert new_state == "shadow", f"Expected shadow, got {new_state}"
    assert cooldown == future_cooldown, "Cooldown should not change"
    print(f"  鉁?shadow 鍐峰嵈鏈熶腑锛堜繚鎸佺姸鎬侊級")
    
    # Case 6: disabled 姘镐箙绂佺敤锛堥渶瑕佷汉宸ュ共棰勶級
    new_state, cooldown = determine_lifecycle_state(
        current_state="disabled",
        failure_rate=0.9,
        failure_streak=10,
        cooldown_until=None,
    )
    assert new_state == "disabled", f"Expected disabled, got {new_state}"
    print(f"  鉁?disabled 姘镐箙绂佺敤锛堥渶瑕佷汉宸ュ共棰勶級")


def test_hexagram_mapping():
    """娴嬭瘯鍗﹁薄鏄犲皠"""
    print("\n[TEST] 鍗﹁薄鏄犲皠")
    
    # 妯℃嫙 Agent 鏁版嵁
    test_agent = {
        "id": "test-agent",
        "lifecycle_state": "active",
        "cooldown_until": None,
    }
    
    # 鍒涘缓娴嬭瘯鎵ц璁板綍锛?0% 澶辫触锛?    import tempfile
    import os
    
    # 涓存椂鏂囦欢
    temp_dir = tempfile.mkdtemp()
    temp_executions = Path(temp_dir) / "task_executions_v2.jsonl"
    
    # 鍐欏叆娴嬭瘯鏁版嵁
    with open(temp_executions, "w", encoding="utf-8") as f:
        for i in range(10):
            record = {
                "agent_id": "test-agent",
                "success": i < 3,  # 鍓?3 娆℃垚鍔燂紝鍚?7 娆″け璐?                "timestamp": (datetime.now() - timedelta(hours=10-i)).isoformat(),
                "error_type": "timeout" if i >= 3 else None,
            }
            f.write(json.dumps(record) + "\n")
    
    # 涓存椂鏇挎崲鏂囦欢璺緞
    import agent_lifecycle_engine
    original_path = agent_lifecycle_engine.TASK_EXECUTIONS_JSONL
    agent_lifecycle_engine.TASK_EXECUTIONS_JSONL = temp_executions
    
    try:
        # 璁＄畻鐢熷懡鍛ㄦ湡鐘舵€?        score = calculate_lifecycle_score(test_agent)
        
        # 楠岃瘉鐘舵€佽浆鎹?        assert score["lifecycle_state"] == "shadow", f"Expected shadow, got {score['lifecycle_state']}"
        assert score["timeout"] == 120, f"Expected 120s, got {score['timeout']}"
        assert score["priority"] == "low", f"Expected low, got {score['priority']}"
        assert score["last_failure_rate"] == 0.7, f"Expected 0.7, got {score['last_failure_rate']}"
        
        print(f"  鉁?涔惧崷 鈫?鍧ゅ崷")
        print(f"    - 澶辫触鐜? {score['last_failure_rate']:.1%}")
        print(f"    - 瓒呮椂: {score['timeout']}s锛堝欢闀匡級")
        print(f"    - 浼樺厛绾? {score['priority']}锛堥檷浣庯級")
        print(f"    - 鍐峰嵈鏈? {score['cooldown_until'][:19]}锛?4灏忔椂锛?)
    
    finally:
        # 鎭㈠鍘熻矾寰?        agent_lifecycle_engine.TASK_EXECUTIONS_JSONL = original_path
        # 娓呯悊涓存椂鏂囦欢
        os.remove(temp_executions)
        os.rmdir(temp_dir)


# ============================================================================
# 涓诲叆鍙?# ============================================================================

def run_all_tests():
    """杩愯鎵€鏈夋祴璇?""
    print("馃И Agent Lifecycle Engine 娴嬭瘯濂椾欢")
    print("=" * 60)
    
    try:
        test_failure_rate()
        test_failure_streak()
        test_state_transitions()
        test_hexagram_mapping()
        
        print("\n" + "=" * 60)
        print("鉁?鎵€鏈夋祴璇曢€氳繃锛?)
        return True
    
    except AssertionError as e:
        print(f"\n鉂?娴嬭瘯澶辫触: {e}")
        return False
    
    except Exception as e:
        print(f"\n鉂?娴嬭瘯寮傚父: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

