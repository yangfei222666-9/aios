#!/usr/bin/env python3
"""
Agent Lifecycle Engine - Core Module

This module implements the Agent Lifecycle Management system based on the
Hexagram Three-State Model (Active → Shadow → Disabled).

The lifecycle engine:
1. Monitors agent execution history from task_executions_v2.jsonl
2. Calculates failure rates and streaks
3. Transitions agents between states based on performance
4. Enforces cooldown periods to prevent state oscillation
5. Manages routing availability based on lifecycle state

State Transitions:
    Active → Shadow: When failure_rate ≥ 0.7 OR failure_streak ≥ 5
    Shadow → Disabled: When failure_rate ≥ 0.7 (after cooldown)
    Shadow → Active: When failure_rate < 0.5 (recovery)
    Disabled → (manual recovery only)

Cooldown Periods:
    Active → Shadow: 24 hours
    Shadow → Disabled: 72 hours

Author: AIOS Team
License: MIT
"""

import json
import logging
import sys
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path setup
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

try:
    from paths import TASK_EXECUTIONS, AGENTS_STATE
except ImportError as e:
    logger.error(f"Failed to import paths module: {e}")
    raise

# ============================================================================
# Configuration Constants
# ============================================================================

# Sliding window size for execution history
WINDOW_SIZE: int = 10

# Failure rate threshold for state transitions
FAILURE_THRESHOLD: float = 0.7

# Recovery threshold (shadow → active)
RECOVERY_THRESHOLD: float = 0.5

# Consecutive failure streak threshold
FAILURE_STREAK_THRESHOLD: int = 5

# Cooldown periods for state transitions（已缩短）
COOLDOWN_PERIODS: Dict[str, timedelta] = {
    "active_to_shadow": timedelta(hours=6),  # 24 → 6
    "shadow_to_disabled": timedelta(hours=24),  # 72 → 24
}

# Timeout configuration per state (seconds)
TIMEOUT_MAP: Dict[str, int] = {
    "active": 60,
    "shadow": 120,
    "disabled": 0,
}

# Priority configuration per state
PRIORITY_MAP: Dict[str, str] = {
    "active": "normal",
    "shadow": "low",
    "disabled": "none",
}


# ============================================================================
# Core Functions
# ============================================================================

def load_recent_executions(
    agent_id: str,
    window_size: int = WINDOW_SIZE
) -> deque:
    """
    Load recent execution records for a specific agent.

    Reads from task_executions_v2.jsonl and returns the most recent N executions
    for the given agent, where N = window_size.

    Args:
        agent_id: Unique identifier of the agent
        window_size: Maximum number of recent executions to load (default: 10)

    Returns:
        deque: A deque containing execution records with 'success' and 'timestamp' fields.
               Returns empty deque if file doesn't exist or no records found.

    Example:
        >>> executions = load_recent_executions("data-collector", window_size=5)
        >>> len(executions)
        5
    """
    executions = deque(maxlen=window_size)

    if not TASK_EXECUTIONS.exists():
        logger.warning(f"Task executions file not found: {TASK_EXECUTIONS}")
        return executions

    try:
        with open(TASK_EXECUTIONS, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line.strip())
                    if record.get('agent_id') == agent_id:
                        executions.append({
                            'success': record.get('status') == 'completed',
                            'timestamp': record.get('completed_at') or record.get('created_at'),
                        })
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    continue

    except IOError as e:
        logger.error(f"Failed to read task executions file: {e}")
        return deque(maxlen=window_size)

    logger.debug(f"Loaded {len(executions)} executions for agent '{agent_id}'")
    return executions


def calculate_failure_rate(executions: deque) -> float:
    """
    Calculate the failure rate from recent executions.

    Args:
        executions: Deque of execution records with 'success' field

    Returns:
        float: Failure rate between 0.0 and 1.0
               Returns 0.0 if no executions available

    Example:
        >>> execs = deque([{'success': True}, {'success': False}, {'success': False}])
        >>> calculate_failure_rate(execs)
        0.6666666666666666
    """
    if not executions:
        return 0.0

    failed = sum(1 for e in executions if not e['success'])
    return failed / len(executions)


def calculate_failure_streak(executions: deque) -> int:
    """
    Calculate the consecutive failure streak from most recent executions.

    Counts failures from the most recent execution backwards until a success is found.

    Args:
        executions: Deque of execution records with 'success' field

    Returns:
        int: Number of consecutive failures (0 if last execution was successful)

    Example:
        >>> execs = deque([
        ...     {'success': True},
        ...     {'success': False},
        ...     {'success': False},
        ...     {'success': False}
        ... ])
        >>> calculate_failure_streak(execs)
        3
    """
    if not executions:
        return 0

    streak = 0
    for e in reversed(executions):
        if not e['success']:
            streak += 1
        else:
            break

    return streak


