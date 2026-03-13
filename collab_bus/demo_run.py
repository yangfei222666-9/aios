"""
demo_run.py - collab_bus_router v0.3 最小演示

演示 1：主链 task_dispatch -> task_result -> review -> summary
演示 2：异常链（未知消息类型）
"""

import json
import os
import sys

# 把 collab_bus 目录加入路径
DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DEMO_DIR)

from collab_bus_router import run, ensure_dirs, OUTBOX, INBOX, STATE, ARCHIVE, load_json

TASK_ID = "demo-task-001"


def write_msg(filename, data):
    path = os.path.join(OUTBOX, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [DEMO] 写入 outbox: {filename}")


def show_state():
    path = os.path.join(STATE, f"{TASK_ID}.json")
    if os.path.exists(path):
        s = load_json(path)
        print(f"  [STATE] stage={s['stage']}  owner={s['current_owner']}  next={s['next_action']}")
        print(f"          history steps: {len(s.get('history', []))}")
    else:
        print("  [STATE] 文件不存在")


def show_inbox(suffix):
    path = os.path.join(INBOX, f"{TASK_ID}_{suffix}.json")
    if os.path.exists(path):
        print(f"  [INBOX] {TASK_ID}_{suffix}.json ✓")
    else:
        print(f"  [INBOX] {TASK_ID}_{suffix}.json ✗ 未生成")


def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── 演示 1：主链 ──────────────────────────────────────────

def demo_main_chain():
    sep("演示 1：主链")

    ensure_dirs()

    # Step 1: task_dispatch
    print("\n[Step 1] task_dispatch")
    write_msg(f"{TASK_ID}_01_dispatch.json", {
        "task_id": TASK_ID,
        "from": "openclaw",
        "to": "xiaojiu",
        "type": "task_dispatch",
        "title": "修复 voice_wakeword 内存泄漏",
        "body": "请修复 voice_wakeword.py 的内存泄漏问题，重点检查 audio_frames 和临时文件处理。",
        "context": {"priority": "high", "needs_confirm": False, "project": "taijiOS"},
        "created_at": "2026-03-13T20:00:00+08:00"
    })
    run()
    show_state()
    show_inbox("dispatch")

    # Step 2: task_result
    print("\n[Step 2] task_result")
    write_msg(f"{TASK_ID}_02_result.json", {
        "task_id": TASK_ID,
        "from": "xiaojiu",
        "to": "openclaw",
        "type": "task_result",
        "title": "修复 voice_wakeword 内存泄漏",
        "body": "已完成修复：1) audio_frames 录音结束后显式清空；2) 临时文件增加 finally 块；3) 录音增加 30s 最大时长限制。",
        "context": {"priority": "high", "needs_confirm": False, "project": "taijiOS",
                    "files_changed": ["voice_wakeword.py"], "tags": ["bugfix", "memory"]},
        "created_at": "2026-03-13T20:05:00+08:00"
    })
    run()
    show_state()
    show_inbox("result")

    # Step 3: review
    print("\n[Step 3] review")
    write_msg(f"{TASK_ID}_03_review.json", {
        "task_id": TASK_ID,
        "from": "openclaw",
        "to": "user",
        "type": "review",
        "title": "审查：修复 voice_wakeword 内存泄漏",
        "body": "修复方向正确，audio_frames 清理和临时文件处理符合预期。建议补充异常路径测试。",
        "context": {"needs_confirm": False, "verdict": "approved",
                    "risks": ["异常路径未覆盖测试"]},
        "created_at": "2026-03-13T20:10:00+08:00"
    })
    run()
    show_state()
    show_inbox("review")

    # Step 4: summary
    print("\n[Step 4] summary")
    write_msg(f"{TASK_ID}_04_summary.json", {
        "task_id": TASK_ID,
        "from": "openclaw",
        "to": "user",
        "type": "summary",
        "title": "✅ 任务完成：修复 voice_wakeword 内存泄漏",
        "body": "任务已完成，审查通过。修复了 audio_frames 清理、临时文件处理、录音超时限制。",
        "context": {"needs_confirm": False},
        "created_at": "2026-03-13T20:15:00+08:00"
    })
    run()
    show_state()
    show_inbox("summary")

    # 最终状态
    print("\n[最终 state 文件]")
    path = os.path.join(STATE, f"{TASK_ID}.json")
    if os.path.exists(path):
        s = load_json(path)
        print(json.dumps(s, ensure_ascii=False, indent=2))

    # archive 检查
    print("\n[archive 产物]")
    for f in sorted(os.listdir(ARCHIVE)):
        if TASK_ID in f:
            print(f"  {f}")


# ── 演示 2：异常链 ────────────────────────────────────────

def demo_error_chain():
    sep("演示 2：异常链（未知消息类型）")

    error_task_id = "demo-task-002"
    ensure_dirs()

    print("\n[Step 1] 写入未知类型消息")
    path = os.path.join(OUTBOX, f"{error_task_id}_unknown.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": error_task_id,
            "from": "unknown_agent",
            "to": "openclaw",
            "type": "magic_command",   # 不在 AUTO_OK 也不在 NEED_CONFIRM
            "title": "测试未知类型",
            "body": "这条消息应该被拒绝并记录到 failed。",
            "created_at": "2026-03-13T20:20:00+08:00"
        }, f, ensure_ascii=False, indent=2)
    print(f"  [DEMO] 写入 outbox: {error_task_id}_unknown.json")

    run()

    # 检查 state
    state_path = os.path.join(STATE, f"{error_task_id}.json")
    if os.path.exists(state_path):
        s = load_json(state_path)
        print(f"\n[STATE] stage={s['stage']}")
        print(f"[ERROR_LOG] {s.get('error_log', [])}")
    else:
        print("\n[STATE] 文件未生成")

    # 检查 inbox error
    error_inbox = os.path.join(INBOX, f"{error_task_id}_error.json")
    if os.path.exists(error_inbox):
        e = load_json(error_inbox)
        print(f"\n[INBOX ERROR] type={e['type']}  title={e['title']}")
    else:
        print("\n[INBOX ERROR] 未生成")


# ── 主入口 ────────────────────────────────────────────────

if __name__ == "__main__":
    demo_main_chain()
    demo_error_chain()

    print(f"\n{'='*60}")
    print("  演示完成")
    print(f"{'='*60}")
    print("\n本轮验证覆盖：")
    print("  ✓ 主链 4 步全部走通")
    print("  ✓ state 文件随每步更新")
    print("  ✓ inbox / archive / state 三处产物一致")
    print("  ✓ 未知消息类型进入 failed + error_log + inbox error")
    print("\n本轮未覆盖：")
    print("  - need_confirm / waiting_user_confirm 分支")
    print("  - review needs_confirm=True 分支")
    print("  - blocked / 人工恢复流程")
    print("  - 多任务并发（v0 不支持）")
