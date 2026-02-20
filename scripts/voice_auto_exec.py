# scripts/voice_auto_exec.py - 语音命令自动执行器
"""
在消息到达 AI 之前拦截语音转写，自动执行可识别的命令。
解决"AI知道该做但没做"的行为问题——从架构层面保证执行。

用法：
  python voice_auto_exec.py "打開柯柯音樂"
  python voice_auto_exec.py "關閉QQ音樂"

返回 JSON:
  {"executed": true, "action": "open", "canonical": "QQ音乐", "result": "SUCCESS", "reply": "已打开QQ音乐"}
  {"executed": false, "reason": "no_match", "raw": "今天天气怎么样"}
"""
import json, sys, subprocess, time, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aios'))

from core.app_alias import resolve, action_summary, RISK_LEVELS


def is_process_running(name):
    try:
        r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"],
                           capture_output=True, timeout=5, encoding='gbk', errors='replace')
        return name.lower() in r.stdout.lower()
    except:
        return False


def exec_open(r):
    exe = r.get("exe_path")
    proc = r.get("process_name")
    if not exe:
        return False, f"未知应用路径: {r['canonical']}"
    if proc and is_process_running(proc):
        return True, "NOOP_ALREADY_RUNNING"
    try:
        subprocess.Popen([exe], shell=False)
        time.sleep(1)
        return True, "SUCCESS"
    except Exception as e:
        return False, str(e)


def exec_close(r):
    proc = r.get("process_name")
    if not proc:
        return False, f"未知进程名: {r['canonical']}"
    if not is_process_running(proc):
        return True, "NOOP_NOT_RUNNING"
    try:
        subprocess.run(["taskkill", "/IM", proc, "/F"],
                       capture_output=True, timeout=5)
        return True, "SUCCESS"
    except Exception as e:
        return False, str(e)


def run(raw_text):
    r = resolve(raw_text)

    # 无法识别的命令
    if not r["action"] or not r["matched"]:
        return {"executed": False, "reason": "no_match", "raw": raw_text}

    # 高风险需确认
    if r["risk"] == "high":
        return {"executed": False, "reason": "needs_confirmation",
                "action": r["action"], "canonical": r["canonical"]}

    # 执行
    if r["action"] == "open":
        ok, detail = exec_open(r)
    elif r["action"] == "close":
        ok, detail = exec_close(r)
    else:
        return {"executed": False, "reason": "unsupported_action", "action": r["action"]}

    reply = action_summary(raw_text) if ok else f"执行失败: {detail}"

    return {
        "executed": ok,
        "action": r["action"],
        "canonical": r["canonical"],
        "result": detail,
        "reply": reply,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: voice_auto_exec.py <text>"}, ensure_ascii=False))
        sys.exit(1)

    text = " ".join(sys.argv[1:])
    result = run(text)
    print(json.dumps(result, ensure_ascii=False))