def determine_lifecycle_state(
    current_state: str,
    failure_rate: float,
    failure_streak: int,
    cooldown_until: Optional[str],
) -> Tuple[str, Optional[str]]:
    """
    Determine the next lifecycle state based on failure metrics.

    Implements the Hexagram Three-State transition logic with cooldown enforcement.

    State Transition Rules:
        Active:
            - If failure_rate ≥ FAILURE_THRESHOLD OR failure_streak ≥ 5 → Shadow (24h cooldown)
            - Otherwise → Active

        Shadow:
            - If in cooldown → Shadow (maintain)
            - If failure_rate ≥ FAILURE_THRESHOLD → Disabled (72h cooldown)
            - If failure_rate < RECOVERY_THRESHOLD → Active (recovery)
            - Otherwise → Shadow

        Disabled:
            - Remains disabled (manual recovery only)

    Args:
        current_state: Current lifecycle state ("active", "shadow", or "disabled")
        failure_rate: Current failure rate (0.0 to 1.0)
        failure_streak: Number of consecutive failures
        cooldown_until: ISO format timestamp of cooldown end (or None)

    Returns:
        Tuple[str, Optional[str]]: (new_state, new_cooldown_until)

    Example:
        >>> determine_lifecycle_state("active", 0.8, 3, None)
        ('shadow', '2026-03-14T10:00:00')
    """
    now = datetime.now()
    in_cooldown = False

    # Check if currently in cooldown period
    if cooldown_until:
        try:
            cooldown_end = datetime.fromisoformat(cooldown_until)
            in_cooldown = now < cooldown_end
        except ValueError as e:
            logger.warning(f"Invalid cooldown timestamp '{cooldown_until}': {e}")

    # State transition logic
    if current_state == "active":
        if failure_rate >= FAILURE_THRESHOLD or failure_streak >= FAILURE_STREAK_THRESHOLD:
            new_cooldown = (now + COOLDOWN_PERIODS["active_to_shadow"]).isoformat()
            logger.info(
                f"Transitioning active → shadow "
                f"(failure_rate={failure_rate:.2f}, streak={failure_streak})"
            )
            return "shadow", new_cooldown
        return "active", None

    elif current_state == "shadow":
        if in_cooldown:
            logger.debug(f"Shadow state in cooldown until {cooldown_until}")
            return "shadow", cooldown_until

        if failure_rate >= FAILURE_THRESHOLD:
            new_cooldown = (now + COOLDOWN_PERIODS["shadow_to_disabled"]).isoformat()
            logger.warning(
                f"Transitioning shadow → disabled (failure_rate={failure_rate:.2f})"
            )
            return "disabled", new_cooldown
        elif failure_rate < RECOVERY_THRESHOLD:
            logger.info(f"Recovering shadow → active (failure_rate={failure_rate:.2f})")
            return "active", None
        else:
            return "shadow", None

    elif current_state == "disabled":
        logger.debug("Agent in disabled state (manual recovery required)")
        return "disabled", cooldown_until

    # Fallback for unknown states
    logger.warning(f"Unknown lifecycle state '{current_state}', defaulting to current")
    return current_state, cooldown_until


def calculate_lifecycle_score(
    agent_id: str,
    current_state: str,
    cooldown_until: Optional[str],
    enabled: bool = True,
    mode: str = "active"
) -> Dict:
    """
    Calculate comprehensive lifecycle score for a single agent.

    This function combines execution history analysis with availability gates
    to determine the agent's routing eligibility and lifecycle state.

    Availability Gates:
        - enabled=False → Not routable, forced to shadow/disabled
        - mode="shadow" → Not routable, forced to shadow
        - mode="disabled" → Not routable, forced to disabled

    Args:
        agent_id: Unique identifier of the agent
        current_state: Current lifecycle state
        cooldown_until: ISO timestamp of cooldown end (or None)
        enabled: Whether agent is enabled (availability gate)
        mode: Agent mode ("active", "shadow", or "disabled")

    Returns:
        dict: Lifecycle score containing:
            - lifecycle_state: Computed state
            - last_failure_rate: Recent failure rate
            - last_failure_streak: Consecutive failures
            - cooldown_until: Cooldown end timestamp
            - timeout: Execution timeout in seconds
            - priority: Routing priority
            - window_size: Number of executions analyzed
            - routable: Whether agent can receive tasks
            - availability_gate: Gate status ("passed" or "blocked_by_enabled_or_mode")

    Example:
        >>> score = calculate_lifecycle_score("data-collector", "active", None, True, "active")
        >>> score['routable']
        True
    """
    # ── Availability Gate ──────────────────────────────────────────────
    # Agents that are disabled or in shadow mode are not routable
    if not enabled or mode in ("shadow", "disabled"):
        forced_state = "disabled" if mode == "disabled" else "shadow"
        logger.info(
            f"Agent '{agent_id}' blocked by availability gate "
            f"(enabled={enabled}, mode={mode})"
        )
        return {
            "lifecycle_state": forced_state,
            "last_failure_rate": 0.0,
            "last_failure_streak": 0,
            "cooldown_until": cooldown_until,
            "timeout": TIMEOUT_MAP[forced_state],
            "priority": PRIORITY_MAP[forced_state],
            "window_size": 0,
            "routable": False,
            "availability_gate": "blocked_by_enabled_or_mode",
        }

    # ── Normal Lifecycle Calculation ──────────────────────────────────
    executions = load_recent_executions(agent_id, WINDOW_SIZE)

    failure_rate = calculate_failure_rate(executions)
    failure_streak = calculate_failure_streak(executions)

    new_state, new_cooldown = determine_lifecycle_state(
        current_state, failure_rate, failure_streak, cooldown_until
    )

    timeout = TIMEOUT_MAP[new_state]
    priority = PRIORITY_MAP[new_state]

    return {
        "lifecycle_state": new_state,
        "last_failure_rate": failure_rate,
        "last_failure_streak": failure_streak,
        "cooldown_until": new_cooldown,
        "timeout": timeout,
        "priority": priority,
        "window_size": len(executions),
        "routable": new_state == "active",
        "availability_gate": "passed",
    }


