# aram/modules/matcher.py - 英雄模糊搜索（可解释 + 反馈学习）
"""
输入中文/拼音/简称 → 匹配英雄 → 返回匹配理由 → 用户纠正 → 自动学习
"""
import json, re, time
from pathlib import Path
from difflib import SequenceMatcher

ARAM_DIR = Path(r"C:\Users\A\Desktop\ARAM-Helper")
DATA_FILE = ARAM_DIR / "aram_data.json"
FEEDBACK_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FEEDBACK_FILE = FEEDBACK_DIR / "matcher_feedback.jsonl"
LEARNED_ALIASES_FILE = FEEDBACK_DIR / "learned_aliases.json"

# 常用别名词典（国服玩家习惯叫法）
ALIASES = {
    # 简称/昵称 → champion_id
    "卡特": "55",    # 不祥之刃 卡特琳娜
    "卡莎": "145",   # 虚空之女 卡莎
    "凯隐": "141",   # 影流之镰 凯隐
    "盲僧": "64",    # 盲僧 李青
    "李青": "64",
    "剑圣": "11",    # 无极剑圣 易
    "易": "11",
    "大嘴": "96",    # 深渊巨口 克格莫
    "石头人": "54",  # 熔岩巨兽 墨菲特
    "石头": "54",
    "锤石": "412",   # 魂锁典狱长 锤石
    "机器人": "53",  # 蒸汽机器人 布里茨
    "女警": "51",    # 皮城女警 凯特琳
    "凯特琳": "51",
    "皮城": "51",
    "男枪": "104",   # 法外狂徒 格雷福斯
    "格雷福斯": "104",
    "男刀": "91",    # 刀锋之影 泰隆
    "泰隆": "91",
    "女刀": "55",    # 不祥之刃 卡特琳娜
    "妖姬": "7",     # 诡术妖姬 乐芙兰
    "乐芙兰": "7",
    "小鱼人": "105", # 潮汐海灵 菲兹
    "菲兹": "105",
    "小法": "45",    # 邪恶小法师 维迦
    "维迦": "45",
    "大虫子": "31",  # 虚空恐惧 科加斯
    "科加斯": "31",
    "狗头": "75",    # 沙漠死神 内瑟斯
    "内瑟斯": "75",
    "猴子": "62",    # 齐天大圣 孙悟空
    "悟空": "62",
    "孙悟空": "62",
    "蛮王": "23",    # 蛮族之王 泰达米尔
    "泰达米尔": "23",
    "剑姬": "114",   # 无双剑姬 菲奥娜
    "菲奥娜": "114",
    "皇子": "59",    # 德玛西亚皇子 嘉文四世
    "嘉文": "59",
    "嘉文四世": "59",
    "赵信": "5",     # 德邦总管 赵信
    "德邦": "5",
    "螳螂": "121",   # 虚空掠夺者 卡兹克
    "卡兹克": "121",
    "蜘蛛": "60",    # 蜘蛛女皇 伊莉丝
    "伊莉丝": "60",
    "狼人": "19",    # 祖安怒兽 沃里克
    "沃里克": "19",
    "老鼠": "29",    # 瘟疫之源 图奇
    "图奇": "29",
    "提莫": "17",    # 迅捷斥候 提莫
    "亚索": "157",   # 疾风剑豪 亚索
    "永恩": "777",   # 封魔剑魂 永恩
    "劫": "238",     # 影流之主 劫
    "阿狸": "103",   # 九尾妖狐 阿狸
    "安妮": "1",     # 黑暗之女 安妮
    "艾希": "22",    # 寒冰射手 艾希
    "寒冰": "22",
    "薇恩": "67",    # 暗夜猎手 薇恩
    "VN": "67",
    "vn": "67",
    "EZ": "81",      # 探险家 伊泽瑞尔
    "ez": "81",
    "伊泽瑞尔": "81",
    "瑞兹": "13",    # 符文法师 瑞兹
    "诺手": "122",   # 诺克萨斯之手 德莱厄斯
    "德莱厄斯": "122",
    "锐雯": "92",    # 放逐之刃 锐雯
    "瑞文": "92",
    "盖伦": "86",    # 德玛西亚之力 盖伦
    "德玛": "86",
    "拉克丝": "99",  # 光辉女郎 拉克丝
    "光辉": "99",
    "女枪": "21",    # 赏金猎人 厄运小姐
    "厄运小姐": "21",
    "MF": "21",
    "mf": "21",
    "琴女": "37",    # 琴瑟仙女 娑娜
    "娑娜": "37",
    "牛头": "12",    # 牛头酋长 阿利斯塔
    "阿木木": "32",  # 殇之木乃伊 阿木木
    "木木": "32",
    "火男": "63",    # 复仇焰魂 布兰德
    "布兰德": "63",
    "塞拉斯": "517", # 解脱者 塞拉斯
    "猪妹": "113",   # 北地之怒 瑟庄妮
    "瑟庄妮": "113",
    "船长": "41",    # 海洋之灾 普朗克
    "普朗克": "41",
    "龙王": "136",   # 铸星龙王 奥瑞利安·索尔
    "奥瑞利安索尔": "136",
    "索尔": "136",
    "亚恒": "904",   # 不落魔峰 亚恒
    "扎恩": "904",
}

_cache = {}

