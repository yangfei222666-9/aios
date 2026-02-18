#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smartlearn.py - OpenClaw 可控"自我学习"核心（纯标准库，无依赖）

自我学习（可解释、可回滚）：
1) 意图识别自学习（Naive Bayes）：你用 /f 纠正，它会把样本写入 training.jsonl，定期重训
2) 工具选择自学习（epsilon-greedy）：记录 asr 引擎（google/vosk）成功率，自动更偏向稳定的
3) 简易知识库（TF-IDF 检索 + 缓存）：/kb 查询，/kbadd 添加，kbimport 批量导入文件夹

安全性：
- 不会自改代码
- 不会执行危险系统命令（system_ops 只给"计划"，真实执行请你做白名单）
- 日志自动脱敏（避免把 key/token 写进磁盘）
"""

from __future__ import annotations

import json
import math
import random
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ====== 你可以按 OpenClaw 改这些 ======
ALLOW_INTENTS = [
    "asr_transcribe",    # 语音/录音转文字
    "tts_speak",         # 文字转语音
    "note_write",        # 记笔记/归档
    "automation_task",   # 自动化/定时
    "system_ops",        # 系统操作（建议你做白名单）
    "question_answer",   # 普通问答
]

CLARIFY_THRESHOLD = 0.55   # 低于就追问澄清
EPSILON = 0.08             # 工具探索率（越大越爱尝试）
AUTO_TRAIN_EVERY = 5       # 收集多少条纠正自动重训一次

# ====== 数据目录 ======
BASE_DIR = Path(__file__).resolve().parent / "smartlearn_data"
BASE_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE   = BASE_DIR / "training.jsonl"
MODEL_FILE   = BASE_DIR / "intent_model.json"
EVENTS_FILE  = BASE_DIR / "events.jsonl"
SESSION_FILE = BASE_DIR / "session.json"
PROFILE_FILE = BASE_DIR / "profile.json"
KB_FILE      = BASE_DIR / "kb_docs.jsonl"
TOOL_STATS   = BASE_DIR / "tool_stats.json"

# ====== 脱敏（避免 key/token 写进日志）======
SENSITIVE_PATTERNS = [
    re.compile(r"\bAIza[0-9A-Za-z\-_]{25,}\b"),
    re.compile(r"\bsk-[0-9A-Za-z]{28,}\b"),
    re.compile(r"(?i)\b(token|secret|apikey|api_key)\b\s*[:=]\s*\S+"),
]


def redact(text: str) -> str:
    if not isinstance(text, str):
        return ""
    out = text
    for p in SENSITIVE_PATTERNS:
        out = p.sub("[REDACTED]", out)
    if len(out) > 4000:
        out = out[:4000] + "...[TRUNCATED]"
    return out


def tokenize(text: str) -> List[str]:
    """中文：字 + 双字；英文：按词；再加点标点作为弱特征。"""
    text = redact(text).strip()
    if not text:
        return []
    words = re.findall(r"[A-Za-z0-9_]+", text.lower())
    hans = re.findall(r"[\u4e00-\u9fff]+", text)
    zh: List[str] = []
    for seg in hans:
        zh.extend(list(seg))
        zh.extend([seg[i:i+2] for i in range(len(seg) - 1)])
    punct = re.findall(r"[？?！!。.,，;；:：/\\\-_]", text)
    return words + zh + punct


# ====== 朴素贝叶斯意图分类（自学习）======
class NaiveBayesIntent:
    def __init__(self, labels: List[str]) -> None:
        self.labels = labels
        self.label_counts: Counter = Counter()
        self.token_counts: Dict[str, Counter] = {lb: Counter() for lb in labels}
        self.total_tokens: Dict[str, int] = {lb: 0 for lb in labels}
        self.vocab: set = set()
        self.trained: bool = False

    def fit(self, samples: List[Tuple[str, str]]) -> None:
        self.label_counts = Counter()
        self.token_counts = {lb: Counter() for lb in self.labels}
        self.total_tokens = {lb: 0 for lb in self.labels}
        self.vocab = set()
        for text, label in samples:
            if label not in self.labels:
                continue
            toks = tokenize(text)
            if not toks:
                continue
            self.label_counts[label] += 1
            c = Counter(toks)
            self.token_counts[label].update(c)
            self.total_tokens[label] += sum(c.values())
            self.vocab.update(c.keys())
        self.trained = sum(self.label_counts.values()) > 0

    def _log_prob(self, toks: List[str], label: str) -> float:
        alpha = 1.0
        V = max(1, len(self.vocab))
        total_docs = max(1, sum(self.label_counts.values()))
        prior = (self.label_counts[label] + alpha) / (total_docs + alpha * len(self.labels))
        logp = math.log(prior)
        denom = self.total_tokens[label] + alpha * V
        tc = self.token_counts[label]
        for t in toks:
            logp += math.log((tc.get(t, 0) + alpha) / denom)
        return logp

    def predict_proba(self, text: str) -> Dict[str, float]:
        toks = tokenize(text)
        if not toks or not self.trained:
            u = 1.0 / max(1, len(self.labels))
            return {lb: u for lb in self.labels}
        scores = {lb: self._log_prob(toks, lb) for lb in self.labels}
        m = max(scores.values())
        exps = {lb: math.exp(v - m) for lb, v in scores.items()}
        s = sum(exps.values()) or 1.0
        return {lb: exps[lb] / s for lb in self.labels}

    def predict(self, text: str) -> Tuple[str, float, List[Tuple[str, float]]]:
        proba = self.predict_proba(text)
        ranked = sorted(proba.items(), key=lambda x: x[1], reverse=True)
        return ranked[0][0], ranked[0][1], ranked

    def to_json(self) -> Dict[str, Any]:
        return {
            "labels": self.labels,
            "label_counts": dict(self.label_counts),
            "token_counts": {lb: dict(self.token_counts[lb]) for lb in self.labels},
            "total_tokens": dict(self.total_tokens),
            "vocab": list(self.vocab),
            "trained": self.trained,
        }

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> "NaiveBayesIntent":
        nb = NaiveBayesIntent(obj.get("labels", []))
        nb.label_counts = Counter(obj.get("label_counts", {}))
        nb.token_counts = {lb: Counter(obj.get("token_counts", {}).get(lb, {})) for lb in nb.labels}
        nb.total_tokens = obj.get("total_tokens", {lb: 0 for lb in nb.labels})
        nb.vocab = set(obj.get("vocab", []))
        nb.trained = bool(obj.get("trained", False))
        return nb


# ====== 工具选择自学习（epsilon-greedy）======
class EpsilonGreedyChooser:
    def __init__(self, path: Path, epsilon: float = EPSILON) -> None:
        self.path = path
        self.epsilon = epsilon
        self.stats: Dict[str, Dict[str, Dict[str, int]]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.stats = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.stats = {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.stats, ensure_ascii=False, indent=2), encoding="utf-8")

    def _rate(self, domain: str, option: str) -> float:
        s = self.stats.get(domain, {}).get(option, {"ok": 0, "fail": 0})
        ok, fail = s.get("ok", 0), s.get("fail", 0)
        return (ok + 1) / (ok + fail + 2)

    def choose(self, domain: str, candidates: List[str]) -> str:
        if not candidates:
            raise ValueError("no candidates")
        if random.random() < self.epsilon:
            return random.choice(candidates)
        return sorted(candidates, key=lambda c: self._rate(domain, c), reverse=True)[0]

    def update(self, domain: str, option: str, ok: bool) -> None:
        self.stats.setdefault(domain, {}).setdefault(option, {"ok": 0, "fail": 0})
        self.stats[domain][option]["ok" if ok else "fail"] += 1
        self._save()


# ====== 简易知识库（TF-IDF 检索 + 缓存）======
class SimpleKB:
    """
    纯标准库 TF-IDF：
    - kb_docs.jsonl 存文档
    - 缓存 df/idf & 每个文档的 tf，避免每次查询都重算全库
    """

    def __init__(self, docs_path: Path) -> None:
        self.docs_path = docs_path
        self.docs: List[Dict[str, Any]] = []
        self._doc_tfs: List[Counter] = []
        self._df: Counter = Counter()
        self._dirty: bool = True
        self._load()

    def _load(self) -> None:
        self.docs = []
        if not self.docs_path.exists():
            self._dirty = True
            return
        for line in self.docs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                self.docs.append(json.loads(line))
            except Exception:
                continue
        self._dirty = True

    def _rebuild_cache(self) -> None:
        self._doc_tfs = []
        self._df = Counter()
        for d in self.docs:
            toks = tokenize((d.get("title", "") or "") + "\n" + (d.get("text", "") or ""))
            tf = Counter(toks)
            self._doc_tfs.append(tf)
            for t in tf.keys():
                self._df[t] += 1
        self._dirty = False

    def add_doc(self, text: str, title: str = "", tags: Optional[List[str]] = None) -> None:
        rec = {
            "id": f"d{int(time.time() * 1000)}",
            "title": redact(title),
            "tags": tags or [],
            "text": redact(text),
            "ts": int(time.time()),
        }
        with self.docs_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.docs.append(rec)
        self._dirty = True

    def import_folder(self, folder: str, exts: Tuple[str, ...] = (".md", ".txt")) -> int:
        p = Path(folder)
        if not p.exists():
            return 0
        n = 0
        for fp in p.rglob("*"):
            if fp.is_file() and fp.suffix.lower() in exts:
                try:
                    txt = fp.read_text(encoding="utf-8", errors="ignore")
                    self.add_doc(txt, title=str(fp), tags=["import"])
                    n += 1
                except Exception:
                    pass
        return n

    def _idf(self, t: str, N: int) -> float:
        return math.log((N + 1) / (self._df.get(t, 0) + 1)) + 1.0

    @staticmethod
    def _cos(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        if len(a) > len(b):
            a, b = b, a
        dot = sum(av * b.get(t, 0.0) for t, av in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        qt = tokenize(query)
        if not qt or not self.docs:
            return []
        if self._dirty:
            self._rebuild_cache()
        N = max(1, len(self.docs))
        qtf = Counter(qt)
        qvec = {t: (qtf[t] * self._idf(t, N)) for t in qtf}
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for d, tf in zip(self.docs, self._doc_tfs):
            dvec = {t: (tf[t] * self._idf(t, N)) for t in tf}
            s = self._cos(qvec, dvec)
            if s > 0:
                scored.append((s, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: List[Dict[str, Any]] = []
        for s, d in scored[:k]:
            out.append({
                "score": round(s, 4),
                "title": d.get("title", ""),
                "snippet": (d.get("text", "") or "")[:300],
                "id": d.get("id", ""),
            })
        return out


# ====== 主核心：可嵌入 OpenClaw ======
class SelfLearningCore:
    def __init__(self) -> None:
        self.nb = NaiveBayesIntent(list(ALLOW_INTENTS))
        self.chooser = EpsilonGreedyChooser(TOOL_STATS, epsilon=EPSILON)
        self.kb = SimpleKB(KB_FILE)
        self._new_samples = 0
        self._load_model()
        self.session = self._load_json(SESSION_FILE, default={})
        self.profile = self._load_json(PROFILE_FILE, default={
            "language": "zh-CN",
            "output_style": "conclusion_steps_next",
        })

    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return default
        return default

    def _save_json(self, path: Path, obj: Any) -> None:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    def log(self, payload: Dict[str, Any]) -> None:
        safe = {k: (redact(v) if isinstance(v, str) else v) for k, v in payload.items()}
        safe["ts"] = int(time.time())
        with EVENTS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe, ensure_ascii=False) + "\n")

    def _load_model(self) -> None:
        if MODEL_FILE.exists():
            try:
                self.nb = NaiveBayesIntent.from_json(
                    json.loads(MODEL_FILE.read_text(encoding="utf-8"))
                )
            except Exception:
                pass

    def _save_model(self) -> None:
        MODEL_FILE.write_text(
            json.dumps(self.nb.to_json(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_training(self) -> List[Tuple[str, str]]:
        samples: List[Tuple[str, str]] = []
        if not TRAIN_FILE.exists():
            return samples
        for line in TRAIN_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                t, i = obj.get("text", ""), obj.get("intent", "")
                if i in ALLOW_INTENTS and isinstance(t, str):
                    samples.append((t, i))
            except Exception:
                continue
        return samples

    def train(self) -> None:
        samples = self._load_training()
        self.nb.fit(samples)
        self._save_model()
        self.log({"type": "train", "samples": len(samples), "trained": self.nb.trained})

    def feedback(self, text: str, correct_intent: str, note: str = "") -> None:
        if correct_intent not in ALLOW_INTENTS:
            raise ValueError(f"intent not allowed: {correct_intent}")
        rec = {
            "text": redact(text),
            "intent": correct_intent,
            "note": redact(note),
            "ts": int(time.time()),
        }
        with TRAIN_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._new_samples += 1
        self.log({"type": "feedback", "intent": correct_intent})
        if self._new_samples >= AUTO_TRAIN_EVERY:
            self.train()
            self._new_samples = 0

    def route(self, text: str) -> Dict[str, Any]:
        best, conf, ranked = self.nb.predict(text)
        top3 = ranked[:3]
        if (not self.nb.trained) or (conf < CLARIFY_THRESHOLD):
            return {"intent": "clarify", "confidence": conf, "topk": top3}
        return {"intent": best, "confidence": conf, "topk": top3}

    def clarify_msg(self, topk: List[Tuple[str, float]]) -> str:
        opts = " / ".join([f"{i+1}.{k}" for i, (k, _) in enumerate(topk)])
        return f'我没完全确定你的意思。你更像是要：{opts}？回复数字 1/2/3 或直接说"我的意思是 xxx"。'

    def extract_slots(self, text: str, intent: str) -> Dict[str, Any]:
        slots: Dict[str, Any] = {}
        urls = re.findall(r"https?://\S+", text)
        if urls:
            slots["urls"] = urls
        paths = re.findall(r"[A-Za-z]:\\[^ \n\r\t]+", text)
        if paths:
            slots["paths"] = paths
        time_words = re.findall(r"(今天|明天|后天|今晚|早上|上午|中午|下午|傍晚|晚上)", text)
        if time_words:
            slots["time_hints"] = time_words
        if re.search(r"(英文|英语|english)", text, re.I):
            slots["language"] = "en-US"
        else:
            slots["language"] = self.profile.get("language", "zh-CN")
        if intent == "asr_transcribe":
            if re.search(r"(离线|vosk)", text, re.I):
                slots["engine"] = "vosk"
            elif re.search(r"(google|谷歌)", text, re.I):
                slots["engine"] = "google"
            else:
                slots["engine"] = "auto"
        return slots

    def choose_asr_engine(self, prefer: str = "auto") -> str:
        if prefer in ("google", "vosk"):
            return prefer
        return self.chooser.choose("asr", ["google", "vosk"])

    def update_tool_result(self, domain: str, option: str, ok: bool) -> None:
        self.chooser.update(domain, option, ok)

    def kb_add(self, text: str, title: str = "", tags: Optional[List[str]] = None) -> None:
        self.kb.add_doc(text, title=title, tags=tags)

    def kb_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        return self.kb.search(query, k=k)

    def handle(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if not text:
            return {"reply": "说点什么吧～"}

        # /f 意图 [原话]：纠正学习
        if text.startswith("/f "):
            parts = text.split(" ", 2)
            intent = parts[1].strip() if len(parts) >= 2 else ""
            origin = parts[2].strip() if len(parts) == 3 else self.session.get("last_text", "")
            if not origin:
                return {"reply": "没有可纠正的上一句。用：/f 意图 你的原话"}
            self.feedback(origin, intent)
            return {"reply": f"已学习：{intent}（以后更准）"}

        # /kbadd 内容：写入知识库
        if text.startswith("/kbadd "):
            payload = text[len("/kbadd "):].strip()
            if payload:
                self.kb_add(payload, title="manual")
                return {"reply": "已加入知识库。"}
            return {"reply": "用法：/kbadd 你要保存的内容"}

        # /kb 查询：知识库检索
        if text.startswith("/kb "):
            q = text[len("/kb "):].strip()
            hits = self.kb_search(q, k=3)
            if not hits:
                return {"reply": "知识库里暂时没搜到。"}
            lines = [f"- {h['title']} (score={h['score']}): {h['snippet']}" for h in hits]
            return {"reply": "我在知识库里找到：\n" + "\n".join(lines), "hits": hits}

        r = self.route(text)
        self.session["last_text"] = text
        self._save_json(SESSION_FILE, self.session)

        if r["intent"] == "clarify":
            return {"reply": self.clarify_msg(r["topk"]), "route": r}

        intent = r["intent"]
        slots = self.extract_slots(text, intent)
        plan: List[str] = []
        tool: str = ""

        if intent == "asr_transcribe":
            eng = self.choose_asr_engine(slots.get("engine", "auto"))
            tool = f"asr:{eng}"
            plan = [f"选择 ASR 引擎：{eng}", "获取音频", "转写", "输出/发送结果"]
        elif intent == "note_write":
            tool = "note"
            plan = ["整理内容", "写入 notes/inbox.md", "返回保存位置"]
        elif intent == "tts_speak":
            tool = "tts"
            plan = ["生成语音", "播放/发送音频"]
        elif intent == "automation_task":
            tool = "task"
            plan = ["提取时间与动作", "创建/更新任务", "返回确认信息"]
        elif intent == "system_ops":
            tool = "system_ops_safe"
            plan = ["识别系统操作", "检查是否在白名单", "执行/或要求确认", "返回日志"]
        else:
            tool = "qa"
            plan = ["必要时检索知识库", "组织答案", "给出下一步建议"]

        reply = (
            f"✅结论：我理解你要做（置信度 {r['confidence']:.2f}）\n"
            f"🔧计划：\n- " + "\n- ".join(plan) + "\n"
            f"➡️下一步：把我接到你的工具执行器上（tool={tool}），我就能真正动手。"
        )

        self.session.update({"last_intent": intent, "last_slots": slots, "last_plan": plan})
        self._save_json(SESSION_FILE, self.session)
        self.log({"type": "route", "intent": intent, "conf": r["confidence"], "tool": tool})

        return {
            "reply": reply,
            "intent": intent,
            "slots": slots,
            "tool": tool,
            "plan": plan,
            "route": r,
        }


# ====== CLI：先本地跑通，再接 OpenClaw ======
def _cli() -> None:
    import sys

    core = SelfLearningCore()
    if len(sys.argv) <= 1:
        print('用法：python smartlearn.py chat | train | route "文本" | kbimport <folder>')
        return

    cmd = sys.argv[1]
    if cmd == "train":
        core.train()
        print("trained:", core.nb.trained)
    elif cmd == "route":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(core.route(text), ensure_ascii=False, indent=2))
        print(core.handle(text)["reply"])
    elif cmd == "kbimport":
        folder = sys.argv[2] if len(sys.argv) > 2 else ""
        n = core.kb.import_folder(folder)
        print("imported:", n)
    elif cmd == "chat":
        print("进入交互：输入文本路由；/f 意图 纠正；/kb 查询；/kbadd 加知识。/q 退出")
        while True:
            text = input("> ").strip()
            if text == "/q":
                break
            out = core.handle(text)
            print(out["reply"])
    else:
        print("未知命令：", cmd)


if __name__ == "__main__":
    _cli()
