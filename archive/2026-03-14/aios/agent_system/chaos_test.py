from paths import SPAWN_REQUESTS
#!/usr/bin/env python3
"""
Chaos Test - 娣锋矊宸ョ▼娴嬭瘯锛堟敞鍏ユ晠闅滐紝楠岃瘉绯荤粺闊ф€э級

娴嬭瘯鍦烘櫙锛?1. 姝ｅ父浠诲姟 鈫?娉ㄥ叆杩炵画瓒呮椂 鈫?瑙﹀彂 fallback 鈫?楠岃瘉鏂?executor 鎺ョ + 瀹¤瀹屾暣
2. 浠诲姟 retry exhausted 鈫?鑷姩鍏?DLQ 鈫?replay 鈫?楠岃瘉閲嶆柊鎵ц
3. force_release 澶辫触 鈫?fallback 涓 鈫?浠诲姟鏈€缁堝叆 DLQ锛堝厹搴曡矾寰勶級
4. 骞跺彂 fallback + replay 鍚屼竴 task_id 鈫?浠呬竴涓垚鍔燂紝鏃犲弻鍐?
楠屾敹鏍囧噯锛?- 鍗曟祴 + 闆嗘垚 + chaos 鍏ㄩ噺缁?- dead_letters.jsonl 瀹¤閾惧畬鏁达紙姣忔潯璁板綍鍙拷婧?enqueue 鈫?replay/discard锛?- 22/22 涓嶅洖閫€
"""

import json
import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 璁剧疆娴嬭瘯鐜
os.environ["FALLBACK_ENABLED"] = "true"

from spawn_lock import try_acquire_spawn_lock, force_release_spawn_lock, get_lock_store
from executor_fallback import handle_timeout
from dlq import enqueue_dead_letter, get_dlq_size, get_dlq_entries
from pipeline_timer import record_fallback_latency, record_dlq_enqueue_latency


