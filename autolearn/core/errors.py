# core/errors.py - 错误签名生成 (v1.0 稳定 API)
import hashlib, re
from core.version import MODULE_VERSION, SCHEMA_VERSION

def normalize_error(msg: str) -> str:
    msg = (msg or "").strip().lower()
    msg = re.sub(r"\s+", " ", msg)
    msg = re.sub(r"[0-9a-f]{8,}", "<hex>", msg)
    msg = re.sub(r"\d{4,}", "<num>", msg)
    msg = re.sub(r"pid \d+", "pid <n>", msg)
    msg = re.sub(r"port \d+", "port <n>", msg)
    return msg[:220]

def _extract_keywords(msg: str) -> list:
    msg = normalize_error(msg)
    noise = {"the", "a", "an", "is", "was", "not", "for", "to", "in", "of", "at", "by", "on", "with", "from"}
    return sorted(set(w for w in re.findall(r"[a-z_]{3,}", msg) if w not in noise))[:15]

# === v1.0 STABLE API ===

def sign_strict(exc_type: str, msg: str) -> str:
    """严格签名：exc_type + normalized msg → 12 char hex"""
    raw = f"{exc_type}:{normalize_error(msg)}"
    return hashlib.sha1(raw.encode("utf-8", errors="replace")).hexdigest()[:12]

def sign_loose(msg: str) -> dict:
    """宽松签名：关键词集合 → {keywords, sig}"""
    keywords = _extract_keywords(msg)
    raw = " ".join(keywords)
    sig = hashlib.sha1(raw.encode("utf-8", errors="replace")).hexdigest()[:12]
    return {"keywords": keywords, "sig": sig}

# === BACKWARD COMPAT (deprecated, use sign_strict/sign_loose) ===
error_sig = sign_strict
def error_sig_loose(msg: str) -> str:
    return sign_loose(msg)["sig"]
