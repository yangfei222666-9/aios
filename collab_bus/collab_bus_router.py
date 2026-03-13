"""
collab_bus_router.py - 文件总线路由器 v0.3

职责：
- 读取 outbox/ 里的标准消息文件
- 按 type 字段做路由
- 把处理结果写到 inbox/ 或 archive/
- 同步更新 state/

约束（v0）：
- 单次运行，不是 daemon
- 不做并发
- 不做自动重试
- 不接 Telegram API
- 失败先记录，不自动重复执行

变更记录：
- v0.1: 初版
- v0.2: 修复路径双层 bug；统一状态迁移走 transition_state()；
        修正 task_result actor；补目录自创建；
        summary 不再推进状态；统一 failed 走 mark_failed()；
        统一返回值枚举
- v0.3: need_confirm 保存逻辑移到 if/else 之后统一执行；
        task_result 补注释说明事件压缩语义；
        summary 返回值改为 "summary"；
        review last_summary 统一在 if/else 后设置；
        unhandled 改为显式 raise，防止白名单和分支脱钩
"""

import json
import os
import shutil
from datetime import datetime, timezone

# router 本身就在 collab_bus/ 目录里，BASE_DIR 即是 COLLAB_BUS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COLLAB_BUS = BASE_DIR
OUTBOX  = os.path.join(COLLAB_BUS, "outbox")
INBOX   = os.path.join(COLLAB_BUS, "inbox")
STATE   = os.path.join(COLLAB_BUS, "state")
ARCHIVE = os.path.join(COLLAB_BUS, "archive")

# 安全闸门
AUTO_OK      = {"task_dispatch", "task_result", "review", "summary"}
NEED_CONFIRM = {"shell_execute", "file_delete", "prod_modify", "external_send"}

# 状态迁移表
# failed 是全局异常态，通过 mark_failed() 从任意状态进入，不在此表里限制
# waiting_user_confirm -> planned 表示用户要求修改，重新派发
STATE_TRANSITIONS = {
    "planned":              ["dispatched"],
    "dispatched":           ["executing", "waiting_user_confirm"],
    "executing":            ["reviewing", "waiting_user_confirm"],
    "reviewing":            ["done", "waiting_user_confirm"],
    "waiting_user_confirm": ["done", "planned"],
    "done":                 [],
    "failed":               ["blocked"],
    "blocked":              ["planned"],
}


# ── 工具函数 ──────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


