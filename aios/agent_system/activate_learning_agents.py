"""
Activate Sleeping Learning Agents

Finds Learning Agents that have never been run and activates them.

Usage:
    python activate_learning_agents.py
"""
import json
import time
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent.parent
AGENTS_FILE = AIOS_ROOT / "agent_system" / "agents.json"


def load_agents():
    """Load agents from agents.json."""
    with open(AGENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["agents"]


def find_sleeping_agents(agents):
    """Find agents that have never been run."""
    sleeping = []
    
    for agent in agents:
        # Check if agent has state field
        if "state" not in agent:
            sleeping.append(agent)
        # Or if state exists but no last_active
        elif agent.get("state", {}).get("last_active") is None:
            sleeping.append(agent)
    
    return sleeping


def activate_agent(agent):
    """
    Activate a sleeping agent by submitting a test task.
    
    For now, we'll just print what would be done.
    In production, this would call sessions_spawn or submit a task.
    """
    agent_id = agent.get("id") or agent.get("name")
    agent_type = agent.get("type", "unknown")
    goal = agent.get("goal", "No goal specified")
    
    print(f"\n[Activating] {agent_id}")
    print(f"  Type: {agent_type}")
    print(f"  Goal: {goal[:80]}...")
    
    # Determine test task based on agent type
    if "document" in agent_id.lower():
        task_desc = "Test document processing"
        task_type = "analysis"
    elif "skill" in agent_id.lower():
        task_desc = "Test skill creation"
        task_type = "code"
    elif "health" in agent_id.lower():
        task_desc = "Test health check"
        task_type = "monitor"
    else:
        task_desc = f"Test {agent_id}"
        task_type = "test"
    
    # Submit task using AIOS task submitter
    try:
        import sys
        sys.path.insert(0, str(AIOS_ROOT))
        from core.task_submitter import submit_task
        
        task_id = submit_task(
            description=task_desc,
            task_type=task_type,
            priority="normal",
            metadata={"agent_id": agent_id, "activation": True}
        )
        
        print(f"  ✓ Task submitted: {task_id}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to submit task: {e}")
        return False


def main():
    print("=" * 70)
    print("Activate Sleeping Learning Agents")
    print("=" * 70)
    
    # Load agents
    print("\n[1] Loading agents...")
    agents = load_agents()
    print(f"  Total agents: {len(agents)}")
    
    # Find sleeping agents
    print("\n[2] Finding sleeping agents...")
    sleeping = find_sleeping_agents(agents)
    print(f"  Sleeping agents: {len(sleeping)}")
    
    if not sleeping:
        print("\n✓ All agents are active!")
        return
    
    # List sleeping agents
    print("\n[3] Sleeping agents:")
    for i, agent in enumerate(sleeping, 1):
        agent_id = agent.get("id") or agent.get("name")
        agent_type = agent.get("type", "unknown")
        print(f"  {i}. {agent_id} ({agent_type})")
    
    # Activate agents
    print("\n[4] Activating agents...")
    activated_count = 0
    for agent in sleeping:
        if activate_agent(agent):
            activated_count += 1
            time.sleep(0.5)  # Small delay between submissions
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print(f"  Sleeping agents found: {len(sleeping)}")
    print(f"  Tasks submitted: {activated_count}")
    print(f"  Failed: {len(sleeping) - activated_count}")
    
    if activated_count > 0:
        print("\n✓ Activation tasks submitted!")
        print("  Run 'python aios.py heartbeat' to execute them.")
    else:
        print("\n✗ No tasks submitted.")


if __name__ == "__main__":
    main()
