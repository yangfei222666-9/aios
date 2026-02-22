import json
from pathlib import Path
p = Path(r"C:\Users\A\.openclaw\workspace\aios\data\decisions.jsonl")
for line in p.read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    d = json.loads(line)
    ts = d.get("ts", "?")[:16]
    outcome = d.get("outcome", "?")
    conf = d.get("confidence", 0)
    ctx = d.get("context", "")[:50]
    chosen = d.get("chosen", "")
    print(f"{ts} | {outcome:15s} | conf={conf:.0%} | {ctx} → {chosen}")
