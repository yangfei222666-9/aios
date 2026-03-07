from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("请在 .env 中设置 TELEGRAM_TOKEN")

BASE_DIR = Path(__file__).parent
AGENTS_FILE = BASE_DIR / "agents.json"
MEMORY_DIR = BASE_DIR / "memory"

print(f"[CONFIG] AIOS config loaded | Agents: {AGENTS_FILE} | Memory: {MEMORY_DIR}")
