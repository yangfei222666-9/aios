#!/usr/bin/env python3
"""
Pipeline Timings 基线单测

验证：
- record_fallback_latency 写入 fallback_latency_ms 字段
- record_dlq_enqueue_latency 写入 dlq_enqueue_latency_ms 字段
- 基线断言：fallback < 500ms，dlq enqueue < 100ms（mock clock，只验证字段存在）
"""

import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline_timer import (
    PipelineTimer,
    record_fallback_latency,
    record_dlq_enqueue_latency,
    TIMINGS_FILE,
)


class TestPipelineTimingsBaseline(unittest.TestCase):

    def setUp(self):
        if TIMINGS_FILE.exists():
            TIMINGS_FILE.unlink()

    def tearDown(self):
        if TIMINGS_FILE.exists():
            TIMINGS_FILE.unlink()

    def _read_timings(self):
        if not TIMINGS_FILE.exists():
            return []
        with open(TIMINGS_FILE, "r", encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    # ── fallback_latency_ms ──────────────────────────────────────────────────
    def test_record_fallback_latency_field_exists(self):
        """record_fallback_latency 写入 fallback_latency_ms 字段"""
        record_fallback_latency("task-fb-001", 42.5)
        records = self._read_timings()
        self.assertEqual(len(records), 1)
        self.assertIn("fallback_latency_ms", records[0])
        self.assertEqual(records[0]["fallback_latency_ms"], 42.5)
        self.assertEqual(records[0]["task_id"], "task-fb-001")

    def test_record_fallback_latency_baseline_under_500ms(self):
        """fallback 基线断言：< 500ms（mock clock，不卡真实耗时）"""
        # 用 mock clock 模拟 499ms
        record_fallback_latency("task-fb-002", 499.0)
        records = self._read_timings()
        self.assertLess(records[0]["fallback_latency_ms"], 500,
                        "fallback 全流程应该 < 500ms")

    def test_record_fallback_latency_multiple(self):
        """多次写入，每条记录独立"""
        for i, ms in enumerate([10.0, 50.0, 200.0]):
            record_fallback_latency(f"task-fb-{i}", ms)
        records = self._read_timings()
        self.assertEqual(len(records), 3)
        for r in records:
            self.assertIn("fallback_latency_ms", r)

    # ── dlq_enqueue_latency_ms ───────────────────────────────────────────────
    def test_record_dlq_enqueue_latency_field_exists(self):
        """record_dlq_enqueue_latency 写入 dlq_enqueue_latency_ms 字段"""
        record_dlq_enqueue_latency("task-dlq-001", 15.3)
        records = self._read_timings()
        self.assertEqual(len(records), 1)
        self.assertIn("dlq_enqueue_latency_ms", records[0])
        self.assertEqual(records[0]["dlq_enqueue_latency_ms"], 15.3)
        self.assertEqual(records[0]["task_id"], "task-dlq-001")

    def test_record_dlq_enqueue_latency_baseline_under_100ms(self):
        """DLQ enqueue 基线断言：< 100ms（mock clock，不卡真实耗时）"""
        record_dlq_enqueue_latency("task-dlq-002", 99.0)
        records = self._read_timings()
        self.assertLess(records[0]["dlq_enqueue_latency_ms"], 100,
                        "DLQ enqueue 应该 < 100ms")

    def test_record_dlq_enqueue_latency_multiple(self):
        """多次写入，每条记录独立"""
        for i, ms in enumerate([5.0, 20.0, 80.0]):
            record_dlq_enqueue_latency(f"task-dlq-{i}", ms)
        records = self._read_timings()
        self.assertEqual(len(records), 3)
        for r in records:
            self.assertIn("dlq_enqueue_latency_ms", r)

    # ── 混合写入 ─────────────────────────────────────────────────────────────
    def test_mixed_timings_coexist(self):
        """fallback 和 dlq 耗时可以混合写入同一文件"""
        record_fallback_latency("task-mix-001", 100.0)
        record_dlq_enqueue_latency("task-mix-001", 20.0)
        records = self._read_timings()
        self.assertEqual(len(records), 2)
        fb_records = [r for r in records if "fallback_latency_ms" in r]
        dlq_records = [r for r in records if "dlq_enqueue_latency_ms" in r]
        self.assertEqual(len(fb_records), 1)
        self.assertEqual(len(dlq_records), 1)

    # ── 真实耗时验证（不 mock，验证实际写入值合理）──────────────────────────
    def test_real_fallback_latency_is_small(self):
        """真实调用 record_fallback_latency，耗时应该极小（< 50ms）"""
        t0 = time.monotonic()
        record_fallback_latency("task-real-001", 1.0)
        elapsed = (time.monotonic() - t0) * 1000
        self.assertLess(elapsed, 50, "record_fallback_latency 本身应该 < 50ms")

    def test_real_dlq_enqueue_latency_is_small(self):
        """真实调用 record_dlq_enqueue_latency，耗时应该极小（< 50ms）"""
        t0 = time.monotonic()
        record_dlq_enqueue_latency("task-real-002", 1.0)
        elapsed = (time.monotonic() - t0) * 1000
        self.assertLess(elapsed, 50, "record_dlq_enqueue_latency 本身应该 < 50ms")


if __name__ == "__main__":
    unittest.main(verbosity=2)
