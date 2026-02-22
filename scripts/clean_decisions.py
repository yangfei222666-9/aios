import json
from pathlib import Path

p = Path(r"C:\Users\A\.openclaw\workspace\aios\data\decisions.jsonl")
lines = p.read_text(encoding="utf-8").splitlines()

cleaned = []
for line in lines:
    if not line.strip():
        continue
    d = json.loads(line)
    ctx = d.get("context", "")
    # 保留 reactor 产生的真实决策，清理早期测试数据
    if "reactor:" in ctx:
        cleaned.append(line)

p.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
print(f"清理完成: {len(lines)} → {len(cleaned)} 条")