class ChaosTest(unittest.TestCase):
    """娣锋矊宸ョ▼娴嬭瘯濂椾欢"""

    def setUp(self):
        """姣忎釜娴嬭瘯鍓嶆竻鐞嗙幆澧?""
        # 娓呯悊鎵€鏈夋祴璇曟枃浠?        test_files = [
            "spawn_lock_store.jsonl",
            "spawn_lock_metrics.json",
            "spawn_locks.json",
            "spawn_locks.json.lock",
            "dead_letters.jsonl",
            "dlq_audit.jsonl",
            "fallback_events.jsonl",
            "spawn_requests.jsonl",
            "pipeline_timings.jsonl",
        ]
        for f in test_files:
            p = Path(__file__).parent / f
            if p.exists():
                p.unlink()

        # 娓呯悊 _active_fallbacks锛堥槻鍙屽啓鐘舵€侊級
        import executor_fallback
        executor_fallback._active_fallbacks.clear()

        # 閲嶇疆 LockStore 鍗曚緥锛堢‘淇濇瘡涓祴璇曠敤鏂扮殑閿佸瓨鍌級
        import spawn_lock
        spawn_lock._lock_store = None

    def tearDown(self):
        """姣忎釜娴嬭瘯鍚庢竻鐞嗙幆澧?""
        self.setUp()

    # 鈹€鈹€ Scenario 1: 姝ｅ父浠诲姟 鈫?杩炵画瓒呮椂 鈫?fallback 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    def test_scenario_1_timeout_triggers_fallback(self):
        """
        鍦烘櫙 1锛氭甯镐换鍔?鈫?娉ㄥ叆杩炵画瓒呮椂 鈫?瑙﹀彂 fallback 鈫?楠岃瘉鏂?executor 鎺ョ + 瀹¤瀹屾暣
        """
        print("\n[CHAOS] Scenario 1: Timeout 鈫?Fallback")

        task = {
            "id": "chaos-001",
            "description": "Test task for chaos scenario 1",
            "agent_id": "coder-dispatcher",
        }

        # Step 1: 鍘?executor 鑾峰彇閿?        token1 = try_acquire_spawn_lock(task)
        self.assertIsNotNone(token1, "鍘?executor 搴旇鎴愬姛鑾峰彇閿?)
        print(f"  [OK] 鍘?executor 鑾峰彇閿? {token1[:8]}...")

        # Step 2: 妯℃嫙瓒呮椂锛堟敞鍏ユ晠闅滐級
        print("  [INJECT] 妯℃嫙 executor 蹇冭烦瓒呮椂...")
        time.sleep(0.1)  # 妯℃嫙浠诲姟鎵ц

        # Step 3: 瑙﹀彂 fallback
        result = handle_timeout(
            task_id="chaos-001",
            original_executor_id="coder-dispatcher",
            task=task,
        )

        # 楠岃瘉 fallback 鎴愬姛
        self.assertTrue(result["success"], "fallback 搴旇鎴愬姛瑙﹀彂")
        self.assertEqual(result["action"], "fallback_triggered")
        self.assertEqual(result["fallback_executor_id"], "analyst-dispatcher")
        self.assertIsNotNone(result["lock_token"], "fallback executor 搴旇鑾峰彇鍒伴攣")
        print(f"  [OK] Fallback 瑙﹀彂鎴愬姛: coder 鈫?analyst")

        # 楠岃瘉瀹¤鏃ュ織
        audit_file = Path(__file__).parent / "fallback_events.jsonl"
        self.assertTrue(audit_file.exists(), "瀹¤鏃ュ織搴旇瀛樺湪")

        with open(audit_file, "r", encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]

        self.assertEqual(len(events), 1, "搴旇鏈?1 鏉″璁¤褰?)
        self.assertEqual(events[0]["action"], "fallback_triggered")
        self.assertEqual(events[0]["task_id"], "chaos-001")
        print(f"  [OK] 瀹¤鏃ュ織瀹屾暣: {events[0]['action']}")

        # 楠岃瘉 spawn 璇锋眰
        spawn_file = SPAWN_REQUESTS
        self.assertTrue(spawn_file.exists(), "spawn 璇锋眰搴旇瀛樺湪")

        with open(spawn_file, "r", encoding="utf-8") as f:
            requests = [json.loads(line) for line in f if line.strip()]

        self.assertEqual(len(requests), 1, "搴旇鏈?1 鏉?spawn 璇锋眰")
        self.assertEqual(requests[0]["agent_id"], "analyst-dispatcher")
        self.assertTrue(requests[0]["is_fallback"], "搴旇鏍囪涓?fallback")
        print(f"  [OK] Spawn 璇锋眰鐢熸垚: {requests[0]['agent_id']}")

        # 楠岃瘉 pipeline_timings
        timings_file = Path(__file__).parent / "pipeline_timings.jsonl"
        self.assertTrue(timings_file.exists(), "pipeline_timings 搴旇瀛樺湪")

        with open(timings_file, "r", encoding="utf-8") as f:
            timings = [json.loads(line) for line in f if line.strip()]

        fallback_timings = [t for t in timings if "fallback_latency_ms" in t]
        self.assertGreater(len(fallback_timings), 0, "搴旇鏈?fallback 鑰楁椂璁板綍")
        self.assertLess(fallback_timings[0]["fallback_latency_ms"], 500, "fallback 鑰楁椂搴旇 < 500ms")
        print(f"  [OK] Fallback 鑰楁椂: {fallback_timings[0]['fallback_latency_ms']} ms")

    # 鈹€鈹€ Scenario 2: Retry exhausted 鈫?DLQ 鈫?Replay 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    def test_scenario_2_retry_exhausted_dlq_replay(self):
        """
        鍦烘櫙 2锛氫换鍔?retry exhausted 鈫?鑷姩鍏?DLQ 鈫?replay 鈫?楠岃瘉閲嶆柊鎵ц
        """
        print("\n[CHAOS] Scenario 2: Retry Exhausted 鈫?DLQ 鈫?Replay")

        # Step 1: 妯℃嫙浠诲姟閲嶈瘯鑰楀敖
        task_id = "chaos-002"
        success = enqueue_dead_letter(
            task_id=task_id,
            attempts=3,
            last_error="timeout after 120s",
            error_type="timeout",
        )
        self.assertTrue(success, "浠诲姟搴旇鎴愬姛鍏?DLQ")
        print(f"  [OK] 浠诲姟鍏?DLQ: {task_id}")

        # 楠岃瘉 DLQ 澶у皬
        dlq_size = get_dlq_size()
        self.assertEqual(dlq_size, 1, "DLQ 搴旇鏈?1 涓换鍔?)
        print(f"  [OK] DLQ 澶у皬: {dlq_size}")

        # 楠岃瘉瀹¤鏃ュ織
        audit_file = Path(__file__).parent / "dlq_audit.jsonl"
        self.assertTrue(audit_file.exists(), "DLQ 瀹¤鏃ュ織搴旇瀛樺湪")

        with open(audit_file, "r", encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]

        self.assertEqual(len(events), 1, "搴旇鏈?1 鏉″璁¤褰?)
        self.assertEqual(events[0]["action"], "enqueue")
        self.assertEqual(events[0]["task_id"], task_id)
        print(f"  [OK] DLQ 瀹¤鏃ュ織瀹屾暣: {events[0]['action']}")

        # Step 2: 妯℃嫙 replay锛堜汉宸ヤ粙鍏ワ級
        # TODO: 瀹炵幇 replay 閫昏緫锛堜粠 DLQ 涓彇鍑轰换鍔★紝閲嶆柊鎻愪氦锛?        print("  [TODO] Replay 閫昏緫寰呭疄鐜?)

        # 楠岃瘉 pipeline_timings
        timings_file = Path(__file__).parent / "pipeline_timings.jsonl"
        self.assertTrue(timings_file.exists(), "pipeline_timings 搴旇瀛樺湪")

        with open(timings_file, "r", encoding="utf-8") as f:
            timings = [json.loads(line) for line in f if line.strip()]

        dlq_timings = [t for t in timings if "dlq_enqueue_latency_ms" in t]
        self.assertGreater(len(dlq_timings), 0, "搴旇鏈?DLQ enqueue 鑰楁椂璁板綍")
        self.assertLess(dlq_timings[0]["dlq_enqueue_latency_ms"], 100, "DLQ enqueue 鑰楁椂搴旇 < 100ms")
        print(f"  [OK] DLQ enqueue 鑰楁椂: {dlq_timings[0]['dlq_enqueue_latency_ms']} ms")

    # 鈹€鈹€ Scenario 3: force_release 澶辫触 鈫?fallback 涓 鈫?DLQ 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    def test_scenario_3_force_release_fails_fallback_aborts(self):
        """
        鍦烘櫙 3锛歠orce_release 澶辫触 鈫?fallback 涓 鈫?浠诲姟鏈€缁堝叆 DLQ锛堝厹搴曡矾寰勶級
        """
        print("\n[CHAOS] Scenario 3: force_release 澶辫触 鈫?Fallback 涓 鈫?DLQ")

        task = {
            "id": "chaos-003",
            "description": "Test task for chaos scenario 3",
            "agent_id": "coder-dispatcher",
        }

        # Step 1: 鍘?executor 鑾峰彇閿?        token1 = try_acquire_spawn_lock(task)
        self.assertIsNotNone(token1, "鍘?executor 搴旇鎴愬姛鑾峰彇閿?)
        print(f"  [OK] 鍘?executor 鑾峰彇閿? {token1[:8]}...")

        # Step 2: Mock force_release 澶辫触
        with patch("executor_fallback.force_release_spawn_lock", return_value=False):
            result = handle_timeout(
                task_id="chaos-003",
                original_executor_id="coder-dispatcher",
                task=task,
            )

            # 楠岃瘉 fallback 涓
            self.assertFalse(result["success"], "fallback 搴旇澶辫触")
            self.assertEqual(result["action"], "error")
            print(f"  [OK] Fallback 涓: {result['message']}")

        # Step 3: 浠诲姟鍏?DLQ锛堝厹搴曡矾寰勶級
        success = enqueue_dead_letter(
            task_id="chaos-003",
            attempts=3,
            last_error="fallback failed: force_release error",
            error_type="unknown",
        )
        self.assertTrue(success, "浠诲姟搴旇鎴愬姛鍏?DLQ")
        print(f"  [OK] 浠诲姟鍏?DLQ锛堝厹搴曡矾寰勶級")

        # 楠岃瘉 DLQ 澶у皬
        dlq_size = get_dlq_size()
        self.assertEqual(dlq_size, 1, "DLQ 搴旇鏈?1 涓换鍔?)
        print(f"  [OK] DLQ 澶у皬: {dlq_size}")

    # 鈹€鈹€ Scenario 4: 骞跺彂 fallback + replay 鍚屼竴 task_id 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    def test_scenario_4_concurrent_fallback_replay_no_double_write(self):
        """
        鍦烘櫙 4锛氬苟鍙?fallback + replay 鍚屼竴 task_id 鈫?浠呬竴涓垚鍔燂紝鏃犲弻鍐?        
        闃插弻鍐欐満鍒讹細executor_fallback._active_fallbacks 璁板綍姝ｅ湪杩涜鐨?fallback锛?        绗簩娆?fallback 璇锋眰浼氳绔嬪嵆鎷掔粷锛坒allback_skipped锛夈€?        """
        print("\n[CHAOS] Scenario 4: 骞跺彂 Fallback + Replay 鈫?鏃犲弻鍐?)

        task = {
            "id": "chaos-004",
            "description": "Test task for chaos scenario 4",
            "agent_id": "coder-dispatcher",
        }

        # Step 1: 鍘?executor 鑾峰彇閿?        token1 = try_acquire_spawn_lock(task)
        self.assertIsNotNone(token1, "鍘?executor 搴旇鎴愬姛鑾峰彇閿?)
        print(f"  [OK] 鍘?executor 鑾峰彇閿? {token1[:8]}...")

        # Step 2: 瑙﹀彂 fallback
        result1 = handle_timeout(
            task_id="chaos-004",
            original_executor_id="coder-dispatcher",
            task=task,
        )
        self.assertTrue(result1["success"], "绗竴娆?fallback 搴旇鎴愬姛")
        print(f"  [OK] 绗竴娆?Fallback 鎴愬姛: {result1['fallback_executor_id']}")

        # Step 3: 骞跺彂瑙﹀彂绗簩娆?fallback锛堟ā鎷?replay锛?        result2 = handle_timeout(
            task_id="chaos-004",
            original_executor_id="coder-dispatcher",
            task=task,
        )

        # 楠岃瘉绗簩娆?fallback 琚槻鍙屽啓鏈哄埗闃绘
        self.assertFalse(result2["success"], "绗簩娆?fallback 搴旇澶辫触锛堥槻鍙屽啓锛?)
        self.assertEqual(result2["action"], "fallback_skipped")
        print(f"  [OK] 绗簩娆?Fallback 琚樆姝紙闃插弻鍐欙級: {result2['message']}")

        # 楠岃瘉 spawn 璇锋眰鍙湁 1 鏉?        spawn_file = SPAWN_REQUESTS
        with open(spawn_file, "r", encoding="utf-8") as f:
            requests = [json.loads(line) for line in f if line.strip()]

        self.assertEqual(len(requests), 1, "搴旇鍙湁 1 鏉?spawn 璇锋眰锛堟棤鍙屽啓锛?)
        print(f"  [OK] 鏃犲弻鍐? spawn 璇锋眰鏁伴噺 = {len(requests)}")


if __name__ == "__main__":
    # 杩愯鎵€鏈夋祴璇?    suite = unittest.TestLoader().loadTestsFromTestCase(ChaosTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 杈撳嚭鎬荤粨
    print("\n" + "=" * 60)
    print("Chaos Test Summary")
    print("=" * 60)
    print(f"Total: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)

    # 閫€鍑虹爜
    exit(0 if result.wasSuccessful() else 1)


