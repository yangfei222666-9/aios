import json, pathlib

p = pathlib.Path(r"C:\Users\A\.openclaw\workspace\aios\data\alert_fsm.json")
data = json.loads(p.read_text(encoding="utf-8"))

for aid, alert in data.items():
    state = alert.get("state", "?")
    severity = alert.get("severity", "?")
    summary = alert.get("summary", "")[:100]
    sla = alert.get("sla_breached", False)
    created = alert.get("created_at", "?")
    sig = alert.get("signature", "?")
    print(f"[{aid}]")
    print(f"  state={state}  severity={severity}  sla_breached={sla}")
    print(f"  created={created}")
    print(f"  signature={sig}")
    print(f"  summary={summary}")
    print()
