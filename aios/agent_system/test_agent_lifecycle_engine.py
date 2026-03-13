#!/usr/bin/env python3
"""
Unit tests for Agent Lifecycle Engine

Tests cover:
- Execution history loading
- Failure rate calculation
- Failure streak calculation
- State transition logic
- Availability gates
- Full lifecycle score calculation
"""

import json
import tempfile
import unittest
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import the module under test
import sys
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from agent_lifecycle_engine import (
    FAILURE_THRESHOLD,
    RECOVERY_THRESHOLD,
    FAILURE_STREAK_THRESHOLD,
    calculate_failure_rate,
    calculate_failure_streak,
    determine_lifecycle_state,
    calculate_lifecycle_score,
    load_recent_executions,
)


class TestFailureRateCalculation(unittest.TestCase):
    """Test failure rate calculation logic"""

    def test_empty_executions(self):
        """Empty execution history should return 0.0"""
        executions = deque()
        self.assertEqual(calculate_failure_rate(executions), 0.0)

    def test_all_success(self):
        """All successful executions should return 0.0"""
        executions = deque([
            {'success': True},
            {'success': True},
            {'success': True},
        ])
        self.assertEqual(calculate_failure_rate(executions), 0.0)

    def test_all_failures(self):
        """All failed executions should return 1.0"""
        executions = deque([
            {'success': False},
            {'success': False},
            {'success': False},
        ])
        self.assertEqual(calculate_failure_rate(executions), 1.0)

    def test_mixed_executions(self):
        """Mixed executions should return correct ratio"""
        executions = deque([
            {'success': True},
            {'success': False},
            {'success': False},
            {'success': True},
            {'success': False},
        ])
        # 3 failures out of 5 = 0.6
        self.assertAlmostEqual(calculate_failure_rate(executions), 0.6)


class TestFailureStreakCalculation(unittest.TestCase):
    """Test consecutive failure streak calculation"""

    def test_empty_executions(self):
        """Empty execution history should return 0"""
        executions = deque()
        self.assertEqual(calculate_failure_streak(executions), 0)

    def test_no_failures(self):
        """No failures should return 0"""
        executions = deque([
            {'success': True},
            {'success': True},
        ])
        self.assertEqual(calculate_failure_streak(executions), 0)

    def test_all_failures(self):
        """All failures should return total count"""
        executions = deque([
            {'success': False},
            {'success': False},
            {'success': False},
        ])
        self.assertEqual(calculate_failure_streak(executions), 3)

    def test_recent_failures_only(self):
        """Should count only consecutive failures from the end"""
        executions = deque([
            {'success': True},
            {'success': False},
            {'success': False},
            {'success': False},
        ])
        self.assertEqual(calculate_failure_streak(executions), 3)

    def test_interrupted_streak(self):
        """Success in the middle should reset streak"""
        executions = deque([
            {'success': False},
            {'success': False},
            {'success': True},
            {'success': False},
        ])
        self.assertEqual(calculate_failure_streak(executions), 1)


