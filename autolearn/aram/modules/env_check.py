# aram/modules/env_check.py - 环境检查
import sys, os, json
from pathlib import Path

ARAM_DIR = Path(r"C:\Users\A\Desktop\ARAM-Helper")
DATA_FILE = ARAM_DIR / "aram_data.json"

def env_check() -> tuple:
    """检查 ARAM 运行环境。返回 (ok: bool, detail: dict)"""
    detail = {}
    ok = True

    # Python
    detail["python"] = sys.version.split()[0]

    # ARAM data
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            total = len(data) if isinstance(data, list) else len(data)
            detail["data_file"] = str(DATA_FILE)
            detail["champions"] = total
            detail["data_size"] = DATA_FILE.stat().st_size
        except Exception as e:
            detail["data_error"] = str(e)[:100]
            ok = False
    else:
        detail["data_file"] = "NOT FOUND"
        ok = False

    # fetch script
    fetch_script = ARAM_DIR / "fetch_real_data.py"
    detail["fetch_script"] = "ok" if fetch_script.exists() else "NOT FOUND"
    if not fetch_script.exists():
        ok = False

    return ok, detail