def _load_data():
    if "data" in _cache:
        return _cache["data"]
    if not DATA_FILE.exists():
        return {}
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    _cache["data"] = data
    return data

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _load_learned_aliases() -> dict:
    """加载用户纠正后学习到的别名"""
    if not LEARNED_ALIASES_FILE.exists():
        return {}
    try:
        return json.loads(LEARNED_ALIASES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_learned_aliases(aliases: dict):
    FEEDBACK_DIR.mkdir(exist_ok=True)
    LEARNED_ALIASES_FILE.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")

def feedback(query: str, correct_champion_id: str, was_wrong: bool = True):
    """
    用户纠正反馈。
    query: 用户输入
    correct_champion_id: 正确的英雄 ID
    was_wrong: 匹配结果是否错误
    """
    FEEDBACK_DIR.mkdir(exist_ok=True)
    data = _load_data()
    correct_info = data.get(correct_champion_id, {})
    
    # 记录反馈
    rec = {
        "ts": int(time.time()),
        "query": query,
        "correct_id": correct_champion_id,
        "correct_title": correct_info.get("title", ""),
        "was_wrong": was_wrong,
    }
    with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    
    # 自动学习：把纠正写入 learned_aliases
    if was_wrong:
        learned = _load_learned_aliases()
        learned[query] = correct_champion_id
        _save_learned_aliases(learned)
    
    return rec

def match(query: str, top_n: int = 3) -> list:
    """
    模糊匹配英雄。
    返回: [{champion_id, name, title, score, reason}]
    """
    data = _load_data()
    if not data:
        return []
    
    query = query.strip()
    results = []
    
    # 0. 用户学习的别名（最高优先级）
    learned = _load_learned_aliases()
    if query in learned:
        cid = learned[query]
        if cid in data:
            info = data[cid]
            results.append({
                "champion_id": cid,
                "name": info.get("name", ""),
                "title": info.get("title", ""),
                "score": 1.0,
                "reason": f"用户纠正学习: {query} → {info.get('title', '')}",
                "match_type": "learned",
            })
            return results
    
    # 1. 别名词典精确命中
    if query in ALIASES:
        cid = ALIASES[query]
        if cid in data:
            info = data[cid]
            results.append({
                "champion_id": cid,
                "name": info.get("name", ""),
                "title": info.get("title", ""),
                "score": 1.0,
                "reason": f"别名词典精确命中: {query} → {info.get('title', '')}",
                "match_type": "alias_exact",
            })
            return results  # 精确命中直接返回
    
    # 2. 别名词典模糊命中
    for alias, cid in ALIASES.items():
        sim = _similarity(query, alias)
        if sim >= 0.6 and cid in data:
            info = data[cid]
            results.append({
                "champion_id": cid,
                "name": info.get("name", ""),
                "title": info.get("title", ""),
                "score": round(sim, 2),
                "reason": f"别名模糊匹配: {query} ≈ {alias} (相似度 {sim:.2f})",
                "match_type": "alias_fuzzy",
            })
    
    # 3. 数据库 name/title 匹配
    for cid, info in data.items():
        name = info.get("name", "")
        title = info.get("title", "")
        
        # 精确包含
        if query in name or query in title:
            score = 0.95 if query == title else 0.90
            results.append({
                "champion_id": cid,
                "name": name,
                "title": title,
                "score": score,
                "reason": f"名称包含匹配: '{query}' in '{title}' / '{name}'",
                "match_type": "contains",
            })
            continue
        
        # 模糊相似度
        sim_name = _similarity(query, name)
        sim_title = _similarity(query, title)
        best_sim = max(sim_name, sim_title)
        best_field = "title" if sim_title >= sim_name else "name"
        
        if best_sim >= 0.5:
            results.append({
                "champion_id": cid,
                "name": name,
                "title": title,
                "score": round(best_sim, 2),
                "reason": f"模糊匹配 {best_field}: 相似度 {best_sim:.2f}",
                "match_type": "fuzzy",
            })
    
    # 去重（同一个 champion_id 取最高分）
    seen = {}
    for r in results:
        cid = r["champion_id"]
        if cid not in seen or r["score"] > seen[cid]["score"]:
            seen[cid] = r
    
    # 排序返回 top_n
    ranked = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:top_n]


def explain(query: str) -> str:
    """人类可读的匹配解释"""
    results = match(query)
    if not results:
        return f"未找到与 '{query}' 匹配的英雄"
    
    lines = [f"搜索: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']} ({r['name']})")
        lines.append(f"   匹配度: {r['score']:.2f} | 类型: {r['match_type']}")
        lines.append(f"   理由: {r['reason']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    
    # feedback mode: python matcher.py feedback "卡特" "55"
    if len(sys.argv) >= 4 and sys.argv[1] == "feedback":
        q = sys.argv[2]
        correct_id = sys.argv[3]
        rec = feedback(q, correct_id)
        print(json.dumps(rec, ensure_ascii=False))
        sys.exit(0)
    
    q = sys.argv[1] if len(sys.argv) > 1 else "凯隐"
    fmt = sys.argv[2] if len(sys.argv) > 2 else "json"
    
    results = match(q)
    if fmt == "json":
        for r in results:
            out = {
                "input": q,
                "matched": r["title"],
                "champion_id": r["champion_id"],
                "score": r["score"],
                "reasons": [],
            }
            if r["match_type"] == "learned":
                out["reasons"].append("user_learned")
            elif r["match_type"] == "alias_exact":
                out["reasons"].append("alias_hit")
            elif r["match_type"] == "alias_fuzzy":
                out["reasons"].append("alias_fuzzy")
            if r["match_type"] == "contains":
                out["reasons"].append("name_contains")
            if r["score"] >= 0.8:
                out["reasons"].append(f"fuzzy_score>={r['score']:.1f}")
            print(json.dumps(out, ensure_ascii=False))
    else:
        print(explain(q))