def ensure_dirs():
    """首跑自创建必要目录"""
    for d in [OUTBOX, INBOX, STATE, ARCHIVE]:
        os.makedirs(d, exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state(task_id):
    path = os.path.join(STATE, f"{task_id}.json")
    if os.path.exists(path):
        return load_json(path)
    return None


def save_state(task_id, state_data):
    save_json(os.path.join(STATE, f"{task_id}.json"), state_data)


# ── 状态机 ────────────────────────────────────────────────

def transition_state(state_data, new_stage, actor, note=""):
    """执行状态迁移，校验合法性"""
    current = state_data.get("stage", "planned")
    allowed = STATE_TRANSITIONS.get(current, [])
    if new_stage not in allowed:
        raise ValueError(f"非法状态迁移: {current} -> {new_stage}（允许: {allowed}）")
    state_data["stage"] = new_stage
    state_data["last_message_from"] = actor
    state_data["updated_at"] = now_iso()
    state_data.setdefault("history", []).append({
        "at": now_iso(),
        "from": actor,
        "action": f"{current} -> {new_stage}",
        "note": note,
    })
    return state_data


def mark_failed(state_data, actor, error_msg):
    """全局异常态：从任意状态进入 failed，不走普通迁移校验"""
    current = state_data.get("stage", "unknown")
    state_data["stage"] = "failed"
    state_data["last_message_from"] = actor
    state_data["updated_at"] = now_iso()
    state_data.setdefault("error_log", []).append({
        "at": now_iso(),
        "error": error_msg,
    })
    state_data.setdefault("history", []).append({
        "at": now_iso(),
        "from": actor,
        "action": f"{current} -> failed",
        "note": error_msg,
    })
    return state_data


def init_state(msg):
    """从消息初始化状态，初始阶段为 planned"""
    return {
        "task_id": msg.get("task_id"),
        "title": msg.get("title", ""),
        "status": "active",
        "stage": "planned",          # 初始阶段 planned，task_dispatch 触发 planned -> dispatched
        "created_by": msg.get("from", "unknown"),
        "current_owner": msg.get("to", "unknown"),
        "reviewer": "openclaw",
        "needs_confirm": msg.get("context", {}).get("needs_confirm", False),
        "last_message_from": msg.get("from", "unknown"),
        "last_summary": "",
        "next_action": "",
        "retry_count": 0,
        "max_retries": 3,
        "error_log": [],
        "history": [],
        "updated_at": now_iso(),
        "created_at": now_iso(),
    }


# ── 路由逻辑 ──────────────────────────────────────────────

def route_message(msg):
    """路由单条消息，返回处理结果（枚举值）"""
    task_id  = msg.get("task_id")
    msg_type = msg.get("type")
    to       = msg.get("to")
    sender   = msg.get("from", "unknown")

    print(f"  [ROUTE] task={task_id} type={msg_type} to={to}")

    # ── 安全闸门 ──
    if msg_type in NEED_CONFIRM:
        print(f"  [GATE] NEED_CONFIRM: {msg_type}，暂停等待用户确认")
        state = load_state(task_id) or init_state(msg)
        current = state.get("stage", "planned")
        allowed = STATE_TRANSITIONS.get(current, [])
        # 尝试正常迁移或标记失败
        if "waiting_user_confirm" in allowed:
            state = transition_state(state, "waiting_user_confirm", "router",
                                     f"安全闸门触发: {msg_type}")
        else:
            # 当前状态不允许正常迁移（如已 done/blocked），直接标记失败
            state = mark_failed(state, "router",
                                 f"安全闸门触发但无法迁移: {msg_type}，当前状态 {current}")
        # 无论走哪个分支，统一更新状态和写消息
        state["needs_confirm"] = True
        state["last_summary"] = f"消息类型 {msg_type} 需要用户确认"
        state["next_action"] = "user_confirm"
        save_state(task_id, state)
        save_json(os.path.join(INBOX, f"{task_id}_need_confirm.json"), {
            "task_id": task_id,
            "from": "router",
            "to": "openclaw",
            "type": "need_confirm",
            "title": msg.get("title", ""),
            "body": f"消息类型 {msg_type} 触发安全闸门，需要珊瑚海确认后才能继续。",
            "original_message": msg,
            "created_at": now_iso(),
        })
        return "need_confirm"

    # ── 未知类型：失败可观察 ──
    if msg_type not in AUTO_OK:
        print(f"  [GATE] 未知消息类型 {msg_type}，默认拒绝")
        state = load_state(task_id) or init_state(msg)
        state = mark_failed(state, "router", f"未知消息类型: {msg_type}")
        state["last_summary"] = f"未知消息类型 {msg_type}，已拒绝"
        save_state(task_id, state)
        save_json(os.path.join(INBOX, f"{task_id}_error.json"), {
            "task_id": task_id,
            "from": "router",
            "to": "openclaw",
            "type": "error",
            "title": f"未知消息类型: {msg_type}",
            "body": f"收到未知消息类型 {msg_type}，任务已标记为 failed。",
            "created_at": now_iso(),
        })
        return "denied"

    # ── 加载或初始化状态 ──
    state = load_state(task_id) or init_state(msg)

    # ── task_dispatch：planned -> dispatched ──
    if msg_type == "task_dispatch":
        state = transition_state(state, "dispatched", sender, "任务已派发")
        state["current_owner"] = to
        state["next_action"] = f"{to}_execute"
        state["last_summary"] = f"任务已派发给 {to}"
        save_state(task_id, state)
        save_json(os.path.join(INBOX, f"{task_id}_dispatch.json"), msg)
        print(f"  [OK] 任务已写入 inbox")
        return "dispatched"

    # ── task_result：dispatched -> executing -> reviewing ──
    elif msg_type == "task_result":
        # v0 中没有单独的 task_start 消息。
        # 执行者完成后发 task_result，router 在此补记 dispatched -> executing，
        # 再推进 executing -> reviewing。这是一种事件压缩，不是真有独立的"开始执行"消息。
        if state.get("stage") == "dispatched":
            state = transition_state(state, "executing", sender, "执行者开始执行（v0 补记）")
        # 再推进 executing -> reviewing
        state = transition_state(state, "reviewing", sender, "执行者已完成，等待审查")
        state["current_owner"] = "openclaw"
        state["next_action"] = "openclaw_review"
        state["last_summary"] = msg.get("body", "")[:200]
        save_state(task_id, state)
        save_json(os.path.join(INBOX, f"{task_id}_result.json"), msg)
        print(f"  [OK] 执行结果已写入 inbox")
        return "reviewing"

    # ── review：reviewing -> done 或 waiting_user_confirm ──
    elif msg_type == "review":
        needs_confirm = msg.get("context", {}).get("needs_confirm", False)
        if needs_confirm:
            state = transition_state(state, "waiting_user_confirm", sender,
                                     "审查完成，需要用户确认")
            state["next_action"] = "user_confirm"
        else:
            state = transition_state(state, "done", sender, "审查通过，任务完成")
            state["next_action"] = "none"
            state["status"] = "completed"
        state["last_summary"] = msg.get("body", "")[:200]
        save_state(task_id, state)
        save_json(os.path.join(INBOX, f"{task_id}_review.json"), msg)
        return state["stage"]

    # ── summary：只做汇报，不推进状态 ──
    elif msg_type == "summary":
        state["last_summary"] = msg.get("body", "")[:200]
        state["updated_at"] = now_iso()
        save_state(task_id, state)
        inbox_path = os.path.join(INBOX, f"{task_id}_summary.json")
        save_json(inbox_path, msg)
        shutil.copy(inbox_path, os.path.join(ARCHIVE, f"{task_id}_summary.json"))
        print(f"  [OK] 汇报已归档")
        return "summary"  # 不返回 done，避免统计语义和状态语义混淆

    # 理论上不应到达：AUTO_OK 白名单和分支必须保持同步
    raise ValueError(f"未处理的合法消息类型: {msg_type}，请检查 AUTO_OK 和分支是否脱钩")


# ── 主循环 ────────────────────────────────────────────────

def run():
    print("=" * 60)
    print("collab_bus_router v0.3 — 文件总线路由器")
    print(f"运行时间: {now_iso()}")
    print("=" * 60)

    ensure_dirs()

    files = [f for f in os.listdir(OUTBOX) if f.endswith(".json")]
    if not files:
        print("[INFO] outbox/ 为空，无消息待处理")
        return

    print(f"[INFO] 发现 {len(files)} 条待处理消息")
    results = {k: 0 for k in ("dispatched", "reviewing", "done",
                               "need_confirm", "denied", "failed", "summary")}

    for fname in sorted(files):
        fpath = os.path.join(OUTBOX, fname)
        print(f"\n处理: {fname}")
        try:
            msg    = load_json(fpath)
            result = route_message(msg)
            results[result] = results.get(result, 0) + 1
            shutil.move(fpath, os.path.join(ARCHIVE, fname))
            print(f"  [ARCHIVE] 已归档")
        except Exception as e:
            print(f"  [ERROR] 处理失败: {e}")
            results["failed"] += 1
            try:
                msg     = load_json(fpath)
                task_id = msg.get("task_id", fname)
                state   = load_state(task_id) or init_state(msg)
                state   = mark_failed(state, "router", str(e))
                save_state(task_id, state)
            except Exception:
                pass

    print("\n" + "=" * 60)
    print("路由完成")
    for k, v in results.items():
        if v > 0:
            print(f"  {k}: {v}")
    print("=" * 60)


if __name__ == "__main__":
    run()