class TestLifecycleStateTransitions(unittest.TestCase):
    """Test state transition logic"""

    def test_active_to_shadow_by_rate(self):
        """Active should transition to shadow when failure rate exceeds threshold"""
        new_state, cooldown = determine_lifecycle_state(
            current_state="active",
            failure_rate=0.8,  # Above FAILURE_THRESHOLD (0.7)
            failure_streak=2,
            cooldown_until=None
        )
        self.assertEqual(new_state, "shadow")
        self.assertIsNotNone(cooldown)

    def test_active_to_shadow_by_streak(self):
        """Active should transition to shadow when failure streak exceeds threshold"""
        new_state, cooldown = determine_lifecycle_state(
            current_state="active",
            failure_rate=0.3,  # Below threshold
            failure_streak=6,  # Above FAILURE_STREAK_THRESHOLD (5)
            cooldown_until=None
        )
        self.assertEqual(new_state, "shadow")
        self.assertIsNotNone(cooldown)

    def test_active_stays_active(self):
        """Active should stay active when metrics are healthy"""
        new_state, cooldown = determine_lifecycle_state(
            current_state="active",
            failure_rate=0.3,
            failure_streak=2,
            cooldown_until=None
        )
        self.assertEqual(new_state, "active")
        self.assertIsNone(cooldown)

    def test_shadow_to_disabled(self):
        """Shadow should transition to disabled when failure rate is high"""
        new_state, cooldown = determine_lifecycle_state(
            current_state="shadow",
            failure_rate=0.8,
            failure_streak=3,
            cooldown_until=None
        )
        self.assertEqual(new_state, "disabled")
        self.assertIsNotNone(cooldown)

    def test_shadow_to_active_recovery(self):
        """Shadow should recover to active when failure rate is low"""
        new_state, cooldown = determine_lifecycle_state(
            current_state="shadow",
            failure_rate=0.3,  # Below RECOVERY_THRESHOLD (0.5)
            failure_streak=1,
            cooldown_until=None
        )
        self.assertEqual(new_state, "active")
        self.assertIsNone(cooldown)

    def test_shadow_stays_shadow(self):
        """Shadow should stay shadow when failure rate is moderate"""
        new_state, cooldown = determine_lifecycle_state(
            current_state="shadow",
            failure_rate=0.6,  # Between RECOVERY_THRESHOLD and FAILURE_THRESHOLD
            failure_streak=2,
            cooldown_until=None
        )
        self.assertEqual(new_state, "shadow")
        self.assertIsNone(cooldown)

    def test_shadow_respects_cooldown(self):
        """Shadow should stay in cooldown period"""
        future_time = (datetime.now() + timedelta(hours=12)).isoformat()
        new_state, cooldown = determine_lifecycle_state(
            current_state="shadow",
            failure_rate=0.3,  # Would normally recover
            failure_streak=0,
            cooldown_until=future_time
        )
        self.assertEqual(new_state, "shadow")
        self.assertEqual(cooldown, future_time)

    def test_disabled_stays_disabled(self):
        """Disabled should always stay disabled (manual recovery only)"""
        new_state, cooldown = determine_lifecycle_state(
            current_state="disabled",
            failure_rate=0.0,  # Perfect score
            failure_streak=0,
            cooldown_until=None
        )
        self.assertEqual(new_state, "disabled")


class TestAvailabilityGates(unittest.TestCase):
    """Test availability gate logic"""

    @patch('agent_lifecycle_engine.load_recent_executions')
    def test_disabled_agent_not_routable(self, mock_load):
        """Disabled agents should not be routable"""
        mock_load.return_value = deque()

        score = calculate_lifecycle_score(
            agent_id="test-agent",
            current_state="active",
            cooldown_until=None,
            enabled=False,  # Disabled
            mode="active"
        )

        self.assertFalse(score['routable'])
        self.assertEqual(score['availability_gate'], "blocked_by_enabled_or_mode")

    @patch('agent_lifecycle_engine.load_recent_executions')
    def test_shadow_mode_not_routable(self, mock_load):
        """Agents in shadow mode should not be routable"""
        mock_load.return_value = deque()

        score = calculate_lifecycle_score(
            agent_id="test-agent",
            current_state="active",
            cooldown_until=None,
            enabled=True,
            mode="shadow"  # Shadow mode
        )

        self.assertFalse(score['routable'])
        self.assertEqual(score['lifecycle_state'], "shadow")

    @patch('agent_lifecycle_engine.load_recent_executions')
    def test_disabled_mode_not_routable(self, mock_load):
        """Agents in disabled mode should not be routable"""
        mock_load.return_value = deque()

        score = calculate_lifecycle_score(
            agent_id="test-agent",
            current_state="active",
            cooldown_until=None,
            enabled=True,
            mode="disabled"  # Disabled mode
        )

        self.assertFalse(score['routable'])
        self.assertEqual(score['lifecycle_state'], "disabled")

    @patch('agent_lifecycle_engine.load_recent_executions')
    def test_enabled_active_agent_routable(self, mock_load):
        """Enabled active agents with good metrics should be routable"""
        # Mock successful executions
        mock_load.return_value = deque([
            {'success': True, 'timestamp': '2026-03-13T09:00:00'},
            {'success': True, 'timestamp': '2026-03-13T09:30:00'},
        ])

        score = calculate_lifecycle_score(
            agent_id="test-agent",
            current_state="active",
            cooldown_until=None,
            enabled=True,
            mode="active"
        )

        self.assertTrue(score['routable'])
        self.assertEqual(score['availability_gate'], "passed")
        self.assertEqual(score['lifecycle_state'], "active")


