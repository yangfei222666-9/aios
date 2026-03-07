import json
from datetime import datetime
from paths import EVOLUTION_SCORE

score_file = EVOLUTION_SCORE
data = json.loads(score_file.read_text('utf-8'))
old = data['score']
data['score'] = 38.8
data['last_update'] = datetime.now().isoformat()
score_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), 'utf-8')
print(f"evolution_score.json updated: {old} -> {data['score']}")
print(f"last_update: {data['last_update']}")
