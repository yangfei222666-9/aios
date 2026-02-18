# aios/scripts/config_loader.py - 加载 config.yaml，解析路径
import os, json
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = AIOS_ROOT / "config.yaml"

_cache = {}

def _expand(s: str) -> str:
    """展开 %USERPROFILE% 等环境变量"""
    return os.path.expandvars(s)

def load() -> dict:
    if "cfg" in _cache:
        return _cache["cfg"]
    
    # 简单 yaml 解析（不依赖 pyyaml）
    cfg = {"paths": {}, "policy": {}, "analysis": {}}
    
    if not CONFIG_FILE.exists():
        return cfg
    
    current_section = None
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        
        # 顶级 section
        if not line.startswith(" ") and stripped.endswith(":") and ":" == stripped[-1]:
            current_section = stripped[:-1]
            if current_section not in cfg:
                cfg[current_section] = {}
            continue
        
        # key: value
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            
            if current_section and current_section in cfg:
                # 类型转换
                if val.lower() == "true": val = True
                elif val.lower() == "false": val = False
                else:
                    try: val = float(val) if "." in str(val) else int(val)
                    except (ValueError, TypeError): pass
                
                cfg[current_section][key] = val
    
    _cache["cfg"] = cfg
    return cfg


def get_path(name: str) -> Path:
    """获取配置中的路径，自动展开环境变量"""
    cfg = load()
    raw = cfg.get("paths", {}).get(name, "")
    if not raw:
        return Path("")
    return Path(_expand(raw))


def get_policy(name: str, default=None):
    cfg = load()
    return cfg.get("policy", {}).get(name, default)


def get_analysis(name: str, default=None):
    cfg = load()
    return cfg.get("analysis", {}).get(name, default)


if __name__ == "__main__":
    cfg = load()
    print(json.dumps({k: str(v) if isinstance(v, Path) else v for k, v in cfg.items()}, 
                     ensure_ascii=False, indent=2))
    print(f"\nevents: {get_path('events')}")
    print(f"alias: {get_path('alias')}")
    print(f"min_confidence: {get_policy('alias_min_confidence')}")
    print(f"no_overwrite: {get_policy('alias_no_overwrite')}")
