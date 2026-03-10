#!/usr/bin/env python3
"""
Rebuild determine_lifecycle_state function with correct indentation
"""

replacement = '''def determine_lifecycle_state(
    current_state: str,
    failure_rate: float,
    failure_streak: int,
    cooldown_until: Optional[str],
) -> Tuple[str, Optional[str]]:
    """
    Determine lifecycle state based on failure metrics
    
    State transition rules:
    - active -> shadow: Failure rate >= 70% or consecutive failures >= 5
    - shadow -> disabled: After cooldown, failure rate still >= 70%
    - shadow -> active: After cooldown, failure rate < 50%
    - disabled -> shadow: Manual intervention (manual reset)
    """
    now = datetime.now()
    in_cooldown = False
    
    if cooldown_until:
        try:
            cooldown_end = datetime.fromisoformat(cooldown_until)
            in_cooldown = now < cooldown_end
        except ValueError:
            pass
    
    if current_state == "active":
        if failure_rate >= FAILURE_THRESHOLD or failure_streak >= 5:
            new_cooldown = (now + COOLDOWN_PERIODS["active_to_shadow"]).isoformat()
            return "shadow", new_cooldown
        return "active", None
    
    elif current_state == "shadow":
        if in_cooldown:
            return "shadow", cooldown_until
        
        if failure_rate >= FAILURE_THRESHOLD:
            new_cooldown = (now + COOLDOWN_PERIODS["shadow_to_disabled"]).isoformat()
            return "disabled", new_cooldown
        elif failure_rate < 0.5:
            return "active", None
        else:
            return "shadow", None
    
    elif current_state == "disabled":
        return "disabled", cooldown_until
    
    return current_state, cooldown_until
'''

# Read file
with open('agent_lifecycle_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the function
import re
pattern = r'def determine_lifecycle_state\([^)]+\)[^:]+:.*?(?=\n\ndef |\nclass |\Z)'
content = re.sub(pattern, replacement.strip(), content, flags=re.DOTALL)

# Write back
with open('agent_lifecycle_engine.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("[OK] Rebuilt determine_lifecycle_state function")
