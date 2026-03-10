#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Learning Agent Observer - 鑷姩瑙傚療绗竴鎵?6 涓?Agent 鐨勮繍琛屾儏鍐?
姣忓ぉ鑷姩鏇存柊瑙傚療琛紝浠?task_executions_v2.jsonl 鎻愬彇鏁版嵁銆?"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# 绗竴鎵?6 涓?Agent
FIRST_BATCH_AGENTS = [
    "Bug_Hunter",
    "Error_Analyzer",
    "GitHub_Code_Reader",
    "GitHub_Researcher",
    "Code_Reviewer",
    "Architecture_Analyst"
]

def load_agents_json():
    """鍔犺浇 agents.json"""
    agents_file = Path(__file__).parent / "agents.json"
    if not agents_file.exists():
        return []
    
    with open(agents_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("agents", [])

def load_task_executions():
    """鍔犺浇 task_executions_v2.jsonl"""
    exec_file = Path(__file__).parent / "task_executions_v2.jsonl"
    if not exec_file.exists():
        return []
    
    executions = []
    with open(exec_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                executions.append(json.loads(line))
    
    return executions

def analyze_agent_performance(agent_name, executions):
    """鍒嗘瀽鍗曚釜 Agent 鐨勬€ц兘"""
    agent_execs = [e for e in executions if e.get("agent_id") == agent_name]
    
    if not agent_execs:
        return {
            "dispatched": 0,
            "succeeded": 0,
            "failed": 0,
            "last_run": None,
            "avg_duration": None,
            "useful_output": 0,
            "keep_active": "寰呰瀵?
        }
    
    succeeded = len([e for e in agent_execs if e.get("status") == "completed"])
    failed = len([e for e in agent_execs if e.get("status") == "failed"])
    
    # 璁＄畻骞冲潎鑰楁椂
    durations = [e.get("duration", 0) for e in agent_execs if e.get("duration")]
    avg_duration = sum(durations) / len(durations) if durations else None
    
    # 鏈€杩戣繍琛屾椂闂?    last_run = max([e.get("completed_at", 0) for e in agent_execs])
    last_run_str = datetime.fromtimestamp(last_run).strftime("%Y-%m-%d %H:%M") if last_run else None
    
    # 鏈夋晥浜у嚭锛堢畝鍗曞垽鏂細鎴愬姛涓旀湁缁撴灉锛?    useful_output = len([e for e in agent_execs if e.get("status") == "completed" and e.get("result")])
    
    # 鍐崇瓥锛氭槸鍚︾户缁?active
    if len(agent_execs) >= 3 and useful_output >= 1:
        keep_active = "A绫?缁х画"
    elif len(agent_execs) >= 1:
        keep_active = "B绫?瑙傚療"
    elif len(agent_execs) == 0:
        keep_active = "D绫?鏃犺皟搴?
    else:
        keep_active = "C绫?闄嶇骇"
    
    return {
        "dispatched": len(agent_execs),
        "succeeded": succeeded,
        "failed": failed,
        "last_run": last_run_str,
        "avg_duration": f"{avg_duration:.1f}s" if avg_duration else None,
        "useful_output": useful_output,
        "keep_active": keep_active
    }

def generate_observation_report():
    """鐢熸垚瑙傚療鎶ュ憡"""
    agents = load_agents_json()
    executions = load_task_executions()
    
    # 鍙垎鏋愮涓€鎵?6 涓?Agent
    first_batch = [a for a in agents if a.get("name") in FIRST_BATCH_AGENTS]
    
    report = []
    report.append("# Learning Agent 瑙傚療琛╘n")
    report.append(f"**瑙傚療鏈燂細** 2026-03-07 ~ 2026-03-14锛?澶╋級\n")
    report.append(f"**鏇存柊鏃堕棿锛?* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    report.append("\n---\n\n")
    
    report.append("## 瑙傚療鎸囨爣\n\n")
    report.append("| Agent | 璋冨害娆℃暟 | 鎴愬姛 | 澶辫触 | 鏈€杩戣繍琛?| 骞冲潎鑰楁椂 | 鏈夋晥浜у嚭 | 缁х画Active |\n")
    report.append("|-------|---------|------|------|---------|---------|---------|-----------|\n")
    
    for agent in first_batch:
        name = agent.get("name")
        perf = analyze_agent_performance(name, executions)
        
        report.append(f"| {name} | {perf['dispatched']} | {perf['succeeded']} | {perf['failed']} | ")
        report.append(f"{perf['last_run'] or '-'} | {perf['avg_duration'] or '-'} | ")
        report.append(f"{perf['useful_output']} | {perf['keep_active']} |\n")
    
    report.append("\n---\n\n")
    
    # 姣忔棩璁板綍
    today = datetime.now().strftime("%Y-%m-%d")
    report.append(f"## 姣忔棩璁板綍\n\n")
    report.append(f"### {today}\n\n")
    
    total_dispatched = sum([analyze_agent_performance(a.get("name"), executions)["dispatched"] for a in first_batch])
    total_succeeded = sum([analyze_agent_performance(a.get("name"), executions)["succeeded"] for a in first_batch])
    total_failed = sum([analyze_agent_performance(a.get("name"), executions)["failed"] for a in first_batch])
    
    if total_dispatched == 0:
        report.append("**鐘舵€侊細** 鏃犺皟搴﹁褰昞n\n")
    else:
        report.append(f"**鐘舵€侊細** 宸茶皟搴?{total_dispatched} 娆★紙鎴愬姛 {total_succeeded}锛屽け璐?{total_failed}锛塡n\n")
    
    report.append("**瑙傚療锛?*\n")
    report.append("- agents.json 杩愯姝ｅ父\n")
    report.append("- Heartbeat 闆嗘垚姝ｅ父\n")
    report.append("- 涓夋€佸睍绀烘竻鏅癨n\n")
    
    report.append("**涓嬩竴姝ワ細**\n")
    if total_dispatched == 0:
        report.append("- 绛夊緟棣栨璋冨害\n")
        report.append("- 鐩戞帶 spawn_requests.jsonl\n\n")
    else:
        report.append("- 缁х画瑙傚療鎵ц鎯呭喌\n")
        report.append("- 鍒嗘瀽澶辫触鍘熷洜\n\n")
    
    report.append("---\n\n")
    
    # 鏍稿績楠岃瘉闂
    report.append("## 鏍稿績楠岃瘉闂锛?涓級\n\n")
    
    report.append("### 1. 鏈夋病鏈夎瀹為檯璋冨害鍒帮紵\n")
    for agent in first_batch:
        name = agent.get("name")
        perf = analyze_agent_performance(name, executions)
        status = "鉁? if perf["dispatched"] > 0 else "鈴?
        report.append(f"- [{status}] {name}锛坽perf['dispatched']} 娆★級\n")
    report.append("\n")
    
    report.append("### 2. 浠诲姟鏉ユ簮鏄粈涔堬紵\n")
    report.append("- [ ] coder-dispatcher 瑙﹀彂\n")
    report.append("- [ ] analyst-dispatcher 瑙﹀彂\n")
    report.append("- [ ] monitor-dispatcher 瑙﹀彂\n")
    report.append("- [ ] 鐢ㄦ埛鎵嬪姩瑙﹀彂\n")
    report.append("- [ ] Heartbeat 鑷姩瑙﹀彂\n\n")
    
    report.append("### 3. 鎵ц鏄惁鎴愬姛锛焅n")
    success_rate = (total_succeeded / total_dispatched * 100) if total_dispatched > 0 else 0
    status = "鉁? if success_rate >= 80 else "鈴?
    report.append(f"- [{status}] 鎴愬姛鐜?{success_rate:.1f}%锛堢洰鏍?>80%锛塡n")
    report.append("- [ ] 澶辫触妯″紡璇嗗埆\n")
    report.append("- [ ] 甯歌閿欒绫诲瀷\n\n")
    
    report.append("### 4. 鏈夋病鏈夊疄闄呮敹鐩婏紵\n")
    for agent in first_batch:
        name = agent.get("name")
        perf = analyze_agent_performance(name, executions)
        status = "鉁? if perf["useful_output"] > 0 else "鈴?
        report.append(f"- [{status}] {name}锛坽perf['useful_output']} 娆℃湁鏁堜骇鍑猴級\n")
    report.append("\n")
    
    report.append("### 5. 鏈夋病鏈夊櫔闊?Agent锛焅n")
    report.append("- [ ] 璐＄尞浣庛€佹秷鑰楅珮\n")
    report.append("- [ ] 鎵ц鎴愬姛浣嗘棤浠峰€糪n")
    report.append("- [ ] 閲嶅鍔冲姩\n\n")
    
    report.append("### 6. Heartbeat 灞曠ず鏄惁娓呮櫚锛焅n")
    report.append("- [鉁匽 涓夋€佸睍绀烘竻鏅癨n")
    report.append("- [ ] 缁熻鏁版嵁鍑嗙‘\n")
    report.append("- [ ] 鏃犲櫔闊冲共鎵癨n\n")
    
    report.append("---\n\n")
    
    # 鍒嗗眰鍐崇瓥鏍囧噯
    report.append("## 鍒嗗眰鍐崇瓥鏍囧噯锛?026-03-14锛塡n\n")
    
    a_class = [a for a in first_batch if analyze_agent_performance(a.get("name"), executions)["keep_active"] == "A绫?缁х画"]
    b_class = [a for a in first_batch if analyze_agent_performance(a.get("name"), executions)["keep_active"] == "B绫?瑙傚療"]
    c_class = [a for a in first_batch if analyze_agent_performance(a.get("name"), executions)["keep_active"] == "C绫?闄嶇骇"]
    d_class = [a for a in first_batch if analyze_agent_performance(a.get("name"), executions)["keep_active"] == "D绫?鏃犺皟搴?]
    
    report.append(f"### A 绫伙細缁х画 active锛坽len(a_class)}涓級\n")
    if a_class:
        for a in a_class:
            report.append(f"- {a.get('name')}\n")
    else:
        report.append("- 鏆傛棤\n")
    report.append("\n")
    
    report.append(f"### B 绫伙細缁х画瑙傚療锛坽len(b_class)}涓級\n")
    if b_class:
        for a in b_class:
            report.append(f"- {a.get('name')}\n")
    else:
        report.append("- 鏆傛棤\n")
    report.append("\n")
    
    report.append(f"### C 绫伙細闄嶅洖 shadow锛坽len(c_class)}涓級\n")
    if c_class:
        for a in c_class:
            report.append(f"- {a.get('name')}\n")
    else:
        report.append("- 鏆傛棤\n")
    report.append("\n")
    
    report.append(f"### D 绫伙細disabled锛坽len(d_class)}涓級\n")
    if d_class:
        for a in d_class:
            report.append(f"- {a.get('name')}\n")
    else:
        report.append("- 鏆傛棤\n")
    report.append("\n")
    
    report.append("---\n\n")
    report.append(f"**鍒涘缓鏃堕棿锛?* 2026-03-07 19:45\n")
    report.append(f"**鏈€鍚庢洿鏂帮細** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    return "".join(report)

def main():
    """涓诲嚱鏁?""
    print("[OBSERVER] Learning Agent Observer Started")
    
    report = generate_observation_report()
    
    # 淇濆瓨鎶ュ憡
    report_file = Path(__file__).parent / "reports" / "learning_agent_observation.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"[OK] Report saved: {report_file}")
    print(f"[OK] Observer completed")

if __name__ == "__main__":
    main()