def calculate_all_lifecycle_scores() -> Dict[str, Dict]:
    """
    Calculate lifecycle scores for all registered agents.

    Reads agent configuration from agents.json and computes lifecycle scores
    for each agent based on their execution history.

    Returns:
        dict: Mapping of agent_id to lifecycle score dict
              Returns empty dict if agents.json doesn't exist

    Raises:
        json.JSONDecodeError: If agents.json is malformed
        IOError: If agents.json cannot be read
    """
    if not AGENTS_STATE.exists():
        logger.warning(f"Agents state file not found: {AGENTS_STATE}")
        return {}

    try:
        with open(AGENTS_STATE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse agents.json: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to read agents.json: {e}")
        raise

    agents = data.get('agents', [])
    scores = {}

    for agent in agents:
        agent_id = agent.get('id') or agent.get('name')
        if not agent_id:
            logger.warning("Skipping agent with missing id/name")
            continue

        current_state = agent.get('lifecycle_state', 'active')
        cooldown_until = agent.get('cooldown_until')
        enabled = agent.get('enabled', True)
        mode = agent.get('mode', 'active')

        try:
            scores[agent_id] = calculate_lifecycle_score(
                agent_id, current_state, cooldown_until, enabled, mode
            )
        except Exception as e:
            logger.error(f"Failed to calculate score for agent '{agent_id}': {e}")
            continue

    logger.info(f"Calculated lifecycle scores for {len(scores)} agents")
    return scores


def write_lifecycle_states(scores: Dict[str, Dict]) -> int:
    """
    Write computed lifecycle states back to agents.json.

    Updates the agents.json file with new lifecycle states, cooldowns,
    timeouts, priorities, and routing flags.

    Args:
        scores: Mapping of agent_id to lifecycle score dict

    Returns:
        int: Number of agents successfully updated

    Raises:
        json.JSONDecodeError: If agents.json is malformed
        IOError: If agents.json cannot be read or written
    """
    if not AGENTS_STATE.exists():
        logger.error(f"Agents state file not found: {AGENTS_STATE}")
        return 0

    try:
        with open(AGENTS_STATE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse agents.json: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to read agents.json: {e}")
        raise

    agents = data.get('agents', [])
    updated = 0

    for agent in agents:
        agent_id = agent.get('id') or agent.get('name')
        if agent_id in scores:
            score = scores[agent_id]
            agent['lifecycle_state'] = score['lifecycle_state']
            agent['cooldown_until'] = score['cooldown_until']
            agent['timeout'] = score['timeout']
            agent['priority'] = score['priority']
            agent['routable'] = score.get('routable', False)
            updated += 1

    try:
        with open(AGENTS_STATE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully updated {updated} agents in {AGENTS_STATE}")
    except IOError as e:
        logger.error(f"Failed to write agents.json: {e}")
        raise

    return updated


def run_lifecycle_engine() -> Dict:
    """
    Execute the complete lifecycle engine workflow.

    This is the main entry point that:
    1. Calculates lifecycle scores for all agents
    2. Writes updated states back to agents.json
    3. Returns a summary of the operation

    Returns:
        dict: Summary containing:
            - total_agents: Number of agents processed
            - updated_agents: Number of agents updated
            - state_distribution: Count of agents per state

    Example:
        >>> result = run_lifecycle_engine()
        >>> print(result)
        {
            'total_agents': 15,
            'updated_agents': 15,
            'state_distribution': {'active': 10, 'shadow': 3, 'disabled': 2}
        }
    """
    logger.info("Starting Agent Lifecycle Engine")

    try:
        scores = calculate_all_lifecycle_scores()

        state_dist = {"active": 0, "shadow": 0, "disabled": 0}
        for score in scores.values():
            state = score['lifecycle_state']
            state_dist[state] = state_dist.get(state, 0) + 1

        updated = write_lifecycle_states(scores)

        result = {
            "total_agents": len(scores),
            "updated_agents": updated,
            "state_distribution": state_dist,
        }

        logger.info(f"Lifecycle engine completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Lifecycle engine failed: {e}")
        raise


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    print("Agent Lifecycle Engine - Hexagram Three-State System")
    print("=" * 60)

    try:
        result = run_lifecycle_engine()
        print(f"Total agents: {result['total_agents']}")
        print(f"Updated: {result['updated_agents']}")
        print(f"State distribution: {result['state_distribution']}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
