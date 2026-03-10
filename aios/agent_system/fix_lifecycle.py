#!/usr/bin/env python3
import re

with open("agent_lifecycle_engine.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix cooldown config block
pattern = r'# cooldown.*?observation\}'
replacement = '''# Cooldown period config (Hexagram mapping)
COOLDOWN_PERIODS = {
    "active_to_shadow": timedelta(hours=24),  # Qian -> Kun: 24h cooldown
    "shadow_to_disabled": timedelta(hours=72),  # Kun -> Kan: 72h observation
}'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open("agent_lifecycle_engine.py", "w", encoding="utf-8", newline='\n') as f:
    f.write(content)

print("Fixed agent_lifecycle_engine.py")