class TestLoadRecentExecutions(unittest.TestCase):
    """Test execution history loading from JSONL"""

    def test_load_from_nonexistent_file(self):
        """Should return empty deque when file doesn't exist"""
        with patch('agent_lifecycle_engine.TASK_EXECUTIONS', Path('/nonexistent/file.jsonl')):
            executions = load_recent_executions("test-agent")
            self.assertEqual(len(executions), 0)

    def test_load_with_valid_records(self):
        """Should correctly parse valid JSONL records"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            f.write(json.dumps({"agent_id": "test-agent", "status": "completed", "created_at": "2026-03-13T09:00:00"}) + '\n')
            f.write(json.dumps({"agent_id": "test-agent", "status": "failed", "created_at": "2026-03-13T09:30:00"}) + '\n')
            f.write(json.dumps({"agent_id": "other-agent", "status": "completed", "created_at": "2026-03-13T10:00:00"}) + '\n')
            temp_path = Path(f.name)

        try:
            with patch('agent_lifecycle_engine.TASK_EXECUTIONS', temp_path):
                executions = load_recent_executions("test-agent")
                self.assertEqual(len(executions), 2)
                self.assertTrue(executions[0]['success'])
                self.assertFalse(executions[1]['success'])
        finally:
            temp_path.unlink()

    def test_load_respects_window_size(self):
        """Should respect window_size parameter"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            for i in range(20):
                f.write(json.dumps({"agent_id": "test-agent", "status": "completed", "created_at": f"2026-03-13T{i:02d}:00:00"}) + '\n')
            temp_path = Path(f.name)

        try:
            with patch('agent_lifecycle_engine.TASK_EXECUTIONS', temp_path):
                executions = load_recent_executions("test-agent", window_size=5)
                self.assertEqual(len(executions), 5)
        finally:
            temp_path.unlink()

    def test_load_handles_malformed_json(self):
        """Should skip malformed JSON lines gracefully"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            f.write(json.dumps({"agent_id": "test-agent", "status": "completed", "created_at": "2026-03-13T09:00:00"}) + '\n')
            f.write("INVALID JSON LINE\n")
            f.write(json.dumps({"agent_id": "test-agent", "status": "failed", "created_at": "2026-03-13T09:30:00"}) + '\n')
            temp_path = Path(f.name)

        try:
            with patch('agent_lifecycle_engine.TASK_EXECUTIONS', temp_path):
                executions = load_recent_executions("test-agent")
                self.assertEqual(len(executions), 2)  # Should skip the invalid line
        finally:
            temp_path.unlink()


class TestFullLifecycleScore(unittest.TestCase):
    """Integration tests for full lifecycle score calculation"""

    @patch('agent_lifecycle_engine.load_recent_executions')
    def test_healthy_agent_score(self, mock_load):
        """Healthy agent should have active state and be routable"""
        mock_load.return_value = deque([
            {'success': True, 'timestamp': '2026-03-13T09:00:00'},
            {'success': True, 'timestamp': '2026-03-13T09:30:00'},
            {'success': True, 'timestamp': '2026-03-13T10:00:00'},
        ])

        score = calculate_lifecycle_score(
            agent_id="healthy-agent",
            current_state="active",
            cooldown_until=None,
            enabled=True,
            mode="active"
        )

        self.assertEqual(score['lifecycle_state'], "active")
        self.assertTrue(score['routable'])
        self.assertEqual(score['last_failure_rate'], 0.0)
        self.assertEqual(score['last_failure_streak'], 0)
        self.assertEqual(score['window_size'], 3)

    @patch('agent_lifecycle_engine.load_recent_executions')
    def test_failing_agent_score(self, mock_load):
        """Failing agent should transition to shadow"""
        mock_load.return_value = deque([
            {'success': False, 'timestamp': '2026-03-13T09:00:00'},
            {'success': False, 'timestamp': '2026-03-13T09:30:00'},
            {'success': False, 'timestamp': '2026-03-13T10:00:00'},
        ])

        score = calculate_lifecycle_score(
            agent_id="failing-agent",
            current_state="active",
            cooldown_until=None,
            enabled=True,
            mode="active"
        )

        self.assertEqual(score['lifecycle_state'], "shadow")
        self.assertFalse(score['routable'])
        self.assertEqual(score['last_failure_rate'], 1.0)
        self.assertEqual(score['last_failure_streak'], 3)


if __name__ == '__main__':
    unittest.main()
